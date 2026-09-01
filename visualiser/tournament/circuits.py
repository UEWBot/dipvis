# Diplomacy Tournament Visualiser
# Copyright (C) 2024-2026 Chris Brand
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Circuit models for the Diplomacy Tournament Visualiser.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from operator import itemgetter

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext as _

from tournament.models import (find_scoring_system, get_scoring_systems,
                               InvalidScoringSystem, NameSlugField, Tournament,
                               TournamentPlayer)
from tournament.players import Player
from tournament.wdd import WDD_BASE_RESULTS_URL, validate_wdd_circuit_id
from tournament.wdr import WDR_BASE_URL, validate_wdr_circuit_id


class CircuitScoringSystem(ABC):
    """
    A scoring system for a Circuit.

    Provides a method to calculate a score for each player of the circuit.
    """
    MAX_NAME_LENGTH=40
    name = ''

    @abstractmethod
    def scores(self, circuit):
        """
        Returns the circuit scores.

        Returns a dict, indexed by player key, of circuit scores.
        """
        raise NotImplementedError

    def __str__(self):
        ret = self.name
        return ret


def _percentiles(tournamentplayers):
    """
    Determines the percentiles for a set of TournamentPlayers

    tournamentplayers must all be from the same Tournament.
    Returns a dict, keyed by TournamentPlayer of float percentiles.
    """
    tps = list(tournamentplayers)
    tps.sort(key=lambda x: x.score)
    count = len(tps)
    if count == 0:
        return {}
    retval = {}
    index = 0
    while index < count:
        score = tps[index].score
        group_end = index
        while (group_end < count) and (tps[group_end].score == score):
            group_end += 1

        # Percentile is based on strictly lower scores only, so tied players share it.
        percentile = index / count
        for tp in tps[index:group_end]:
            retval[tp.player] = percentile
        index = group_end
    return retval


class CScoringSumPercentiles(CircuitScoringSystem):
    """
    Percentile circuit scoring system

    Circuit score is the sum of the best N tournament scores,
    where the score for a tournament is calculated as:
    Number of ranked tournament players who finished with a LOWER rank than the player
    DIVIDED BY
    Total number of ranked players at the tournament
    """
    scored_rounds = 0

    def __init__(self, name, scored_rounds):
        self.name = name
        self.scored_rounds = scored_rounds

    def scores(self, circuit):
        """
        Returns the circuit scores.

        Returns a dict, indexed by player key, of circuit scores.
        """
        scores, _ = self.scores_and_results(circuit)
        return scores

    def scores_and_results(self, circuit):
        """Return circuit scores and contribution details keyed by TournamentPlayer id."""
        # Fetch CircuitPlayers once with select_related('player') so that
        # the players-set build and all subsequent tp.player lookups inside
        # _percentiles are query-free.
        circuit_players = circuit.circuitplayer_set.select_related('player').all()

        # Build the set of Player objects for all CircuitPlayers.
        players = {cp.player for cp in circuit_players}

        tournaments = circuit.tournaments.all()

        # Query 1: PKs of every TournamentPlayer explicitly linked to a
        # CircuitPlayer in this circuit.  Materialising as a frozenset means
        # we pay for this lookup exactly once.  The previous implementation
        # rebuilt an equivalent subquery inside the tournament loop, causing it
        # to be re-evaluated once per INTERSECT.
        linked_tp_ids = frozenset(
            CircuitTournamentResult.objects
            .filter(circuit_player__in=circuit_players)
            .values_list('tournament_player_id', flat=True)
        )

        # Query 2: fetch all qualifying TournamentPlayers across every circuit
        # tournament in a single round-trip, then group in Python.
        # select_related('player') avoids an N+1 when _percentiles accesses
        # tp.player for each row.  The previous INTERSECT approach prevented
        # chaining select_related, causing a separate Player fetch per TP.
        # player__in=players is a safety guard against data inconsistency where
        # a CircuitPlayer might be linked to a TP belonging to a different player.
        all_tps = (
            TournamentPlayer.objects
            .filter(tournament__in=tournaments, player__in=players, id__in=linked_tp_ids)
            .select_related('player')
            .order_by()
        )

        # Group the fetched TPs by tournament_id so _percentiles can be called
        # per tournament without issuing any further queries.
        tps_by_tournament = defaultdict(list)
        for tp in all_tps:
            tps_by_tournament[tp.tournament_id].append(tp)

        # Calculate the percentile each player achieved in each tournament.
        percentiles = {}
        tp_by_tournament_and_player = {}
        for t in tournaments:
            # tps_by_tournament.get returns [] for tournaments with no linked
            # TPs (e.g. a newly added tournament with no players yet).
            tournament_players = tps_by_tournament.get(t.id, [])
            percentiles[t] = _percentiles(tournament_players)
            for tp in tournament_players:
                tp_by_tournament_and_player[(t.id, tp.player_id)] = tp

        # Sum the best scored_rounds percentiles for each player.
        retval = {}
        results = {}
        for p in players:
            # Collect this player's percentile from every tournament where they
            # have a linked TournamentPlayer, then sort best-first.
            p_scores = []
            for t in tournaments:
                if p in percentiles[t]:
                    tp = tp_by_tournament_and_player[(t.id, p.id)]
                    p_scores.append((percentiles[t][p], t.start_date, t.id, tp.id))
            p_scores.sort(key=lambda value: (-value[0], value[1], value[2]))

            # Accumulate the top scored_rounds values; any extras are ignored.
            retval[p] = 0.0
            for n, (score, _start_date, _tournament_id, tournament_player_id) in enumerate(p_scores):
                score_dropped = n >= self.scored_rounds
                results[tournament_player_id] = (score, score_dropped)
                if not score_dropped:
                    retval[p] += score
        return retval, results


# All the supported circuit scoring systems
C_SCORING_SYSTEMS = [
    CScoringSumPercentiles(_('Sum best 3 tournament percentiles'), 3),
]


def find_circuit_scoring_system(name):
    """
    Searches for a scoring system with the given name

    Returns either the CircuitScoringSystem object or None.
    """
    try:
        return find_scoring_system(name, C_SCORING_SYSTEMS)
    except InvalidScoringSystem:
        return None


def validate_circuit_scoring_system(value):
    """
    Validator for Circuit.scoring_system
    """
    system = find_circuit_scoring_system(value)
    if not system:
        raise ValidationError(_("%{name} is not a valid tournament scoring system"),
                              params={'name': value})


class Circuit(models.Model):
    """
    A circuit of Diplomacy Tournaments
    """
    MAX_NAME_LENGTH = 60

    name = models.CharField(max_length=MAX_NAME_LENGTH)
    scoring_system = models.CharField(validators=[validate_circuit_scoring_system],
                                      max_length=CircuitScoringSystem.MAX_NAME_LENGTH,
                                      choices=get_scoring_systems(C_SCORING_SYSTEMS),
                                      help_text=_('How to combine tournament scores into a circuit score'))
    start_date = models.DateField()
    end_date = models.DateField()
    #managers = models.ManyToManyField(User,
    #                                  help_text=_(u'Which users can modify the circuit'))
    tournaments = models.ManyToManyField(Tournament, blank=True)
    wdd_circuit_id = models.PositiveIntegerField(validators=[validate_wdd_circuit_id],
                                                 verbose_name=_("This circuit's id in the World Diplomacy Database"),
                                                 blank=True,
                                                 null=True,
                                                 help_text=_("Add this after the circuit has been added to the WDD"))
    wdr_circuit_id = models.PositiveIntegerField(validators=[validate_wdr_circuit_id],
                                                 verbose_name=_("This circuit's id in the World Diplomacy Reference"),
                                                 blank=True,
                                                 null=True,
                                                 help_text=_("Add this after the circuit has been added to the WDR"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'start_date'],
                                    name='circuit_unique_name_date'),
            models.CheckConstraint(check=Q(end_date__gte=F('start_date')),
                                   name='%(class)s_starts_before_end'),
        ]

    def __str__(self):
        return '%s %d' % (self.name, self.start_date.year)

    def save(self, *args, **kwargs):
        """
        Save the object to the database

        If the scoring system may have changed, recalculate scores
        """
        super().save(*args, **kwargs)

        if ('update_fields' not in kwargs) or ('scoring_system' in kwargs['update_fields']):
            try:
                validate_circuit_scoring_system(self.scoring_system)
            except ValidationError:
                pass
            self.update_scores()

    def get_absolute_url(self):
        """Returns the canonical URL for the object"""
        return reverse('circuit_detail', args=[str(self.id)])

    def scoring_system_obj(self):
        """
        Return the CircuitScoringSystem object for the Circuit

        Can raise InvalidScoringSystem.
        """
        system = find_circuit_scoring_system(self.scoring_system)
        if not system:
            raise InvalidScoringSystem(self.scoring_system)
        return system

    def ranks_and_scores(self):
        """
        Returns the scores for the Circuit

        Returns a dict, keyed by player, of 2-tuples containing integer rankings
          (1 for first place, etc) and float circuit scores.
        """
        scores = {}
        for cp in self.circuitplayer_set.select_related('player').all():
            scores[cp.player] = cp.score
        result = {}
        last_score = None
        for i, (k, v) in enumerate(sorted([(k,v) for k, v in scores.items()],
                                          key=itemgetter(1),
                                          reverse=True),
                                   start=1):
            if v != last_score:
                place, last_score = i, v
            result[k] = (place, v)
        return result

    def update_scores(self):
        """
        Recalculate and store CircuitPlayer scores and tournament contributions.
        """
        system = self.scoring_system_obj()
        new_scores, result_details = system.scores_and_results(self)
        # Fetch CircuitPlayers separately for the update loop; select_related
        # avoids N+1 on cp.player in the scores.get() call below.
        cps = self.circuitplayer_set.select_related('player').all()
        to_update = []
        for cp in cps:
            new_score = new_scores.get(cp.player, 0.0)
            if cp.score != new_score:
                cp.score = new_score
                to_update.append(cp)
        if to_update:
            CircuitPlayer.objects.bulk_update(to_update, ['score'])

        results = CircuitTournamentResult.objects.filter(
            circuit_player__circuit=self
        ).select_related('tournament_player')
        results_to_update = []
        for result in results:
            score, score_dropped = result_details[result.tournament_player_id]
            if result.score != score or result.score_dropped != score_dropped:
                result.score = score
                result.score_dropped = score_dropped
                results_to_update.append(result)
        if results_to_update:
            CircuitTournamentResult.objects.bulk_update(results_to_update,
                                                        ['score', 'score_dropped'])

    def add_or_update_circuit_players(self):
        """
        Check whether CircuitPlayers exist for all associated Tournaments

        For any missing Tournaments, add them.
        Also update all CircuitPlayer scores.
        """
        ranked_tps = TournamentPlayer.objects.filter(
            tournament__circuit=self,
            unranked=False
        ).select_related('player').distinct()

        existing_cp_by_player = {
            cp.player_id: cp.id
            for cp in self.circuitplayer_set.only('id', 'player_id')
        }

        missing_player_ids = {
            tp.player_id for tp in ranked_tps
        } - set(existing_cp_by_player.keys())
        if missing_player_ids:
            CircuitPlayer.objects.bulk_create([
                CircuitPlayer(player_id=player_id, circuit=self)
                for player_id in missing_player_ids
            ])
            existing_cp_by_player = {
                cp.player_id: cp.id
                for cp in self.circuitplayer_set.only('id', 'player_id')
            }

        through = CircuitPlayer.tournamentplayers.through
        through.objects.bulk_create([
            through(circuit_player_id=existing_cp_by_player[tp.player_id],
                    tournament_player_id=tp.id)
            for tp in ranked_tps
        ], ignore_conflicts=True)

        try:
            validate_circuit_scoring_system(self.scoring_system)
        except ValidationError:
            pass
        else:
            self.update_scores()

    def remove_orphan_circuit_players(self):
        """Drop TournamentPlayer links and CircuitPlayers no longer in this Circuit."""
        through = CircuitPlayer.tournamentplayers.through
        through.objects.filter(
            circuit_player__circuit=self
        ).exclude(
            tournament_player__tournament__circuit=self
        ).delete()

        self.circuitplayer_set.filter(tournamentplayers__isnull=True).delete()

        # Removing a CircuitPlayer may change other players scores
        try:
            validate_circuit_scoring_system(self.scoring_system)
        except ValidationError:
            pass
        else:
            self.update_scores()

    def wdd_url(self):
        """
        URL for this circuit in the World Diplomacy Database, if known
        """
        if self.wdd_circuit_id:
            return WDD_BASE_RESULTS_URL + f'circuit_class.php?id_circuit={self.wdd_circuit_id}'
        return ''

    def wdr_url(self):
        """
        URL for this circuit in the World Diplomacy Reference, if known
        """
        if self.wdr_circuit_id:
            return WDR_BASE_URL + f'tournaments/{self.wdr_circuit_id}'
        return ''


class CircuitPlayer(models.Model):
    """
    A person who played in a Circuit.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    tournamentplayers = models.ManyToManyField(TournamentPlayer,
                                               through='CircuitTournamentResult',
                                               blank=True)

    class Meta:
        # Each player can only be in each circuit once
        constraints = [
            models.UniqueConstraint(fields=['player', 'circuit'],
                                    name='unique_player_circuit'),
            # Ideally we'd check the tournamentplayers here
        ]

    def __str__(self):
        return _('%(player)s in %(circuit)s') % {'player': self.player,
                                                 'circuit': self.circuit}

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('circuit_player_detail', args=[str(self.circuit.id),
                                                      str(self.id)])


class CircuitTournamentResult(models.Model):
    """A TournamentPlayer's contribution to one CircuitPlayer's score."""
    circuit_player = models.ForeignKey(CircuitPlayer,
                                       related_name='tournament_results',
                                       on_delete=models.CASCADE)
    tournament_player = models.ForeignKey(TournamentPlayer,
                                          related_name='+',
                                          on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    score_dropped = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['circuit_player', 'tournament_player'],
                                    name='unique_circuit_tournament_result'),
        ]


class CircuitSeries(models.Model):
    """
    A series of Circuits, usually one per year.
    """
    MAX_NAME_LENGTH = 60
    MAX_DESC_LENGTH = 2000

    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    description = models.CharField(max_length=MAX_DESC_LENGTH, null=True)
    circuits = models.ManyToManyField(Circuit, blank=True)
    slug = NameSlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Circuit Series'

    def __str__(self):
        return '%s' % (self.name)

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('circuit_series_detail', args=[self.slug])


@receiver(m2m_changed, sender=Circuit.tournaments.through)
def _sync_circuit_players_on_tournament_m2m_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Keep CircuitPlayer rows in sync when tournaments are linked to a Circuit."""
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    if reverse:
        # Django can send a menaingless post_add with an empty pk_set
        if not pk_set:
            # This will also be exercised for tournament.circuit_set.clear(),
            # leaving orphan CircuitPlayer rows in the database
            return
        circuits = model.objects.filter(pk__in=pk_set)
        for circuit in circuits:
            if action == 'post_add':
                circuit.add_or_update_circuit_players()
            else:
                circuit.remove_orphan_circuit_players()
        return

    if action == 'post_add':
        instance.add_or_update_circuit_players()
    else:
        instance.remove_orphan_circuit_players()


@receiver(pre_save, sender=Tournament)
def _remember_tournament_editable_before_save(sender, instance, **kwargs):
    """Capture pre-save editable state so post-save can detect True->False transition."""
    if instance.pk is None:
        instance._editable_before_save = None
        return
    try:
        old = Tournament.objects.only('editable').get(pk=instance.pk)
    except Tournament.DoesNotExist:
        instance._editable_before_save = None
    else:
        instance._editable_before_save = old.editable


@receiver(post_save, sender=Tournament)
def _sync_circuit_scores_on_tournament_completion(sender, instance, created, **kwargs):
    """Sync circuits when a tournament is marked complete (editable toggled to False)."""
    if created:
        return
    if instance.editable:
        return
    if getattr(instance, '_editable_before_save', None) is not True:
        return

    for circuit in Circuit.objects.filter(tournaments=instance).only('id', 'scoring_system').distinct():
        circuit.add_or_update_circuit_players()
