# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016 Chris Brand
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
Django models file for the Diplomacy Tournament Visualiser.
"""

from abc import ABC, abstractmethod
import inspect
from operator import itemgetter
import os
import random
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Max
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _

from tournament.background import WDD_BASE_URL
from tournament.diplomacy import GameSet, GreatPower, SupplyCentre
from tournament.diplomacy import FIRST_YEAR, WINNING_SCS, TOTAL_SCS
from tournament.diplomacy import validate_year_including_start, validate_year
from tournament.diplomacy import validate_ranking, validate_preference_string
from tournament.email import send_prefs_email
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.players import Player, add_player_bg, position_str
from tournament.players import MASK_ALL_BG, MASK_ROUND_ENDPOINTS
from tournament.players import validate_wdd_tournament_id

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, _('spring')),
    (FALL, _('fall')),
)

# Mask values to choose which news strings to include
MASK_BOARD_TOP = 1 << 0
MASK_GAINERS = 1 << 1
MASK_LOSERS = 1 << 2
MASK_DRAW_VOTES = 1 << 3
MASK_ELIMINATIONS = 1 << 4
MASK_SC_CHANGES = 1 << 5
MASK_SC_CHANGE_COUNTS = 1 << 6
MASK_SC_OWNER_COUNTS = 1 << 7
MASK_ALL_NEWS = (1 << 8) - 1


class InvalidScoringSystem(Exception):
    """The specified scoring systm name is not recognised"""
    pass


class InvalidYear(Exception):
    """The year provided is not a valid game year"""
    pass


class SCOwnershipsNotFound(Exception):
    """
    The required SupplyCentreOwnership objects were not found in the database.
    """
    pass


class InvalidPreferenceList(Exception):
    """The string does not represent a valid preference list."""
    pass


class PowerAlreadyAssigned(Exception):
    """The GamePlayer already has a power assigned to them."""
    pass


class RoundScoringSystem(ABC):
    """
    A scoring system for a Round.
    Provides a method to calculate a score for each player of one round.
    """
    name = u''

    @abstractmethod
    def scores(self, game_players, non_players):
        """
        game_players is a QuerySet of GamePlayers.
        non_players is a QuerySet of RoundPlayers who were present but agreed
            not to play.
        Returns a dict, indexed by player key, of scores.
        """
        pass


class RScoringBest(RoundScoringSystem):
    """
    Take the best of any game scores for that round.
    """
    def __init__(self, non_player_score=0.0):
        self.non_player_score = non_player_score
        self.name = _(u'Best game counts')
        if non_player_score > 0.0:
            self.name = _('Best game counts. Sitters get %(points)d') % {'points': non_player_score}

    def scores(self, game_players, non_players):
        """
        If any player played multiple games, take the best game score.
        Otherwise, just take their game score.
        game_players is a QuerySet of GamePlayers.
        non_players is a QuerySet of RoundPlayers who were present but agreed
            not to play.
        Return a dict, indexed by player key, of scores.
        """
        retval = {}
        # First retrieve all the scores of all the games that are involved
        # This will give us the "if the game ended now" score for in-progress games
        game_scores = {}
        for g in Game.objects.filter(gameplayer__in=game_players).distinct():
            game_scores[g] = g.scores()
        # for each player who played any of the specified games
        for p in Player.objects.filter(gameplayer__in=game_players).distinct():
            # Find just their games
            # filter out games where they haven't been assigned a power
            player_games = game_players.filter(player=p).filter(power__isnull=False)
            # Find the highest score
            if player_games.exists():
                retval[p] = max(game_scores[g.game][g.power] for g in player_games)
            else:
                retval[p] = 0.0
        # Give the appropriate points to anyone who agreed to sit out
        for p in non_players:
            retval[p.player] = self.non_player_score
        return retval


# All the round scoring systems we support
R_SCORING_SYSTEMS = [
    RScoringBest(),
    RScoringBest(4005.0),
]


class TournamentScoringSystem(ABC):
    """
    A scoring system for a Tournament.
    Provides a method to calculate a score for each player of tournament.
    """
    name = u''

    @abstractmethod
    def scores_detail(self, round_players):
        """
        This is the same as scores(), excpet that it also returns the Round
        scores.
        Returns a 2-tuple:
        - a dict, indexed by player key, of tournament scores
        - a list, indexed by round, of dicts, indexed by player key,
          of round scores
        """
        pass


class TScoringSum(TournamentScoringSystem):
    """
    Just add up the best N round scores.
    """
    scored_rounds = 0

    def __init__(self, name, scored_rounds):
        self.name = name
        self.scored_rounds = scored_rounds

    def scores_detail(self, round_players):
        """
        If a player played more than N rounds, sum the best N round scores.
        Otherwise, sum all their round scores.
        Return a 2-tuple:
        - a dict, indexed by player key, of tournament scores
        - a dict, indexed by round, of dicts, indexed by player key,
          of round scores
        """
        # Retrieve all the scores for all the rounds involved.
        # This will give us "if the round ended now" scores for in-progress round(s)
        round_scores = {}
        for r in Round.objects.filter(roundplayer__in=round_players).distinct():
            round_scores[r] = r.scores()
        t_scores = {}
        # for each player who played any of the specified rounds
        for p in Player.objects.filter(roundplayer__in=round_players).distinct():
            # Find just their rounds
            player_rounds = round_players.filter(player=p)
            # Extract the scores into a sorted list, highest first
            player_scores = []
            for r in player_rounds:
                player_scores.append(round_scores[r.the_round][r.player])
            player_scores.sort(reverse=True)
            # Add up the first N
            t_scores[p] = sum(player_scores[:self.scored_rounds])
        return (t_scores, round_scores)


# All the tournament scoring systems we support
T_SCORING_SYSTEMS = [
    TScoringSum(_('Sum best 2 rounds'), 2),
    TScoringSum(_('Sum best 3 rounds'), 3),
    TScoringSum(_('Sum best 4 rounds'), 4),
]


def find_scoring_system(name, the_list):
    """
    Searches through the_list for a scoring system with the specified name.
    Returns either the ScoringSystem object or None.
    """
    for s in the_list:
        # There shouldn't be any abstract systems in here, but just in case...
        if (s.name == name) and not inspect.isabstract(s):
            return s
    return None


def find_game_scoring_system(name):
    """
    Searches for a scoring system with the given name.
    Returns either the GameScoringSystem object or None.
    """
    return find_scoring_system(name, G_SCORING_SYSTEMS)


def find_round_scoring_system(name):
    """
    Searches for a scoring system with the given name.
    Returns either the RoundScoringSystem object or None.
    """
    return find_scoring_system(name, R_SCORING_SYSTEMS)


def find_tournament_scoring_system(name):
    """
    Searches for a scoring system with the given name.
    Returns either the TournamentScoringSystem object or None.
    """
    return find_scoring_system(name, T_SCORING_SYSTEMS)


def get_scoring_systems(systems):
    """
    Returns a list of two-tuples, suitable for use in a
    Django CharField.choices parameter.
    """
    return sorted([(s.name, s.name) for s in systems if not inspect.isabstract(s)])


def validate_sc_count(value):
    """
    Checks for a valid SC count
    """
    if value < 0 or value > TOTAL_SCS:
        raise ValidationError(_(u'%(value)d is not a valid SC count'),
                              params={'value': value})


def validate_game_name(value):
    """
    Game names cannot contain spaces because they are used in URLs.
    """
    if u' ' in value:
        raise ValidationError(_(u'Game names cannot contain spaces'))


def validate_vote_count(value):
    """
    Checks for a valid vote count
    """
    if value < 0 or value > 7:
        raise ValidationError(_('%(value)d is not a valid vote count'),
                              params={'value': value})


def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # We expect instance to be a GameImage
    game = instance.game
    tournament = game.the_round.tournament
    directory = os.path.join(tournament.name, str(tournament.start_date), game.name)
    return os.path.join('games', directory, filename)


class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
    # Draw secrecy levels
    SECRET = 'S'
    COUNTS = 'C'
    DRAW_SECRECY = (
        (SECRET, _('Pass/Fail')),
        (COUNTS, _('Numbers for and against')),
    )

    # Power assignment methods
    AUTO = 'A'
    MANUAL = 'M'
    PREFERENCES = 'P'
    POWER_ASSIGN_METHODS = (
        (AUTO, _('Minimising playing the same power')),
        (MANUAL, _('Manually by TD or at the board')),
        (PREFERENCES, _('Using player preferences and ranking')),
    )

    # Best Country Criterion
    SCORE = 'S'
    DOTS = 'D'
    BEST_COUNTRY_CRITERION = (
        (SCORE, _('Highest score')),
        (DOTS, _('Highest centre count')),
    )

    # Flag value to use for players who are excluded from the rankings
    UNRANKED = 999999

    name = models.CharField(max_length=60)
    start_date = models.DateField()
    end_date = models.DateField()
    # How do we combine round scores to get an overall player tournament score ?
    # This is the name of a TournamentScoringSystem object
    tournament_scoring_system = models.CharField(max_length=40,
                                                 choices=get_scoring_systems(T_SCORING_SYSTEMS),
                                                 help_text=_(u'How to combine round scores into a tournament score'))
    # How do we combine game scores to get an overall player score for a round ?
    # This is the name of a RoundScoringSystem object
    round_scoring_system = models.CharField(max_length=40,
                                            choices=get_scoring_systems(R_SCORING_SYSTEMS),
                                            help_text=_(u'How to combine game scores into a round score'))
    draw_secrecy = models.CharField(max_length=1,
                                    verbose_name=_(u'What players are told about failed draw votes'),
                                    choices=DRAW_SECRECY,
                                    default=SECRET)
    is_published = models.BooleanField(default=False,
                                       help_text=_(u'Whether the tournament is visible to all site visitors'))
    managers = models.ManyToManyField(User,
                                      help_text=_(u'Which users can modify the tournament,<br/> and see it while it is unpublished.<br/>'))
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_("This tournament's id in the WDD"),
                                                    blank=True,
                                                    null=True,
                                                    help_text=_('Add this after the tournament is complete and results have been uploaded to the WDD'))
    seed_games = models.BooleanField(default=False,
                                     help_text=_('Check to let the software seed players to games'))
    power_assignment = models.CharField(max_length=1,
                                        verbose_name=_('How powers are assigned'),
                                        choices=POWER_ASSIGN_METHODS,
                                        default=MANUAL)
    editable = models.BooleanField(default=True,
                                   help_text=_('Check to disallow any further changes to the tournament'))
    best_country_criterion = models.CharField(max_length=1,
                                              verbose_name=_(u'How Best Country awards are determined'),
                                              choices=BEST_COUNTRY_CRITERION,
                                              default=SCORE)

    class Meta:
        ordering = ['-start_date']

    def powers_assigned_from_prefs(self):
        """
        Returns True is power_assignment is PREFERENCES.
        Intended for use in template code.
        """
        return self.power_assignment == self.PREFERENCES

    def _scores_detail_calculated(self):
        """
        Calculate the scores.
        Return a 2-tuple:
        - Dict, keyed by player, of float tournament scores.
        - Dict, keyed by round, of dicts, keyed by player,
          of float round scores
        """
        # Find the scoring system to combine round scores into a tournament score
        system = find_tournament_scoring_system(self.tournament_scoring_system)
        if not system:
            raise InvalidScoringSystem(self.tournament_scoring_system)
        t_scores, r_scores = system.scores_detail(RoundPlayer.objects.filter(the_round__tournament=self).distinct())
        # Now add in anyone who has yet to attend a round
        for tp in self.tournamentplayer_set.all():
            if tp.player not in t_scores:
                t_scores[tp.player] = 0.0
                # TODO Do we need to tweak r_scores here, too?
        return t_scores, r_scores

    def calculated_scores(self):
        """
        Calculates the scores for everyone registered for the tournament.
        Return a dict, keyed by player, of floats.
        """
        return self._scores_detail_calculated()[0]

    def scores_detail(self):
        """
        Returns the scores for everyone registered for the tournament.
        If the tournament is over, this will be the stored scores.
        If the tournament is ongoing, it will calculate the "if all games
            ended now" scores.
        Return a 2-tuple:
        - Dict, keyed by player, of float tournament scores.
        - Dict, keyed by round, of dicts, keyed by player,
          of float round scores
        """
        # If the tournament is over, report the stored scores
        if self.is_finished():
            t_scores = {}
            for p in self.tournamentplayer_set.all():
                t_scores[p.player] = p.score
            r_scores = {}
            for r in self.round_set.all():
                r_scores[r] = r.scores()
            return t_scores, r_scores
        return self._scores_detail_calculated()

    def positions_and_scores(self):
        """
        Returns the positions and scores of everyone registered.
        Return a 2-tuple:
        - Dict, keyed by player, of 2-tuples containing integer rankings
          (1 for first place, etc) and float tournament scores.
          Players who are flagged as unranked in the tournament get the special
          place UNRANKED.
        - Dict, keyed by round, of dicts, keyed by player, of float round scores
        """
        result = {}
        t_scores, r_scores = self.scores_detail()
        # First, deal with any unranked players
        for tp in self.tournamentplayer_set.filter(unranked=True):
            # Take it out of scores and add it to result
            result[tp.player] = (Tournament.UNRANKED, t_scores.pop(tp.player))
        last_score = None
        for i, (k, v) in enumerate(sorted([(k, v) for k, v in t_scores.items()],
                                          key=itemgetter(1),
                                          reverse=True),
                                   start=1):
            if v != last_score:
                place, last_score = i, v
            result[k] = (place, v)
        return result, r_scores

    def store_scores(self):
        """
        Recalculate the scores for the Tournament,
        and store them in the TournamentPlayers.
        """
        scores = self.calculated_scores()
        for p in self.tournamentplayer_set.all():
            try:
                p.score = scores[p.player]
            except KeyError:
                # Player was added to the tournament but didn't play
                p.score = 0.0
            p.save()

    def round_numbered(self, number):
        """
        Return the Round (if any) of the tournament with the specified number.
        """
        for r in self.round_set.all():
            if r.number() == int(number):
                return r
        # This allows this function to be used like QuerySet.get()
        raise Round.DoesNotExist

    def _sort_best_country_list(self, gp_list):
        """
        Take the list of (GamePlayer, score, dots, unranked) 4-tuples
        for one country, and sort it into best country ordering
        (highest to lowest).
        """
        # First sort criterion is always whether they're ranked or not
        # Second a third are score and centre count, with the order they're
        # used depending on how the Tournament is set up.
        # For ranking, we want regular order (so False is before True),
        # for the others, we want reverse order (highest first)
        if self.best_country_criterion == self.SCORE:
            gp_list.sort(key=itemgetter(1, 2), reverse=True)
        else:
            gp_list.sort(key=itemgetter(2, 1), reverse=True)
        gp_list.sort(key=itemgetter(3))

    def best_countries(self, whole_list=False):
        """
        Returns a dict, indexed by GreatPower,
          of lists of the GamePlayers doing best with each GreatPower.
        If whole_list is True, returns every player of each power, in order.
        If whole_list is False, returns just the winners (still a list, though).
        """
        tuples = {}
        # We're going to need to "if all games ended now" score for every GamePlayer
        all_games = Game.objects.filter(the_round__tournament=self)
        # If no Games exist, return a dict of empty lists
        if not all_games:
            for power in GreatPower.objects.all():
                tuples[power] = []
            return tuples
        all_scores = {}
        for g in all_games:
            all_scores[g] = g.scores()
        # Populate tuples. Dict, keyed by GreatPower,
        # of lists of (GamePlayer, score, dots, unranked) 4-tuples
        for r in self.round_set.all().prefetch_related('game_set'):
            for g in r.game_set.all().prefetch_related('gameplayer_set'):
                for gp in g.gameplayer_set.all():
                    score = all_scores[gp.game][gp.power]
                    tuple_ = (gp, score, gp.final_sc_count(), gp.tournamentplayer().unranked)
                    tuples.setdefault(gp.power, []).append(tuple_)
        for power in tuples:
            self._sort_best_country_list(tuples[power])
        retval = {}
        # If the caller wants the whole list, that's easy
        if whole_list:
            for power in tuples:
                retval[power] = [gp for gp, _, _, _ in tuples[power]]
            return retval
        # Filter out all except the best for each country
        for power in tuples:
            best_gp, best_score, best_dots, best_unranked = tuples[power].pop(0)
            list_ = [best_gp]
            for gp, score, dots, unranked in tuples[power]:
                # It's only a tie if all three criteria match
                if (score == best_score) and (dots == best_dots) and (unranked == best_unranked):
                    list_.append(gp)
            retval[power] = list_
        return retval

    def background(self, mask=MASK_ALL_BG):
        """
        Returns a list of background strings for the tournament
        """
        results = []
        for tp in self.tournamentplayer_set.all():
            results += tp.player.background(mask=mask)
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def news(self):
        """
        Returns a list of news strings for the tournament
        """
        results = []
        include_leader = False
        current_round = self.current_round()
        # Always include the number of players
        if self.is_finished():
            tense_str = _('were')
        else:
            tense_str = _('are')
        results.append(_('%(count)d players %(are)s registered to play in the tournament.')
                       % {'count': self.tournamentplayer_set.count(),
                          'are': tense_str})
        if current_round:
            # Include who is leading the tournament
            include_leader = True
            if current_round.in_progress():
                # And which round is currently being played
                results.append(_(u'Round %(r_num)d of %(rounds)d is currently being played.')
                               % {'r_num': current_round.number(),
                                  'rounds': self.round_set.count()})
            else:
                results.append(_(u'Round %(r_num)d of %(rounds)d will start at %(date)s.')
                               % {'r_num': current_round.number(),
                                  'rounds': self.round_set.count(),
                                  'date': str(current_round.start)})
            # Get the news for the current round
            results += current_round.news()
        # If the tournament is over, just report the top three players, plus best countries
        elif self.is_finished():
            for player, (rank, score) in self.positions_and_scores()[0].items():
                if rank in [1, 2, 3]:
                    results.append(_(u'%(player)s came %(pos)s, with a score of %(score).2f.')
                                   % {'player': str(player),
                                      'pos':  position_str(rank),
                                      'score':  score})
            # Add best countries
            for power, gps in self.best_countries().items():
                gp = gps[0]
                if len(gps) == 1:
                    results.append(_(u'%(player)s won Best %(country)s with %(dots)d centre(s) and a score of %(score).2f in game %(game)s of round %(round)d.')
                                   % {'player': str(gp.player),
                                      'country': power.name,
                                      'dots': gp.final_sc_count(),
                                      'score': gp.score,
                                      'game': gp.game.name,
                                      'round': gp.game.the_round.number()})
                else:
                    # Tie for best power
                    winner_str = ', '.join([str(p.player) for p in gps])
                    results.append(_(u'Best %(country)s was jointly won by %(winner_str)s with %(dots)d centre(s) and a score of %(score).2f.')
                                   % {'country': power.name,
                                      'winner_str': winner_str,
                                      'dots': gp.final_sc_count(),
                                      'score': gp.score})
        else:
            # which rounds have been played ?
            played_rounds = 0
            for r in self.round_set.all():
                if r.is_finished():
                    played_rounds += 1
            if played_rounds == 0:
                results.append(_(u'Tournament has yet to start.'))
            else:
                if played_rounds == 1:
                    have_str = u'has'
                else:
                    have_str = u'have'
                results.append(_(u'%(r_num)d of %(rounds)d rounds %(have)s been played.')
                               % {'r_num': played_rounds,
                                  'rounds': self.round_set.count(),
                                  'have': have_str})
                # Include who is leading the tournament
                include_leader = True
        if include_leader:
            the_scores = self.scores_detail()[0]
            if the_scores:
                max_score = max(the_scores.values())
                winners = [str(k) for k, v in the_scores.items() if v == max_score]
                player_str = ', '.join(winners)
                results.append(_(u'If the tournament ended now, the winning score would be %(score).2f for %(players)s.')
                               % {'score': max_score,
                                  'players': player_str})
            # Include the top score from each previous round (if any)
            for r in self.round_set.all():
                if r.is_finished():
                    results.append(r.leader_str())
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def current_round(self):
        """
        Returns the Round in progress, or None
        """
        # Rely on the default ordering
        rds = self.round_set.reverse()
        for r in rds:
            if r.in_progress():
                return r
        # If no round is in progress, return the first unfinished round
        rds = self.round_set.all()
        for r in rds:
            if not r.is_finished():
                return r
        return None

    def is_finished(self):
        """
        Returns True if the tournament has rounds, and they are all finished.
        Returns False otherwise.
        """
        rds = self.round_set.all()
        # If there are no rounds, the tournament can't have started
        if not rds:
            return False
        # Look for any unfinished round
        for r in rds:
            if not r.is_finished():
                return False
        return True

    def wdd_url(self):
        """
        URL for this tournament in the World Diplomacy Database, if known.
        """
        if self.wdd_tournament_id:
            return WDD_BASE_URL + 'tournament_class.php?id_tournament=%d' % self.wdd_tournament_id
        return u''

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('tournament_detail', args=[str(self.id)])

    def __str__(self):
        return '%s %d' % (self.name, self.start_date.year)


class TournamentPlayer(models.Model):
    """
    One player in a tournament
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    unranked = models.BooleanField(default=False,
                                   verbose_name=_('Ineligible for awards'),
                                   help_text=_('Set this to ignore this player when determining rankings'))
    uuid_str = models.CharField(max_length=36, blank=True)

    class Meta:
        ordering = ['player']
        # Each player can only be in each tournament once
        unique_together = ('player', 'tournament')

    def position(self):
        """
        Where is the player (currently) ranked overall in the tournament?
        Returns Tournament.UNRANKED if self.unranked is True.
        """
        return self.tournament.positions_and_scores()[0][self.player][0]

    def roundplayers(self):
        """
        Returns a QuerySet for the corresponding RoundPlayers.
        """
        return self.player.roundplayer_set.filter(the_round__tournament=self.tournament).distinct()

    def create_preferences_from_string(self, the_string):
        """
        Given a string like "AEGFIRT", creates the corresponding Preferences
        in the database.
        Powers will be assigned a ranking from 1 for the first.
        Excluded powers will be unranked.
        Any pre-existing preferences for the player will be deleted.
        Raises InvalidPreferenceList if anything is wrong with the string.
        """
        # Convert the preference string to all uppercase
        the_string = the_string.upper()
        try:
            validate_preference_string(the_string)
        except ValidationError as e:
            raise InvalidPreferenceList(str(e))
        # Remove any existing preferences for this player
        self.preference_set.all().delete()
        to_power = {}
        for p in GreatPower.objects.all():
            to_power[p.abbreviation] = p
        # Go through the string, creating Preferences
        for i, c in enumerate(the_string, 1):
            Preference.objects.create(player=self, power=to_power[c], ranking=i)

    def prefs_string(self):
        """
        Returns the preferences for this TournamentPlayer as a string.
        More-or-less the inverse of create_preferences_from_string().
        """
        ret = []
        for p in self.preference_set.all():
            ret.append(p.power.abbreviation)
        return ''.join(ret)

    def get_prefs_url(self):
        """
        Returns the absolute URL to update the preferences for this
        TournamentPlayer.
        """
        if not self.uuid_str:
            self._generate_uuid()
        path = reverse('player_prefs',
                       args=[str(self.tournament.id), self.uuid_str])
        return 'https://%(host)s%(path)s' % {'host': settings.HOSTNAME,
                                             'path': path}

    def _generate_uuid(self):
        """
        Populates the uuid_str attribute.
        """
        self.uuid_str = str(uuid.uuid4())

    def __str__(self):
        return _('%(player)s at %(tourney)s') % {'tourney': self.tournament,
                                                 'player': self.player}

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Update background info when a player is added to the Tournament (only)
        if is_new:
            send_prefs_email(self)
            add_player_bg(self.player)


def validate_weight(value):
    """
    Checks a SeederBias weight.
    """
    if value < 1:
        raise ValidationError(_('%(value)d is not a valid weighting'),
                              params={'value': value})


class SeederBias(models.Model):
    """
    Tell the game seeder to avoid putting two players in the same game.
    """
    player1 = models.ForeignKey(TournamentPlayer,
                                on_delete=models.CASCADE)
    player2 = models.ForeignKey(TournamentPlayer,
                                on_delete=models.CASCADE,
                                related_name='second_seederbias_set')
    weight = models.PositiveSmallIntegerField(validators=[validate_weight],
                                              help_text=_("Number of games to pretend they've already played together"))

    class Meta:
        verbose_name_plural = 'Seeder biases'
        # Only one weighting per pair of players
        unique_together = ('player1', 'player2')

    def clean(self):
        """
        Validate the object.
        player1 != player2.
        All players are from the same Tournament.
        """
        if self.player1 == self.player2:
            raise ValidationError(_('The players must differ'))
        if self.player1.tournament != self.player2.tournament:
            raise ValidationError(_('The players must be playing the same tournament'))

    def __str__(self):
        return _("%(p1)s and %(p2)s at %(tourney)s") % {'p1': self.player1.player,
                                                        'p2': self.player2.player,
                                                        'tourney': self.player1.tournament}


class Preference(models.Model):
    """
    How much a player wants to play a particular power.
    """
    player = models.ForeignKey(TournamentPlayer, on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, on_delete=models.CASCADE)
    ranking = models.PositiveSmallIntegerField(validators=[validate_ranking])

    class Meta:
        # Each player can only have one ranking per power
        unique_together = ('player', 'power')
        # Every ranking by a player must be unique
        unique_together = ('player', 'ranking')
        # Highest-rank first
        ordering = ['ranking']

    def __str__(self):
        return _('%(player)s ranks %(power)s at %(rank)d') % {'player': self.player,
                                                              'power': self.power.name,
                                                              'rank': self.ranking}


class Round(models.Model):
    """
    A single round of a Tournament
    """
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    # How do we combine game scores to get an overall player score for a round ?
    # This is the name of a GameScoringSystem object
    # There has at least been talk of tournaments using multiple scoring systems, one per round
    scoring_system = models.CharField(max_length=40,
                                      verbose_name=_(u'Game scoring system'),
                                      choices=get_scoring_systems(G_SCORING_SYSTEMS),
                                      help_text=_(u'How to calculate a score for one game'))
    dias = models.BooleanField(verbose_name=_(u'Draws Include All Survivors'))
    start = models.DateTimeField()
    final_year = models.PositiveSmallIntegerField(blank=True,
                                                  null=True,
                                                  validators=[validate_year])
    earliest_end_time = models.DateTimeField(blank=True, null=True)
    latest_end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['start']

    def scores(self, force_recalculation=False):
        """
        Returns the scores for everyone who played in the round.
        Returns a dict, keyed by Player, of floats.
        """
        # If the round is over, report the stored scores unless we're told to recalculate
        if not force_recalculation and self.is_finished():
            retval = {}
            for p in self.roundplayer_set.all():
                retval[p.player] = p.score
            return retval

        # Find the scoring system to combine game scores into a round score
        system = find_round_scoring_system(self.tournament.round_scoring_system)
        if not system:
            raise InvalidScoringSystem(self.tournament.round_scoring_system)
        # Identify any players who were checked in but didn't play
        gps = GamePlayer.objects.filter(game__the_round=self).distinct()
        non_players = self.roundplayer_set.exclude(player__in=[gp.player for gp in gps])
        return system.scores(gps, non_players)

    def store_scores(self):
        """
        Recalculate the scores for the Round,
        and store them in the RoundPlayers.
        """
        scores = self.scores(True)
        for p in self.roundplayer_set.all():
            p.score = scores[p.player]
            p.save()

    def is_finished(self):
        """
        Returns True if the Round has games, and they have all finished.
        Returns False otherwise.
        """
        gs = self.game_set.all()
        if not gs:
            # Rounds with no games can't have started
            return False
        for g in gs:
            if not g.is_finished:
                return False
        return True

    def in_progress(self):
        """
        Returns True if the Round has RoundPlayers (i.e. roll call has happened)
        or Games, and it hasn't finished.
        """
        if not self.roundplayer_set.exists() and not self.game_set.exists():
            # Not yet started
            return False
        # Started, so in_progress unless already finished
        return not self.is_finished()

    def number(self):
        """
        Which round within the tournament is this one ?
        """
        rounds = self.tournament.round_set.all()
        for count, r in enumerate(rounds, 1):
            if r == self:
                return count
        assert 0, u"Round doesn't exist within its own tournament"

    def leader_str(self):
        """
        Returns a news string detailing the person with the best score
        for the round.
        """
        the_scores = self.scores()
        if not the_scores:
            return None
        max_score = max(the_scores.values())
        winners = [k for k, v in the_scores.items() if v == max_score]
        if self.is_finished():
            done_str = _(u'Final')
        else:
            done_str = _(u'Current')
        player_str = ', '.join([str(w) for w in winners])
        return _(u'%(done)s top score for round %(r_num)d is %(score).2f for %(players)s.') % {'done': done_str,
                                                                                               'r_num': self.number(),
                                                                                               'score': max_score,
                                                                                               'players': player_str}

    def news(self):
        """
        Returns a list of news strings for the round.
        This is the latest news for every game in the round.
        """
        results = []
        # Include who has done best in the round (so far)
        ls = self.leader_str()
        if ls:
            results.append(ls)
        # Always include the number of players
        if self.is_finished():
            tense_str = _('were')
        else:
            tense_str = _('are')
        results.append(_('%(count)d players %(are)s registered to play in the round.')
                       % {'count': self.roundplayer_set.count(),
                          'are': tense_str})
        # Get the news for every game in the round
        done_games = 0
        for g in self.game_set.all():
            if g.is_finished:
                done_games += 1
            results += g.news(include_game_name=True)
        # Note if the round has finished
        if self.is_finished():
            results.append(_(u'Round %(r_num)d has ended.') % {'r_num': self.number()})
        elif not self.in_progress:
            results.append(_(u'Round %(r_num)d has not yet started.') % {'r_num': self.number()})
        else:
            # Otherwise, add a count of completed games
            if done_games == 0:
                done_str = _(u'None')
            else:
                done_str = u'%d' % done_games
            results.append(_(u'%(done)s of the %(total_num)d games in round %(r_num)d have ended.')
                           % {'done': done_str,
                              'r_num': self.number(),
                              'total_num': self.game_set.count()})
            # TODO Add time played in the round so far (difficult to internationalise ?)
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def background(self, mask=MASK_ALL_BG):
        """
        Returns a list of background strings for the round
        """
        results = []
        if (mask & MASK_ROUND_ENDPOINTS) != 0 and self.earliest_end_time:
            results.append(_(u'Round %(round)d could end as early as %(time)s.')
                           % {'round': self.number(),
                              'time': self.earliest_end_time.strftime("%H:%M")})
        if (mask & MASK_ROUND_ENDPOINTS) != 0 and self.latest_end_time:
            results.append(_(u'Round %(round)d could end as late as %(time)s.')
                           % {'round': self.number(),
                              'time': self.latest_end_time.strftime("%H:%M")})
        if (mask & MASK_ROUND_ENDPOINTS) != 0 and self.final_year:
            results.append(_(u'Round %(round)d will end after playing year %(year)d.')
                           % {'round': self.number(),
                              'year': self.final_year})
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def clean(self):
        """
        Validate the object.
        Must have either both end times, or neither.
        """
        if self.earliest_end_time and not self.latest_end_time:
            raise ValidationError(_(u'Earliest end time specified without latest end time'))
        if self.latest_end_time and not self.earliest_end_time:
            raise ValidationError(_(u'Latest end time specified without earliest end time'))

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('round_detail',
                       args=[str(self.tournament.id), str(self.number())])

    def __str__(self):
        return _(u'%(tournament)s round %(round)d') % {'tournament': self.tournament,
                                                       'round': self.number()}


def _sc_gains_and_losses(prev_scos, current_scos):
    """
    Returns two dicts (gains then losses), indexed by GreatPower, of
      2-tuples containing SupplyCentre and other Power (previous owner
      (None if neutral) or new owner).
    Parameters are two QuerySets for last year and this year's
      SupplyCentreOwnerships.
    """
    # Extract the info we need into two sets that can be operated on
    prev = set()
    for sco in prev_scos.all():
        prev.add((sco.sc, sco.owner))
    current = set()
    for sco in current_scos.all():
        current.add((sco.sc, sco.owner))
    gains = {}
    losses = {}
    for sc, owner in prev - current:
        for s, o in current:
            if s == sc:
                new_owner = o
                break
        losses.setdefault(owner, []).append((sc, new_owner))
    for sc, owner in current - prev:
        prev_owner = None
        for s, o in prev:
            if s == sc:
                prev_owner = o
                break
        gains.setdefault(owner, []).append((sc, prev_owner))
    return gains, losses


class Game(models.Model):
    """
    A single game of Diplomacy, within a Round
    """
    name = models.CharField(max_length=20,
                            validators=[validate_game_name],
                            help_text=_(u'Must be unique within the tournament. No spaces'))
    started_at = models.DateTimeField(default=timezone.now)
    is_finished = models.BooleanField(default=False)
    is_top_board = models.BooleanField(default=False)
    the_round = models.ForeignKey(Round, verbose_name=_(u'round'), on_delete=models.CASCADE)
    the_set = models.ForeignKey(GameSet, verbose_name=_(u'set'), on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    def assign_powers_from_prefs(self):
        """
        Assigns powers to the GamePlayers.
        The player with the lowest tournament score gets first choice,
        the player with the highest score gets whatever power nobody else wants.
        If players have the same score, they are ordered randomly.
        Raises PowerAlreadyAssigned if any GamePlayers already have assigned
        powers.
        """
        position_to_gps = {}
        gps = self.gameplayer_set.all()
        # Find current tournament positions (and scores)
        ranks = self.the_round.tournament.positions_and_scores()[0]
        # Check for any GamePlayer that already has a power assigned
        # and find the interesting player positions
        for gp in gps:
            if gp.power:
                raise PowerAlreadyAssigned(str(gp) + ' is already assigned ' + str(gp.power))
            pos = ranks[gp.player][0]
            position_to_gps.setdefault(pos, []).append(gp)
        # Starting from the lowest rank, work through the whole list
        for pos in sorted(position_to_gps.keys()):
            # At each rank, order players randomly
            random.shuffle(position_to_gps[pos])
            for gp in position_to_gps[pos]:
                gp.set_power_from_prefs()

    def create_or_update_sc_counts_from_ownerships(self, year):
        """
        Ensures that there is one CentreCount for each power for the
        specified year, and that the values match those determined by
        looking at the SupplyCentreOwnerships for that year.
        Can raise SCOwnershipsNotFound.
        """
        all_scos = self.supplycentreownership_set.filter(year=year)
        if not all_scos.exists():
            raise SCOwnershipsNotFound('%d of game %s' % (year, str(self)))
        for p in GreatPower.objects.all():
            i = CentreCount.objects.update_or_create(power=p,
                                                     game=self,
                                                     year=year,
                                                     defaults={'count': all_scos.filter(owner=p).count()})[0]
            i.save()

    def compare_sc_counts_and_ownerships(self, year):
        """
        Compares the SupplyCentreOwnerships and CentreCounts for the given
        game year.
        Returns a list of strings describing any issues.
        Can raise SCOwnershipsNotFound.
        """
        all_scos = self.supplycentreownership_set.filter(year=year)
        if not all_scos.exists():
            raise SCOwnershipsNotFound('%d of game %s' % (year, str(self)))
        retval = []
        for p in GreatPower.objects.all():
            sco_dots = all_scos.filter(owner=p).count()
            try:
                cc = CentreCount.objects.get(power=p,
                                             game=self,
                                             year=year)
            except CentreCount.DoesNotExist:
                retval.append(_('Missing count of %(dots)d centre(s) for %(power)s')
                              % {'dots': sco_dots,
                                 'power': p})
            else:
                if cc.count != sco_dots:
                    retval.append(_('%(power)s owns %(sco_dots)d centre(s) in %(year)d, but their centrecount is %(dots)d')
                                  % {'power': p,
                                     'year': year,
                                     'sco_dots': sco_dots,
                                     'dots': cc.count})
        return retval

    def scores(self, force_recalculation=False):
        """
        If the game has ended and force_recalculation is False,
        report the recorded scores.
        If the game has not ended or force_recalculation is True,
        calculate the scores if the game were to end now.
        Return value is a dict, indexed by power id, of scores.
        """
        if not force_recalculation and self.is_finished:
            # Return the stored scores for the game
            retval = {}
            players = self.gameplayer_set.all()
            for p in players:
                # TODO Need to combine scores if multiple players played a power
                retval[p.power] = p.score
            return retval

        # Calculate the scores for the game using the specified ScoringSystem
        system = find_game_scoring_system(self.the_round.scoring_system)
        if not system:
            raise InvalidScoringSystem(self.the_round.scoring_system)
        return system.scores(self.centrecount_set.all())

    def positions(self):
        """
        Returns the positions of all the powers.
        Dict, keyed by power id, of integer rankings (1 for first place,
        2 for second place, etc)
        """
        result = {}
        last_score = None
        for i, (k, v) in enumerate(sorted([(k, v) for k, v in self.scores().items()],
                                          key=itemgetter(1),
                                          reverse=True),
                                   start=1):
            if v != last_score:
                place, last_score = i, v
            result[k] = place
        return result

    def is_dias(self):
        """
        Returns whether the game is Draws Include All Survivors
        """
        return self.the_round.dias

    def years_played(self):
        """
        Returns a list of years for which there are SC counts for this game
        """
        scs = self.centrecount_set.all()
        return sorted(list({sc.year for sc in scs}))

    def players(self, latest=True):
        """
        Returns a dict, keyed by power, of lists of players of that power
        If latest is True, only include the latest player of each power
        """
        powers = GreatPower.objects.all()
        gps = self.gameplayer_set.all().order_by('-first_year')
        retval = {}
        for power in powers:
            ps = gps.filter(power=power)
            if latest:
                ps = ps[0:1]
            retval[power] = [gp.player for gp in ps]
        return retval

    def news(self, include_game_name=False, mask=MASK_ALL_NEWS):
        """
        Returns a list of strings the describe the latest events in the game
        """
        if include_game_name:
            gn_str = _(u' in game %(name)s') % {'name': self.name}
        else:
            gn_str = ''
        if self.is_finished:
            # Just report the final result
            return [self.result_str(include_game_name) + '.']
        centres_set = self.centrecount_set.order_by('-year')
        # Which is the most recent year we have info for ?
        last_year = centres_set[0].year
        # If the game just started, there is no news, so return the background instead
        if last_year == 1900:
            return self.background()
        player_dict = self.players(latest=True)
        current_scs = centres_set.filter(year=last_year)
        current_scos = self.supplycentreownership_set.filter(year=last_year)
        results = []
        if (mask & MASK_SC_OWNER_COUNTS):
            # Which dots have had lots of owners?
            owner_sets = {}
            for sco in self.supplycentreownership_set.all():
                if sco.sc not in owner_sets:
                    owner_sets[sco.sc] = set()
                owner_sets[sco.sc].add(sco.owner)
            for sc, set_ in owner_sets.items():
                if len(set_) > 3:
                    results.append(_('%(dot)s has been owned by %(owners)d different Great Powers (%(list)s).')
                                   % {'dot': sc,
                                      'owners': len(set_),
                                      'list': ','.join([p.abbreviation for p in set_])})
        if (mask & MASK_BOARD_TOP) != 0:
            # Who's topping the board ?
            max_scs = current_scs.order_by('-count')[0].count
            first = current_scs.order_by('-count').filter(count=max_scs)
            first_str = ', '.join(['%s (%s)' % (player_dict[scs.power][0],
                                                _(scs.power.abbreviation)) for scs in list(first)])
            results.append(_(u'Highest SC count%(game)s is %(dots)d, for %(player)s.')
                           % {'game': gn_str,
                              'dots': max_scs,
                              'player': first_str})
        if last_year > 1900:
            prev_scs = centres_set.filter(year=last_year-1)
            prev_scos = self.supplycentreownership_set.filter(year=last_year-1)
            sc_gains, sc_losses = _sc_gains_and_losses(prev_scos, current_scos)
        else:
            # We only look for differences, so just force no differences
            prev_scs = current_scs
            sc_gains = {}
            sc_losses = {}
        for scs in current_scs:
            power = scs.power
            try:
                prev = prev_scs.get(power=power)
            except CentreCount.DoesNotExist:
                continue
            # Who gained 2 or more centres in the last year ?
            if (mask & MASK_GAINERS) != 0:
                if scs.count - prev.count > 1:
                    results.append(_(u'%(player)s (%(power)s) grew from %(old)d to %(new)d centres%(game)s.')
                                   % {'player': player_dict[power][0],
                                      'power': _(power.abbreviation),
                                      'old': prev.count,
                                      'new': scs.count,
                                      'game': gn_str})
            # Who lost 2 or more centres in the last year ?
            if (mask & MASK_LOSERS) != 0:
                if prev.count - scs.count > 1:
                    results.append(_(u'%(player)s (%(power)s) shrank from %(old)d to %(new)d centre(s)%(game)s.')
                                   % {'player': player_dict[power][0],
                                      'power': _(power.abbreviation),
                                      'old': prev.count,
                                      'new': scs.count,
                                      'game': gn_str})
            # Who took 2 or more, lost 2 or more, or had a total of 4 or more gains and losses?
            if (mask & MASK_SC_CHANGES) != 0:
                gains = sc_gains.get(power, [])
                losses = sc_losses.get(power, [])
                if (len(gains) > 2) or (len(losses) > 2) or (len(gains) + len(losses) > 3):
                    if gains:
                        gains_str = ''
                        for s, p in gains:
                            if gains_str:
                                gains_str += ', '
                            if p:
                                gains_str += _('%(sc)s (from %(power)s)' % {'sc': s.abbreviation,
                                                                            'power': p.abbreviation})
                            else:
                                gains_str += _('%(sc)s (neutral)' % {'sc': s.abbreviation})
                    else:
                        gains_str = _('no centres')
                    if losses:
                        losses_str = ', '.join(_('%(sc)s (to %(power)s)' % {'sc': s.abbreviation,
                                                                            'power': p.abbreviation}) for s, p in losses)
                    else:
                        losses_str = _('no centres')
                    results.append(_('%(player)s (%(power)s) took %(gains)s and lost %(losses)s%(game)s.')
                                   % {'player': player_dict[power][0],
                                      'power': _(power.abbreviation),
                                      'gains': gains_str,
                                      'losses': losses_str,
                                      'game': gn_str})
        # How many non-neutrals were captured?
        if (last_year > 1900) and ((mask & MASK_SC_CHANGE_COUNTS) != 0):
            count = 0
            for l in sc_losses.values():
                count += len(l)
            results.append(_('%(count)d non-neutral centre(s) changed hands%(game)s.')
                           % {'count': count,
                              'game': gn_str})
        if (mask & MASK_DRAW_VOTES) != 0:
            # How many draw votes have there been ?
            votes = self.drawproposal_set.count()
            results.append(_('%(count)d draw vote(s) have been taken.')
                           % {'count': votes})
            # What draw votes failed recently ?
            # Note that it's fairly arbitrary where we draw the line here
            draws_set = self.drawproposal_set.order_by('-year').filter(year__gte=last_year)
            # TODO Lots of overlap with result_str()
            for d in draws_set:
                powers = d.powers()
                sz = len(powers)
                incl = []
                for power in powers:
                    # TODO This looks broken if there were replacements
                    game_player = self.gameplayer_set.get(power=power)
                    incl.append(_(u'%(player)s (%(power)s)') % {'player': game_player.player,
                                                                'power': _(power.abbreviation)})
                incl_str = ', '.join(incl)
                if self.the_round.tournament.draw_secrecy == Tournament.COUNTS:
                    count_str = _(', %(for)d for, %(against)d against' % {'for': d.votes_in_favour,
                                                                          'against': d.votes_against()})
                else:
                    count_str = ''
                if sz == 1:
                    d_str = _(u'Vote to concede to %(powers)s failed%(game)s%(count)s.') % {'powers': incl_str,
                                                                                            'game': gn_str,
                                                                                            'count': count_str}
                else:
                    d_str = _(u'Draw vote for %(n)d-way between %(powers)s failed%(game)s%(count)s.') % {'n': sz,
                                                                                                         'powers': incl_str,
                                                                                                         'game': gn_str,
                                                                                                         'count': count_str}
                results.append(d_str)
        if (mask & MASK_ELIMINATIONS) != 0:
            # Who has been eliminated so far, and when ?
            zeroes = centres_set.filter(count=0).reverse()
            while zeroes:
                scs = zeroes[0]
                power = scs.power
                zeroes = zeroes.exclude(power=power)
                results.append(_(u'%(player)s (%(power)s) was eliminated in %(year)d%(game)s.')
                               % {'player': player_dict[power][0],
                                  'power': _(power.abbreviation),
                                  'year': scs.year,
                                  'game': gn_str})
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def background(self, mask=MASK_ALL_BG):
        """
        Returns a list of strings that give background for the game
        """
        players_by_power = self.players(latest=True)
        results = []
        for c, players in players_by_power.items():
            for p in players:
                results += p.background(c, mask=mask)
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def passed_draw(self):
        """
        Returns either a DrawProposal if a draw vote passed, or None.
        """
        # Did a draw proposal pass ?
        try:
            return self.drawproposal_set.get(passed=True)
        except DrawProposal.DoesNotExist:
            return None

    def board_toppers(self):
        """
        Returns a list of CentreCounts for the current leader(s)
        """
        current_scs = self.centrecount_set.filter(year=self.final_year()).order_by('-count')
        max_scs = current_scs[0].count
        first = current_scs.filter(count=max_scs)
        return list(first)

    def neutrals(self, year=None):
        """How many neutral SCs are/were there ?"""
        if year is None:
            year = self.final_year()
        scs = self.centrecount_set.filter(year=year)
        if not scs.exists():
            raise InvalidYear(year)
        return TOTAL_SCS - scs.aggregate(Sum('count'))['count__sum']

    def final_year(self):
        """
        Returns the last complete year of the game, whether the game is
        completed or ongoing
        """
        return self.centrecount_set.all().aggregate(Max('year'))['year__max']

    def soloer(self):
        """
        Returns either a GamePlayer if somebody soloed the game, or None
        """
        # Just order by SC count, and check the first (highest)
        scs = self.centrecount_set.order_by('-count')
        if scs[0].count >= WINNING_SCS:
            # TODO This looks like it fails if the soloer was a replacement player
            return self.gameplayer_set.get(power=scs[0].power)
        return None

    def survivors(self, year=None):
        """
        Returns a list of the CentreCounts for the surviving powers.
        If a year is provided, it returns a list of the powers that survived
        that whole year.
        If a year is provided for which there are no CentreCounts, an empty
        list will be returned.
        """
        if year is None:
            year = self.final_year()
        final_scs = self.centrecount_set.filter(year=year)
        return [sc for sc in final_scs if sc.count > 0]

    def result_str(self, include_game_name=False):
        """
        Returns a string representing the game result, if any, or None
        """
        if include_game_name:
            gn_str = ' %s' % self.name
        else:
            gn_str = ''
        # Did a draw proposal pass ?
        draw = self.passed_draw()
        if draw:
            powers = draw.powers()
            sz = len(powers)
            if sz == 1:
                retval = _(u'Game%(game)s conceded to ') % {'game': gn_str}
            else:
                retval = _(u'Vote passed to end game%(game)s as a %(n)d-way draw between ') % {'game': gn_str,
                                                                                               'n': sz}
            winners = []
            for power in powers:
                # TODO This looks broken if there were replacements
                game_player = self.gameplayer_set.get(power=power)
                winners.append(_(u'%(player)s (%(power)s)') % {'player': game_player.player,
                                                               'power': _(power.abbreviation)})
            return retval + ', '.join(winners)
        # Did a power reach 18 (or more) centres ?
        soloer = self.soloer()
        if soloer:
            # TODO would be nice to include their SC count
            return _(u'Game%(game)s won by %(player)s (%(power)s)') % {'game': gn_str,
                                                                       'player': soloer.player,
                                                                       'power': _(soloer.power.abbreviation)}
        # TODO Did the game get to the fixed endpoint ?
        if self.is_finished:
            player_dict = self.players(latest=True)
            toppers = self.board_toppers()
            first_str = ', '.join([_(u'%(player)s (%(power)s)') % {'player': player_dict[scs.power][0],
                                                                   'power': _(scs.power.abbreviation)} for scs in list(toppers)])
            return _(u'Game%(game)s ended. Board top is %(top)d centres, for %(player)s') % {'game': gn_str,
                                                                                             'top': toppers[0].count,
                                                                                             'player': first_str}
        # Then it seems to be ongoing
        return None

    def clean(self):
        """
        Validate the object.
        Game names must be unique within the tournament.
        """
        games = Game.objects.filter(the_round__tournament=self.the_round.tournament).distinct()
        for g in games:
            if (self != g) and (self.name == g.name):
                raise ValidationError(_('Game names must be unique within the tournament'))

    def save(self, *args, **kwargs):
        """
        Save the object to the database.
        Ensures that 1901 SC counts and ownership info exists.
        Ensures that S1901M image exists.
        If the Game is now finished, calculates and saves the scores.
        If the round is now finished, calculates and saves the scores.
        If the tournament is now finished, calculates and saves the scores.
        """
        super().save(*args, **kwargs)

        # Auto-create 1900 SC counts (unless they already exist)
        # Auto-create SC Ownership (unless they already exist)
        for power in GreatPower.objects.all():
            i, _ = CentreCount.objects.get_or_create(power=power,
                                                     game=self,
                                                     year=FIRST_YEAR - 1,
                                                     count=power.starting_centres)
            for sc in SupplyCentre.objects.filter(initial_owner=power):
                i, _ = SupplyCentreOwnership.objects.get_or_create(owner=power,
                                                                   game=self,
                                                                   year=FIRST_YEAR - 1,
                                                                   sc=sc)

        # Auto-create S1901M image (if it doesn't exist)
        i, _ = GameImage.objects.get_or_create(game=self,
                                               year=FIRST_YEAR,
                                               season=SPRING,
                                               phase=GameImage.MOVEMENT)
        i.image = self.the_set.initial_image
        i.save()

        # If the game is (now) finished, store the player scores
        if self.is_finished:
            scores = self.scores(True)
            players = self.gameplayer_set.all()
            # TODO Need to split the score somehow if there were multiple players of a power
            for p in players:
                p.score = scores[p.power]
                p.save()

            # If the round is (now) finished, store the player scores
            r = self.the_round
            if r.is_finished():
                r.store_scores()

            # if the tournament is (now) finished, store the player scores
            t = self.the_round.tournament
            if t.is_finished():
                t.store_scores()

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('game_detail',
                       args=[str(self.the_round.tournament.id), self.name])

    def __str__(self):
        return _('%(game)s at %(tourney)s') % {'game': self.name,
                                               'tourney': self.the_round.tournament}


class SupplyCentreOwnership(models.Model):
    """
    Record of which GreatPower owned a given SupplyCentre
    at the end of a particular game year in a Game.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year_including_start])
    sc = models.ForeignKey(SupplyCentre, on_delete=models.CASCADE)
    owner = models.ForeignKey(GreatPower, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('sc', 'game', 'year')
        ordering = ['game', 'year']

    def __str__(self):
        return _("%(dot)s in %(game)s was owned by %(power)s at the end of %(year)d") % {'dot': self.sc,
                                                                                         'game': self.game,
                                                                                         'power': self.owner,
                                                                                         'year': self.year}


class DrawProposal(models.Model):
    """
    A single draw or concession proposal in a game
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    season = models.CharField(max_length=1, choices=SEASONS)
    passed = models.NullBooleanField(blank=True, null=True)
    proposer = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    power_1 = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    power_2 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    power_3 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    power_4 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    power_5 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    power_6 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    power_7 = models.ForeignKey(GreatPower,
                                blank=True,
                                null=True,
                                related_name='+',
                                on_delete=models.CASCADE)
    votes_in_favour = models.PositiveSmallIntegerField(blank=True,
                                                       null=True,
                                                       validators=[validate_vote_count])

    def draw_size(self):
        """
        Returns the number of powers included in the DrawProposal.
        """
        return len(self.powers())

    def powers(self):
        """
        Returns a list of powers included in the draw proposal.
        """
        retval = []
        for name, value in self.__dict__.items():
            if name.startswith('power_'):
                if value:
                    retval.append(GreatPower.objects.get(pk=value))
        return retval

    def power_is_part(self, power):
        """
        Returns a Boolean indicating whether the specified power is included.
        """
        if self.power_1 == power:
            return True
        if self.power_2 == power:
            return True
        if self.power_3 == power:
            return True
        if self.power_4 == power:
            return True
        if self.power_5 == power:
            return True
        if self.power_6 == power:
            return True
        if self.power_7 == power:
            return True
        return False

    def votes_against(self):
        """
        Returns the number of votes against the draw proposal.
        """
        # Get the most recent CentreCounts before the DrawProposal
        scs = self.game.centrecount_set.filter(year__lt=self.year)
        survivors = scs.filter(count__gt=0).count()
        try:
            return survivors - self.votes_in_favour
        except TypeError:
            raise TypeError(_('This DrawProposal only has pass/fail, not vote counts'))

    def clean(self):
        """
        Validate the object.
        The Power_N attributes must be used in numerical order.
        Each GreatPower must only appear a maximum of once in the Power_N
        attributes.
        Only one DrawProposal for a given Game can be successful.
        A successful DrawProposal for a Game cannot happen after any
        CentreCount.
        Dead powers cannot be included.
        If the Tournament has its draw_secrecy attribute set to SECRET,
        the passed attribute must be set.
        If the Tournament has its draw_secrecy attribute set to COUNTS,
        the votes_in_favour attribute must be set.
        """
        # No skipping powers
        found_null = False
        for n in range(1, 8):
            if not self.__dict__['power_%d_id' % n]:
                found_null = True
            elif found_null:
                raise ValidationError(_(u'Draw powers should go as early as possible'))
        # Each power must be unique
        powers = set()
        for name, value in self.__dict__.items():
            if value and name.startswith('power_'):
                power = GreatPower.objects.get(pk=value)
                if power in powers:
                    raise ValidationError(_(u'%(power)s present more than once'),
                                          params={'power':  power})
                powers.add(power)
        # Only one successful draw proposal
        if self.passed:
            try:
                p = DrawProposal.objects.get(game=self.game,
                                             passed=True)
                if p != self:
                    raise ValidationError(_(u'Game already has a successful draw proposal'))
            except DrawProposal.DoesNotExist:
                pass
        # No successful proposal prior to the latest SC count
        final_year = self.game.final_year()
        if self.passed and (self.year <= final_year):
            raise ValidationError(_(u'Game already has a centre count for %(year)d'),
                                  params={'year': final_year})
        # No dead powers included
        # If DIAS, all alive powers must be included
        dias = self.game.is_dias()
        # Get the most recent CentreCounts before the DrawProposal
        scs = self.game.centrecount_set.filter(year__lt=self.year)
        # We will always have at least the 1900 CentreCounts, and DrawProposal.year must be >= 1901
        scs = scs.filter(year=scs.last().year)
        for sc in scs:
            if sc.power in powers:
                if sc.count == 0:
                    raise ValidationError(_(u'Dead power %(power)s included in proposal'),
                                          params={'power': sc.power})
            else:
                if dias and sc.count > 0:
                    raise ValidationError(_(u'Missing alive power %(power)s in DIAS game'),
                                          params={'power': sc.power})
        # Ensure that either passed or votes_in_favour, as appropriate, are set
        if self.game.the_round.tournament.draw_secrecy == Tournament.SECRET:
            if self.passed is None:
                raise ValidationError(_('Passed needs a value'))
        elif self.game.the_round.tournament.draw_secrecy == Tournament.COUNTS:
            if self.votes_in_favour is None:
                raise ValidationError(_('Votes_in_favour needs a value'))
        else:
            assert 0, 'Tournament draw secrecy has an unexpected value %c' % self.game.the_round.tournament.draw_secrecy

    def save(self, *args, **kwargs):
        if self.game.the_round.tournament.draw_secrecy == Tournament.COUNTS:
            # Derive passed from votes_in_favour and survivor count
            survivors = len(self.game.survivors())
            if self.votes_in_favour:
                # Votes must be unanimous
                self.passed = (self.votes_in_favour == survivors)
        super().save(*args, **kwargs)
        # Does this complete the game ?
        if self.passed:
            self.game.is_finished = True
            self.game.save()

    def __str__(self):
        return '%(game)s %(year)d%(season)s' % {'game': self.game,
                                                'year': self.year,
                                                'season': self.season}


class RoundPlayer(models.Model):
    """
    A person who played a round in a tournament
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    the_round = models.ForeignKey(Round, verbose_name=_(u'round'), on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    game_count = models.PositiveIntegerField(default=1,
                                             help_text=_('number of games being played this round'))

    class Meta:
        ordering = ['player']

    def tournamentplayer(self):
        """
        Returns the TournamentPlayer corresponding to this RoundPlayer.
        """
        return self.player.tournamentplayer_set.get(tournament=self.the_round.tournament)

    def gameplayers(self):
        """
        Returns a QuerySet for the corresponding GamePlayers.
        """
        return self.player.gameplayer_set.filter(game__the_round=self.the_round).distinct()

    def clean(self):
        """
        Validate the object.
        There must already be a corresponding TournamentPlayer.
        """
        t = self.the_round.tournament
        if not self.player.tournamentplayer_set.filter(tournament=t).exists():
            raise ValidationError(_(u'Player is not yet in the tournament'))

    def __str__(self):
        return _(u'%(player)s in %(round)s') % {'player': self.player,
                                                'round': self.the_round}


class GamePlayer(models.Model):
    """
    A person who played a Great Power in a Game
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower,
                              null=True,
                              blank=True,
                              related_name='+',
                              on_delete=models.CASCADE)
    first_year = models.PositiveSmallIntegerField(default=FIRST_YEAR,
                                                  validators=[validate_year])
    first_season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    last_year = models.PositiveSmallIntegerField(blank=True,
                                                 null=True,
                                                 validators=[validate_year])
    last_season = models.CharField(max_length=1, choices=SEASONS, blank=True)
    score = models.FloatField(default=0.0)

    def roundplayer(self):
        """
        Returns the RoundPlayer corresponding to this GamePlayer.
        """
        return self.player.roundplayer_set.get(the_round=self.game.the_round)

    def tournamentplayer(self):
        """
        Returns the TournamentPlayer corresponding to this GamePlayer.
        """
        return self.player.tournamentplayer_set.get(tournament=self.game.the_round.tournament)

    def preferences(self):
        """
        Returns the current Preferences for this player, if any,
        ordered highest-to-lowest.
        """
        return self.tournamentplayer().preference_set.all()

    def elimination_year(self):
        """
        Year in which the player was eliminated, or None.
        """
        sc = self.game.centrecount_set.filter(power=self.power).filter(count=0).order_by('year').first()
        if not sc:
            return None
        e_year = sc.year
        # The power was eliminated. Was this player playing it at the time?
        if not self.last_year:
            return e_year
        if e_year > self.last_year:
            return None
        if e_year == self.last_year and self.last_season == SPRING:
            return None
        return e_year

    def final_sc_count(self):
        """
        Number of SupplyCentres held at the end of the Game,
        or currently if the Game iss till ongoing.
        """
        game = self.game
        final_year = game.final_year()
        if self.last_year:
            if self.last_season == SPRING:
                final_year = self.last_year - 1
            else:
                final_year = self.last_year
        return game.centrecount_set.filter(year__lte=final_year,
                                           power=self.power).last().count

    def set_power_from_prefs(self):
        """
        Set the power attribute from the highest-ranked unassigned power
        in the player's priority list for the tournament.
        """
        prefs = self.preferences()
        gps = self.game.gameplayer_set.all()
        for p in prefs:
            if gps.filter(power=p.power).exists():
                # This power is already taken - on to the next
                continue
            # Found a power that isn't taken
            self.power = p.power
            break
        if self.power is None:
            # No preferences left, so pick a power at random from the unassigned ones
            used_powers = [gp.power for gp in gps.filter(power__isnull=False)]
            free_powers = list(GreatPower.objects.all())
            for p in used_powers:
                free_powers.remove(p)
            random.shuffle(free_powers)
            self.power = free_powers[0]
        assert self.power is not None
        self.save()

    def clean(self):
        """
        Validate the object.
        There must already be a corresponding TournamentPlayer.
        If either of the last_year and last_season attributes are set,
        both must be set.
        Only one Player can be playing this power at any given point in the
        Game.
        """
        # Player should already be in the tournament
        t = self.game.the_round.tournament
        if not self.player.tournamentplayer_set.filter(tournament=t).exists():
            raise ValidationError(_(u'Player is not yet in the tournament'))
        # Need either both or neither of last_year and last_season
        if self.last_season == '' and self.last_year:
            raise ValidationError(_(u'Final season played must also be specified'))
        if self.last_season != '' and not self.last_year:
            raise ValidationError(_(u'Final year must be specified with final season'))
        # Check for overlap with another player
        others = []
        if self.power:
            others = GamePlayer.objects.filter(game=self.game, power=self.power).exclude(player=self.player)
        # Ensure one player at a time
        for other in others:
            # It's possible that the in-memory object has a different player than the one in the database
            if self == other:
                continue
            if self.first_year < other.first_year:
                we_were_first = True
            elif self.first_year == other.first_year:
                if self.first_season == other.first_season:
                    raise ValidationError(_(u'%(player1)s and %(player2)s both start playing %(power)s %(season)s %(year)d'),
                                          params={'player1': other.player,
                                                  'player2': self.player,
                                                  'power': self.power,
                                                  'season': self.first_season,
                                                  'year': self.first_year})
                we_were_first = bool(self.first_season == SPRING)
            else:
                we_were_first = False
            if we_were_first:
                # Our term must finish before theirs started
                err_str = _(u'%(player)s is listed as playing %(power)s in game %(game)s from %(season)s %(year)d')
                if not self.last_year or self.last_year > other.first_year:
                    raise ValidationError(err_str,
                                          params={'player': other.player,
                                                  'power': other.power,
                                                  'game': other.game.name,
                                                  'season': other.first_season,
                                                  'year': other.first_year})
                if self.last_year == other.first_year:
                    if self.last_season != SPRING or other.first_season != FALL:
                        raise ValidationError(err_str,
                                              params={'player': other.player,
                                                      'power': other.power,
                                                      'game': other.game.name,
                                                      'season': other.first_season,
                                                      'year': other.first_year})
            else:
                # Their term must finish before ours started
                err_str = _(u'%(player)s is listed as still playing %(power)s in game %(game)s from %(season)s %(year)d')
                if not other.last_year or other.last_year > self.first_year:
                    raise ValidationError(err_str,
                                          params={'player': other.player,
                                                  'power': other.power,
                                                  'game': other.game,
                                                  'season': other.first_season,
                                                  'year': other.first_year})
                if other.last_year == self.first_year:
                    if other.last_season != SPRING or self.first_season != FALL:
                        raise ValidationError(err_str,
                                              params={'player': other.player,
                                                      'power': other.power,
                                                      'game': other.game,
                                                      'season': other.first_season,
                                                      'year': other.first_year})
        # TODO Ensure no gaps - may have to be done elsewhere

    def __str__(self):
        if self.power:
            return _('%(player)s as %(power)s in %(game)s') % {'game': self.game,
                                                               'player': self.player,
                                                               'power': self.power}
        return _('%(player)s in %(game)s Power TBD') % {'game': self.game,
                                                        'player': self.player}


class GameImage(models.Model):
    """
    An image depicting a Game at a certain point.
    The year, season, and phase together indicate the phase that is about to
    be played.
    """
    MOVEMENT = 'M'
    RETREATS = 'R'
    # Use X for adjustments to simplify sorting
    ADJUSTMENTS = 'X'

    PHASES = (
        (MOVEMENT, _('movement')),
        (RETREATS, _('retreats')),
        (ADJUSTMENTS, _('adjustments')),
    )
    # Map a PHASE to its human-readable form
    PHASE_STR = {
        MOVEMENT: 'M',
        RETREATS: 'R',
        ADJUSTMENTS: 'A',
    }

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    phase = models.CharField(max_length=1, choices=PHASES, default=MOVEMENT)
    image = models.ImageField(upload_to=game_image_location)

    class Meta:
        unique_together = ('game', 'year', 'season', 'phase')
        ordering = ['game', 'year', '-season', 'phase']

    def turn_str(self):
        """
        Short string version of season/year/phase
        e.g. 'S1901M'
        """
        return u'%s%d%s' % (self.season, self.year, self.PHASE_STR[self.phase])

    def clean(self):
        """
        Validate the object.
        The phase attribute can only be set to ADJUSTMENTS when the season
        attribute is set to FALL.
        """
        if self.season == SPRING and self.phase == self.ADJUSTMENTS:
            raise ValidationError(_(u'No adjustment phase in spring'))

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('game_image', args=[str(self.game.the_round.tournament.id),
                                           self.game.name,
                                           self.turn_str()])

    def __str__(self):
        return _(u'%(game)s %(turn)s image') % {'game': self.game,
                                                'turn': self.turn_str()}


class CentreCount(models.Model):
    """
    The number of centres owned by one power at the end of a given game year
    """
    power = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year_including_start])
    count = models.PositiveSmallIntegerField(validators=[validate_sc_count])

    class Meta:
        unique_together = ('power', 'game', 'year')
        ordering = ['game', 'year']

    def clean(self):
        """
        Validate the object.
        The year attribute must pre-date the Round's final_year attribute,
        if any.
        The count attribute cannot be more than double that for the same power
        in the previous year.
        If the count for this power for any preivous year was zero,
        the count attribute must be zero.
        """
        # Is this for a year that is supposed to be played ?
        final_year = self.game.the_round.final_year
        if final_year and self.year > final_year:
            raise ValidationError(_(u'Games in this round end with %(year)d'),
                                  params={'year': final_year})
        # Not possible to more than double your count in one year
        # or to recover from an elimination
        try:
            prev = CentreCount.objects.get(power=self.power,
                                           game=self.game,
                                           year=self.year - 1)
        except CentreCount.DoesNotExist:
            # We're either missing a year, or this is the first year - let that go
            return
        if (prev.count == 0) and (self.count > 0):
            raise ValidationError(_(u'SC count for a power cannot increase from zero'))
        if self.count > 2 * prev.count:
            raise ValidationError(_(u'SC count for a power cannot more than double in a year'))

    def __str__(self):
        return u'%(game)s %(year)d %(power)s' % {'game': self.game,
                                                 'year': self.year,
                                                 'power': _(self.power.abbreviation)}
