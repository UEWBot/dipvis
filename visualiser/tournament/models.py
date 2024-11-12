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
from datetime import date, timedelta
import inspect
from operator import itemgetter
from pathlib import Path
import random
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, Max, F, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from tournament import backstabbr
from tournament import webdip

from tournament.background import WDD_BASE_RESULTS_URL
from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.diplomacy.values.diplomacy_values import FIRST_YEAR, WINNING_SCS, TOTAL_SCS
from tournament.diplomacy.tasks.validate_preference_string import validate_preference_string
from tournament.diplomacy.tasks.validate_ranking import validate_ranking
from tournament.diplomacy.tasks.validate_sc_count import validate_sc_count
from tournament.diplomacy.tasks.validate_year import validate_year
from tournament.diplomacy.tasks.validate_year_including_start import validate_year_including_start

from tournament.email import send_prefs_email
from tournament.game_scoring import G_SCORING_SYSTEMS, GameScoringSystem
from tournament.players import Player, add_player_bg
from tournament.players import MASK_ALL_BG, MASK_ROUND_ENDPOINTS, MASK_SERIES_WINS
from tournament.players import validate_wdd_tournament_id
from tournament.tournament_game_state import TournamentGameState


class Seasons(models.TextChoices):
    """Game turn season"""
    SPRING = 'S', _('spring')
    FALL = 'F', _('fall')


class Phases(models.TextChoices):
    """Game turn phase"""
    MOVEMENT = 'M', _('movement')
    RETREATS = 'R', _('retreats')
    # Use X for adjustments to simplify sorting
    ADJUSTMENTS = 'X', _('adjustments')

# Map a PHASE to its human-readable form
PHASE_STR = {
    Phases.MOVEMENT: 'M',
    Phases.RETREATS: 'R',
    Phases.ADJUSTMENTS: 'A',
}


class DrawSecrecy(models.TextChoices):
    """What is revealed about draw votes"""
    SECRET = 'S', _('Pass/Fail')
    COUNTS = 'C', _('Numbers for and against')


class BestCountryCriteria(models.TextChoices):
    """How Best Country awards are determined"""
    SCORE = 'S', _('Highest score')
    DOTS = 'D', _('Highest centre count')


class Formats(models.TextChoices):
    """Tournament formats"""
    FTF = 'F', _('Face to Face')
    VFTF = 'V', _('Virtual Face to Face')


class PowerAssignMethods(models.TextChoices):
    """How powers are assigned to players"""
    AUTO = 'A', _('Minimising playing the same power')
    MANUAL = 'M', _('Manually by TD or at the board')
    PREFERENCES = 'P', _('Using player preferences and ranking')


class InvalidScoringSystem(Exception):
    """The specified scoring system name is not recognised"""
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


class InvalidPowerAssignmentMethod(Exception):
    """The Tournament does not need player input to assign powers."""
    pass


class RoundScoringSystem(ABC):
    """
    A scoring system for a Round.

    Provides a method to calculate a score for each player of one round.
    """
    MAX_NAME_LENGTH=40
    name = u''

    @abstractmethod
    def scores(self, game_players, non_players):
        """
        Returns a dict, indexed by player key, of scores.

        game_players is a QuerySet of GamePlayers.
        non_players is a QuerySet of RoundPlayers who were present but agreed
            not to play.
        """
        raise NotImplementedError

    def __str__(self):
        ret = self.name
        return ret


class RScoringBest(RoundScoringSystem):
    """
    Take the best of any game scores for that round.

    non_player_score is the points that players get for sitting out a round.
    if non_player_score_once is set, non_player_score can only be scored
     once per player, regardless of the number of rounds they sit out.
    """
    def __init__(self, non_player_score=0.0, non_player_score_once=False):
        self.non_player_score = non_player_score
        self.non_player_score_once = non_player_score_once
        self.name = _(u'Best game counts')
        if non_player_score > 0.0:
            if non_player_score_once:
                once_str = " once"
            else:
                once_str = ""
            self.name = _('Best game counts. Sitters get %(points)d%(once)s') % {'points': non_player_score,
                                                                                 'once': once_str}

    def scores(self, game_players, non_players):
        """
        Returns a dict, indexed by player key, of scores.

        If any player played multiple games, take the best game score and flag the rest as dropped.
        Otherwise, just take their game score.
        game_players is a QuerySet of GamePlayers.
        non_players is a QuerySet of RoundPlayers who were present but agreed
            not to play.
        """
        retval = {}
        # for each player who played any of the specified games
        for p in Player.objects.filter(gameplayer__in=game_players).distinct():
            # Find just their games
            player_games = game_players.filter(player=p)
            # Find the highest score
            best = None
            for gp in player_games:
                if not best:
                    best = gp
                elif gp.score > best.score:
                    best.score_dropped = True
                    best.save(update_fields=['score_dropped'])
                    best = gp
                else:
                    gp.score_dropped = True
                    gp.save(update_fields=['score_dropped'])
            best.score_dropped = False
            best.save(update_fields=['score_dropped'])
            retval[p] = best.score
        # Give the appropriate points to anyone who agreed to sit out
        for rp in non_players:
            if self.non_player_score_once:
                # If the "sitting out" bonus is only allowed once and they've sat out multiple rounds, they get zero
                bonus_already_given = False
                for r in rp.the_round.tournament.round_set.all():
                    if r == rp.the_round:
                        break
                    rps = RoundPlayer.objects.filter(the_round=r).filter(player=rp.player)
                    gps = GamePlayer.objects.filter(game__the_round=r).distinct().filter(player=rp.player)
                    if rps.exists() and not gps.exists():
                        # Player also didn't play in this earlier round
                        bonus_already_given = True
                        break
                if bonus_already_given:
                    retval[rp.player] = 0.0
                    continue
            retval[rp.player] = self.non_player_score
        return retval

    def __str__(self):
        ret = 'Best game score in each round counts'
        if self.non_player_score > 0.0:
            ret += '. Sitting out scores %.2f' % self.non_player_score
        if self.non_player_score_once:
            ret += ' once only'
        return ret


class RScoringAll(RoundScoringSystem):
    """
    Total all the Player's game scores for that round.
    """
    def __init__(self):
        self.name = _(u'Add all game scores')

    def scores(self, game_players, non_players):
        """
        Returns a dict, indexed by player key, of scores.

        If any player played multiple games, sum all game scores.
        Otherwise, just take their game score.
        game_players is a QuerySet of GamePlayers.
        non_players is a QuerySet of RoundPlayers who were present but agreed
            not to play.
        """
        retval = {}
        # for each player who played any of the specified games
        for p in Player.objects.filter(gameplayer__in=game_players).distinct():
            # Find just their games
            player_games = game_players.filter(player=p)
            # Add all game scores
            retval[p] = sum(gp.score for gp in player_games)
        # Give zero to anyone who didn't play
        for rp in non_players:
            retval[rp.player] = 0.0
        return retval


# All the round scoring systems we support
R_SCORING_SYSTEMS = [
    RScoringBest(),
    RScoringBest(4005.0),
    RScoringBest(4005.0, True),
    RScoringAll(),
]


class TournamentScoringSystem(ABC):
    """
    A scoring system for a Tournament.

    Provides a method to calculate a score for each player of tournament.
    """
    MAX_NAME_LENGTH=50
    name = u''

    @abstractmethod
    def scores(self, round_players):
        """
        Returns a dict, indexed by player key, of tournament scores

        Returns the tournament scores. Where Games and Rounds are complete,
        this is the final score. Where Games and Rounds are still in progress,
        this is the "if all games finished now" scores.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def uses_round_scores(self):
        """
        True if the scoring system combines Round scores, False if it uses Game scores directly.
        """
        raise NotImplementedError

    def __str__(self):
        ret = self.name
        return ret


class TScoringSum(TournamentScoringSystem):
    """
    Just add up the best N round scores.
    """
    def __init__(self, name, scored_rounds):
        self.name = name
        self.scored_rounds = scored_rounds

    uses_round_scores = True

    def scores(self, round_players):
        """
        Returns a dict, indexed by player key, of tournament scores

        If a player played more than N rounds, sum the best N round scores and flag the rest as dropped.
        Otherwise, sum all their round scores.
        """
        t_scores = {}
        # for each player who played any of the specified rounds
        for p in Player.objects.filter(roundplayer__in=round_players).distinct():
            # Find just their rounds, sort by score, descending
            rps = round_players.filter(player=p).order_by('-score')
            # Add up the first N
            t_scores[p] = 0.0
            for n, rp in enumerate(rps):
                if n < self.scored_rounds:
                    t_scores[p] += rp.score
                    rp.score_dropped = False
                    rp.save(update_fields=['score_dropped'])
                else:
                    rp.score_dropped = True
                    rp.save(update_fields=['score_dropped'])
        return t_scores


class TScoringSumGames(TournamentScoringSystem):
    """
    Just add up the best N Game scores regardless of the round(s) in which they were played.

    Optionally if a player played more than that number of Games, add the average of the scores
    of the remaining Games, multiplied by some factor.
    """
    def __init__(self, name, scored_games, residual_multiplier=0.0):
        self.name = name
        self.scored_games = scored_games
        self.residual_multiplier = residual_multiplier

    uses_round_scores = False

    def _flag_included_score(self, gp, fraction=1.0):
        """
        Store that this Game score counts toward the Round score.

        Update the RoundPlayer to note that the specified Game
        score contributes towards the overall score (and therefore
        to the Round score, which itself contributes)
        """
        rp = gp.roundplayer()
        rp.score += gp.score * fraction
        rp.score_dropped = False
        rp.save(update_fields=['score', 'score_dropped'])

    def scores(self, round_players):
        """
        Returns a dict, indexed by player key, of tournament scores

        If a player played fewer than N or exactly N games, sum all their game scores.
        Otherwise, sum their best N game scores and add the average of the remainder
        multiplied by self.residual_multiplier.
        Also updates all Round scores to reflect which games count towards the tournament score.
        """
        t_scores = {}
        # for each player who played any of the specified rounds
        for p in Player.objects.filter(roundplayer__in=round_players).distinct():
            # Find just the rounds they played
            rps = round_players.filter(player=p)
            rounds = []
            for rp in rps:
                rp.score = 0.0
                if self.residual_multiplier == 0.0:
                    # Assume the round scores is dropped unless we find out otherwise
                    rp.score_dropped = True
                rp.save(update_fields=['score', 'score_dropped'])
                rounds.append(rp.the_round)
            player_scores = GamePlayer.objects.filter(player=p,
                                                      game__the_round__in=rounds).order_by('score')
            t_scores[p] = 0
            if len(player_scores) <= self.scored_games:
                # All games count for this player
                for gp in player_scores:
                    t_scores[p] += gp.score
                    self._flag_included_score(gp)
            else:
                player_scores = list(player_scores)
                # Add up the best N Game scores and flag those scores as not dropped
                for _ in range(self.scored_games):
                    gp = player_scores.pop()
                    t_scores[p] += gp.score
                    self._flag_included_score(gp)
                    if self.residual_multiplier == 0.0:
                        # It's possible that a player's score for a Game in-progress
                        # has dropped below an earlier score that was previously dropped
                        # so we have to explicitly flag this score as not dropped
                        gp.score_dropped = False
                        gp.save(update_fields=['score_dropped'])
                if (self.residual_multiplier != 0.0) and len(player_scores):
                    # How much does each additional score contribute ?
                    bonus_factor = self.residual_multiplier / len(player_scores)
                # Then go through any remaining Game scores
                for gp in player_scores:
                    if self.residual_multiplier == 0.0:
                        # This score doesn't contribute
                        gp.score_dropped = True
                        gp.save(update_fields=['score_dropped'])
                        # If every Game in this Round is dropped, score the Round as the sum,
                        # and dropped, to keep us consistent with other scoring systems
                        rp = gp.roundplayer()
                        if rp.score_dropped:
                            rp.score += gp.score
                            rp.save(update_fields=['score'])
                    else:
                        t_scores[p] += gp.score * bonus_factor
                        self._flag_included_score(gp, fraction=bonus_factor)
        # The problem is that we go up from Game, to Round, to Tournament,
        # but now we want to go back to set the Round scores.
        # I guess we need to set them here and have a NOP RoundScoringSystem.
        # There's still the issue of what the RoundScoringSystem will report,
        # but maybe that doesn't matter - the calculation will be done before we ever use the round scores
        return t_scores


# All the tournament scoring systems we support
T_SCORING_SYSTEMS = [
    TScoringSum(_('Sum best 2 rounds'), 2),
    TScoringSum(_('Sum best 3 rounds'), 3),
    TScoringSum(_('Sum best 4 rounds'), 4),
    TScoringSumGames(_('Sum best 3 games in any rounds'), 3),
    TScoringSumGames(_('Sum best 4 games in any rounds'), 4),
    TScoringSumGames(_('Best single game result'), 1),
    TScoringSumGames(_('Sum best 2 games plus half the average of the rest'), 2, 0.5),
]

# Special "name" used to not calculate scores
# Used for Round scoring when rounds are irrelevant
NO_SCORING_SYSTEM_STR = _("None")

def find_scoring_system(name, the_list):
    """
    Searches through the_list for a scoring system with the specified name.

    Returns the ScoringSystem object.
    Can raise InvalidScoringSystem.
    """
    if name == NO_SCORING_SYSTEM_STR:
        return None
    for s in the_list:
        # There shouldn't be any abstract systems in here, but just in case...
        if (s.name == name) and not inspect.isabstract(s):
            return s
    raise InvalidScoringSystem(name)


def find_game_scoring_system(name):
    """
    Searches for a scoring system with the given name.

    Returns the GameScoringSystem object.
    Can raise InvalidScoringSystem.
    """
    return find_scoring_system(name, G_SCORING_SYSTEMS)


def find_round_scoring_system(name):
    """
    Searches for a scoring system with the given name.

    Returns the RoundScoringSystem object.
    Can raise InvalidScoringSystem.
    """
    return find_scoring_system(name, R_SCORING_SYSTEMS)


def find_tournament_scoring_system(name):
    """
    Searches for a scoring system with the given name.

    Returns the TournamentScoringSystem object.
    Can raise InvalidScoringSystem.
    """
    return find_scoring_system(name, T_SCORING_SYSTEMS)


def get_scoring_systems(systems, include_none=False):
    """
    Convert a list of scoring systems to a list of choices.

    Returns a list of two-tuples, suitable for use in a
    Django CharField.choices parameter.
    """
    sys_list = []
    if include_none:
        sys_list.append((NO_SCORING_SYSTEM_STR, NO_SCORING_SYSTEM_STR))
    sys_list += sorted([(s.name, s.name) for s in systems if not inspect.isabstract(s)])
    return sys_list


def validate_weight(value):
    """
    No longer used. Retained for migrations.
    """
    raise AssertionError("This function should no longer be used")


def validate_game_name(value):
    """
    Checks for a valid Game name

    Game names cannot contain spaces or '/' because they are used in URLs.
    """
    VALID_CHARS = set(string.ascii_letters + string.digits + "-._~:[]@!$'()*,;%=")
    if not set(value) <= VALID_CHARS:
        raise ValidationError(_(u'Game names cannot contain "%(chars)s"'),
                              params={'chars': ''.join(set(value) - VALID_CHARS)})


def validate_vote_count(value):
    """
    Checks for a valid vote count
    """
    if (value < 0) or (value > 7):
        raise ValidationError(_('%(value)d is not a valid vote count'),
                              params={'value': value})


def validate_bid(value):
    """
    No longer used. Retained for migrations.
    """
    raise AssertionError("This function should no longer be used")


def validate_tournament_scoring_system(value):
    """
    Validator for Tournament.tournament_scoring_system
    """
    try:
        system = find_tournament_scoring_system(value)
    except InvalidScoringSystem:
        raise ValidationError(_("%{value} is not a valid tournament scoring system"),
                              params={'value': value})


def validate_round_scoring_system(value):
    """
    Validator for Tournament.round_scoring_system
    """
    try:
        system = find_round_scoring_system(value)
    except InvalidScoringSystem:
        raise ValidationError(_("%{value} is not a valid round scoring system"),
                              params={'value': value})


def validate_game_scoring_system(value):
    """
    Validator for Round.scoring_system.
    """
    try:
        system = find_game_scoring_system(value)
    except InvalidScoringSystem:
        raise ValidationError(_("%{value} is not a valid game scoring system"),
                              params={'value': value})


def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # We expect instance to be a GameImage
    game = instance.game
    tournament = game.the_round.tournament
    return Path('games', tournament.name, str(tournament.start_date), game.name, filename)


class Award(models.Model):
    """
    An award for some notable achievement at a Tournament
    """

    MAX_NAME_LENGTH = 40
    MAX_DESCRIPTION_LENGTH = 200

    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    description = models.CharField(max_length=MAX_DESCRIPTION_LENGTH)
    power = models.ForeignKey(GreatPower,
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE,
                              help_text=_(u'Set if this award is associated with a specific power (e.g. "Best Italy")'))

    class Meta:
        ordering = ['name']

    def __str__(self):
        return _(f'{self.name}')


class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
    # Flag value to use for players who are excluded from the rankings
    UNRANKED = 999999

    MAX_NAME_LENGTH = 60

    name = models.CharField(max_length=MAX_NAME_LENGTH,
                            help_text='Year will be appended based on start date')
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=300, blank=True)
    # How do we combine round scores to get an overall player tournament score ?
    # This is the name of a TournamentScoringSystem object
    tournament_scoring_system = models.CharField(validators=[validate_tournament_scoring_system],
                                                 max_length=TournamentScoringSystem.MAX_NAME_LENGTH,
                                                 choices=get_scoring_systems(T_SCORING_SYSTEMS),
                                                 help_text=_(u'How to combine round scores into a tournament score'))
    handicaps = models.BooleanField(default=False,
                                    help_text=_('Check to give each TournamentPlayer a predetermined score bonus'))
    # How do we combine game scores to get an overall player score for a round ?
    # This is the name of a RoundScoringSystem object
    round_scoring_system = models.CharField(validators=[validate_round_scoring_system],
                                            max_length=RoundScoringSystem.MAX_NAME_LENGTH,
                                            choices=get_scoring_systems(R_SCORING_SYSTEMS, include_none=True),
                                            help_text=_(u'How to combine game scores into a round score'))
    draw_secrecy = models.CharField(max_length=1,
                                    verbose_name=_(u'What players are told about failed draw votes'),
                                    choices=DrawSecrecy.choices,
                                    default=DrawSecrecy.SECRET)
    is_published = models.BooleanField(default=False,
                                       help_text=_(u'Whether the tournament is visible to all site visitors'))
    managers = models.ManyToManyField(User,
                                      help_text=_(u'Which users can modify the tournament,<br> and see it while it is unpublished.<br>'))
    wdd_tournament_id = models.PositiveIntegerField(validators=[validate_wdd_tournament_id],
                                                    verbose_name=_("This tournament's id in the WDD"),
                                                    blank=True,
                                                    null=True,
                                                    help_text=_('Add this after the tournament is complete and results have been uploaded to the WDD'))
    seed_games = models.BooleanField(default=True,
                                     help_text=_('Check to let the software seed players to games'))
    power_assignment = models.CharField(max_length=1,
                                        verbose_name=_('How powers are assigned'),
                                        choices=PowerAssignMethods.choices,
                                        default=PowerAssignMethods.AUTO)
    editable = models.BooleanField(default=True,
                                   help_text=_('Uncheck to disallow any further changes to the tournament'))
    best_country_criterion = models.CharField(max_length=1,
                                              verbose_name=_(u'How Best Country awards are determined'),
                                              choices=BestCountryCriteria.choices,
                                              default=BestCountryCriteria.SCORE)
    format = models.CharField(max_length=1,
                              choices=Formats.choices,
                              default=Formats.FTF)
    no_email = models.BooleanField(default=False,
                                   help_text=_('Check to only generate email to tournament managers'))
    delay_game_url_publication = models.BooleanField(default=False,
                                                     verbose_name=_('Delay publishing game URL'),
                                                     help_text=_('Check to keep game URL secret until after the tournament completes'))
    awards = models.ManyToManyField(Award,
                                    help_text=_('Which achievements may be recognised.'))
    discord_url = models.URLField(verbose_name=_('Discord webhook URL'),
                                  blank=True,
                                  null=True,
                                  help_text=_('Board calls will be posted here'))

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(check=Q(draw_secrecy__in=DrawSecrecy.values),
                                   name='%(class)s_draw_secrecy_valid'),
            models.CheckConstraint(check=Q(power_assignment__in=PowerAssignMethods.values),
                                   name='%(class)s_power_assignment_valid'),
            models.CheckConstraint(check=Q(best_country_criterion__in=BestCountryCriteria.values),
                                   name='%(class)s_best_country_criterion_valid'),
            models.CheckConstraint(check=Q(format__in=Formats.values),
                                   name='%(class)s_format_valid'),
            models.CheckConstraint(check=Q(end_date__gte=F('start_date')),
                                   name='%(class)s_starts_before_end'),
            models.UniqueConstraint(fields=['name', 'start_date'],
                                    name='unique_name_date'),
        ]

    def powers_assigned_from_prefs(self):
        """
        Returns True if power_assignment is PREFERENCES.

        Intended for use in template code.
        """
        return self.power_assignment == PowerAssignMethods.PREFERENCES

    def is_virtual(self):
        """
        Returns True if the Tournament is online,

        False if it is truly face-to-face.
        """
        return self.format == Formats.VFTF

    def show_game_urls(self):
        """
        Return a boolean indicating whether Game external_url should be displayed.
        """
        if self.delay_game_url_publication:
            # Wait until 24 hours after the end of the last Round
            # (we ignore timezone issues - the delay doesn't have to be precise)
            return (date.today() > self.end_date + timedelta(hours=24))
        return True

    def tournament_scoring_system_obj(self):
        """
        Return the TournamentScoringSystem object for the Tournament.

        Can raise InvalidScoringSystem.
        """
        # Find the scoring system to combine round scores into a tournament score
        return find_tournament_scoring_system(self.tournament_scoring_system)

    def round_scoring_system_obj(self):
        """
        Return the RoundScoringSystem object for the Tournament.

        Can raise InvalidScoringSystem.
        """
        # Find the scoring system to combine game scores into a round score
        return find_round_scoring_system(self.round_scoring_system)

    def non_power_awards(self):
        """
        Returns a QuerySet of all awards other than "Best Country" awards.
        """
        return self.awards.filter(power=None)

    def award_number(self, award):
        """
        Returns the number (1..n) for the specified (non-best country) award at the tournament
        """
        assert award.power is None
        for i, a in enumerate(self.awards.filter(power=None), 1):
            if a == award:
                return i
        raise AssertionError(f'award {award} not found in {tournament}')

    def _calculated_scores(self):
        """
        Calculates the scores for everyone registered for the tournament.

        Return a dict, keyed by player, of floats.
        """
        system = self.tournament_scoring_system_obj()
        t_scores = system.scores(RoundPlayer.objects.filter(the_round__tournament=self).distinct())
        # Now add in anyone who has yet to attend a round
        for tp in self.tournamentplayer_set.all():
            if tp.player not in t_scores:
                t_scores[tp.player] = 0.0
        return t_scores

    def scores_detail(self):
        """
        Returns the scores for everyone registered for the tournament.

        If the tournament is over, this will be the stored scores.
        If the tournament is ongoing, it will be the "if all games
            ended now" scores.
        Returns a dict, keyed by player, of float tournament scores.
        """
        t_scores = {}
        for tp in self.tournamentplayer_set.prefetch_related('player'):
            t_scores[tp.player] = tp.score
        return t_scores

    def positions_and_scores(self):
        """
        Returns the positions and scores of everyone registered.

        Returns a dict, keyed by player, of 2-tuples containing integer rankings
          (1 for first place, etc) and float tournament scores.
          Players who are flagged as unranked in the tournament get the special
          place UNRANKED.
        """
        result = {}
        t_scores = self.scores_detail()
        # First, deal with any unranked players
        for tp in self.tournamentplayer_set.filter(unranked=True).prefetch_related('player'):
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
        return result

    def winner(self):
        """
        Return the player who won, or None if the tournament isn't yet finished
        """
        if self.is_finished():
            # TODO This assumes no tie
            return self.tournamentplayer_set.filter(unranked=False).order_by('-score').first().player
        return None

    def update_scores(self):
        """
        Recalculate the scores for the Tournament and store them in the TournamentPlayers.

        If the Tournament has now ended, add Best Country awards to
        the appropriate TournamentPlayers.
        """
        scores = self._calculated_scores()
        finished = self.is_finished()
        add_handicap = finished and self.handicaps
        for tp in self.tournamentplayer_set.prefetch_related('player'):
            tp.score = scores[tp.player]
            # Handicaps, if any, get added after the tournament is complete
            # but only if the player actually played
            if add_handicap and tp.roundplayers().exists():
                tp.score += tp.handicap
            tp.save(update_fields=['score'])
        if finished:
            # Hand out Best Country awards
            for power, gp_list in self.best_countries().items():
                for award in self.awards.filter(power=power).all():
                    for gp in gp_list:
                        # TODO What if this gets called more than once?
                        gp.tournamentplayer().awards.add(award)

    def round_numbered(self, number):
        """
        Return the Round (if any) of the tournament with the specified number.

        Can raise Round.DoesNotExist.
        """
        for r in self.round_set.all():
            if r.number() == int(number):
                return r
        # This allows this function to be used like QuerySet.get()
        raise Round.DoesNotExist

    def _sort_best_country_list(self, gp_list):
        """
        Order a list of results with one power by rank

        Take the list of (GamePlayer, score, dots, unranked) 4-tuples
        for one country, and sort it into best country ordering
        (highest to lowest).
        """
        # First sort criterion is always whether they're ranked or not
        # Second and third are score and centre count, with the order they're
        # used depending on how the Tournament is set up.
        # For ranking, we want regular order (so False is before True),
        # for the others, we want reverse order (highest first)
        if self.best_country_criterion == BestCountryCriteria.SCORE:
            gp_list.sort(key=itemgetter(1, 2), reverse=True)
        else:
            gp_list.sort(key=itemgetter(2, 1), reverse=True)
        gp_list.sort(key=itemgetter(3))

    def best_countries(self, whole_list=False):
        """
        Find the best result for every power

        Returns a dict, indexed by GreatPower.
        If whole_list is False, each dict is a list of the GamePlayers doing
        best with each GreatPower.
        If whole_list is True, each dict is a list of lists of the GreatPowers
        in order. Usually each list will contain a single GreatPower, but tied
        GamePlayers will be in the same list. For example, three GamePlayers
        A, B, and C with scores of 2.0, 5.0, and 2.0 respectively would be
        returned as [[B], [A, C]].
        """
        tuples = {}
        # We're going to need to "if all games ended now" score for every GamePlayer
        all_games = Game.objects.filter(the_round__tournament=self)
        # If no Games exist, return a dict of empty lists
        if not all_games:
            for power in GreatPower.objects.all():
                tuples[power] = []
            return tuples
        # Populate tuples. Dict, keyed by GreatPower,
        # of lists of (GamePlayer, score, dots, unranked) 4-tuples
        for gp in GamePlayer.objects.filter(game__the_round__tournament=self).prefetch_related('power', 'player', 'game', 'game__the_round__tournament'):
            if not gp.power:
                continue
            tuple_ = (gp, gp.score, gp.final_sc_count(), gp.tournamentplayer().unranked)
            tuples.setdefault(gp.power, []).append(tuple_)
        for power in tuples:
            self._sort_best_country_list(tuples[power])
        retval = {}
        if whole_list:
            for power in tuples:
                retval[power] = []
                # Store the score, dot count, and unranked for the last tuple accessed
                last = (None, None, None)
                while len(tuples[power]):
                    tup = tuples[power].pop(0)
                    nxt = tup[1:]
                    if nxt == last:
                        # Tie - append to current list
                        retval[power][-1].append(tup[0])
                    else:
                        # No tie - start a new list
                        retval[power].append([tup[0]])
                    last = nxt
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
        for tp in self.tournamentplayer_set.prefetch_related('player'):
            results += tp.player.background(mask=mask)
        if (mask & MASK_SERIES_WINS) != 0:
            # Add in background for any series this Tournament is in
            for s in self.series_set.all():
                for t in s.tournaments.all():
                    p = t.winner()
                    if not p:
                        continue
                    # Is the winner of that Tournament also playing in this one?
                    if self.tournamentplayer_set.filter(player=p).exists():
                        results.append(_('%(name)s won %(tourney)s')
                                       % {'name': p, 'tourney': t})
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def game_set(self):
        """
        Returns a queryset of all the Games in the Tournament
        """
        return Game.objects.filter(the_round__tournament=self)

    def current_round(self):
        """
        Returns the Round in progress, or None
        """
        # Rely on the default ordering
        rds = self.round_set.reverse().prefetch_related('game_set')
        for r in rds:
            if r.in_progress():
                return r
        # If no round is in progress, return the first unfinished round
        rds = rds.reverse()
        for r in rds:
            if not r.is_finished():
                return r
        return None

    def is_finished(self):
        """
        Determines whether the Tournament is complete.

        Returns True if the tournament has rounds, and they are all finished.
        Returns False otherwise.
        """
        rds = self.round_set.prefetch_related('game_set')
        # If there are no rounds, the tournament can't have started
        if not rds:
            return False
        # Look for any unfinished round
        for r in rds:
            if not r.is_finished():
                return False
        return True

    def in_progress(self):
        """
        Determines whether the Tournament has started but not yet finished.

        Returns True if the tournament has rounds, any is in progress,
        and not all have finished.
        Returns False otherwise.
        """
        r = self.current_round()
        if r is None:
            # Either no rounds, or all are finished
            return False
        if r.number() != 1:
            # First round is finished
            return True
        # r is round 1, so the tournament is in_progress if the round is
        return r.in_progress()

    def wdd_url(self):
        """URL for this tournament in the World Diplomacy Database, if known."""
        if self.wdd_tournament_id:
            return WDD_BASE_RESULTS_URL + 'tournament_class.php?id_tournament=%d' % self.wdd_tournament_id
        return u''

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('tournament_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        """
        Save the object to the database.

        Updates score attributes of any RoundPlayers and TournamentPlayers.
        """
        super().save(*args, **kwargs)

        # Change may affect the scoring
        try:
            validate_round_scoring_system(self.round_scoring_system)
            validate_tournament_scoring_system(self.tournament_scoring_system)
        except ValidationError:
            pass
        else:
            # Update all round scores. This will also call self.update_scores()
            for r in self.round_set.all():
                r.update_scores()

    def __str__(self):
        return '%s %d' % (self.name, self.start_date.year)


class DBNCoverage(models.Model):
    """
    A Diplomacy Broadcast Network broadcast for a Tournament.
    """
    MAX_DESC_LENGTH = 80

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    dbn_url = models.URLField(verbose_name=_('DBN URL on YouTube'))
    description = models.CharField(max_length=MAX_DESC_LENGTH)

    class Meta:
        verbose_name_plural = 'DBN coverages'

    def __str__(self):
        return '%s %s' % (self.tournament, self.description)


class SeriesSlugField(models.SlugField):
    """Auto-generate a slug from the model's name field """
    def pre_save(self, model_instance, add):
        slug = super().pre_save(model_instance, add)
        if not slug:
            slug = slugify(model_instance.name)
            setattr(model_instance, self.attname, slug)
        return slug


class Series(models.Model):
    """
    A series of Diplomacy tournaments, related in some way.

    For example each year's occurrance of an annual Tournament.
    """
    MAX_NAME_LENGTH = 60
    MAX_DESC_LENGTH = 2000

    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.CharField(max_length=MAX_DESC_LENGTH, null=True)
    tournaments = models.ManyToManyField(Tournament)
    slug = SeriesSlugField(null=False, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Series'

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('series_detail', args=[self.slug])

    def __str__(self):
        return '%s' % (self.name)


class TPPlayerField(models.CharField):
    """Default to match the Player if not provided """
    def pre_save(self, model_instance, add):
        val = super().pre_save(model_instance, add)
        # For new objects with no value set...
        if add and not val:
            # ... use the field of the same name from the Player
            val = getattr(model_instance.player, self.attname)
            setattr(model_instance, self.attname, val)
        return val


class TPUnrankedField(models.BooleanField):
    """Default from the Player and Tournament """
    def pre_save(self, model_instance, add):
        val = super().pre_save(model_instance, add)
        # For new objects with no value set...
        if add and not val:
            user = model_instance.player.user
            val = (user is not None) and user.tournament_set.filter(pk=model_instance.tournament.pk).exists()
            setattr(model_instance, self.attname, val)
        return val


class TournamentPlayer(models.Model):
    """
    One player in a tournament
    """
    MAX_BACKSTABBR_USERNAME_LENGTH=40

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    handicap = models.FloatField(default=0.0,
                                 help_text=_('Secret bonus score added after all games end. Only used if enabled for the Tournament'))
    unranked = TPUnrankedField(default=False,
                               verbose_name=_('Ineligible for awards'),
                               help_text=_('Set this to ignore this player when determining rankings'))
    uuid_str = models.CharField(max_length=36, blank=True)
    backstabbr_username = TPPlayerField(max_length=MAX_BACKSTABBR_USERNAME_LENGTH,
                                        blank=True,
                                        help_text=_('Username on the backstabbr website'))
    location = TPPlayerField(max_length=60, blank=True)
    paid = models.BooleanField(default=False,
                               help_text=_('Have they paid any registration fee?'))
    awards = models.ManyToManyField(Award, blank=True)

    class Meta:
        ordering = ['player']
        # Each player can only be in each tournament once
        constraints = [
            models.UniqueConstraint(fields=['player', 'tournament'],
                                    name='unique_player_tournament'),
        ]

    def score_is_final(self):
        """
        Returns True if the score attribute cannot now change

        Returns True if the score attribute represents the final score for the TournamentPlayer,
        False if it is the "if all games ended now" score.
        """
        t = self.tournament
        if t.is_finished():
            return True
        if t.handicaps:
            # Handicaps are added after all games end
            return False
        system = t.tournament_scoring_system_obj()
        if system.uses_round_scores:
            # If any round score for this player isn't final, this score also could change
            for rp in self.roundplayers():
                if not rp.score_is_final():
                    return False
        final_round = t.round_set.last()
        if not final_round.in_progress():
            # There are more rounds to go, so more opportunities to score
            return False
        if not system.uses_round_scores:
            # If the final Round is in progress, just check all their Games
            for gp in GamePlayer.objects.filter(player=self.player,
                                                game__the_round__tournament=t):
                if not gp.score_is_final():
                    return False
            return True
        # The final Round has started
        # They're either not playing in it
        # or they are playing and we already checked their round score,
        # and it can't change
        return True

    def position(self):
        """
        Where is the player (currently) ranked overall in the tournament?

        Returns Tournament.UNRANKED if self.unranked is True.
        """
        return self.tournament.positions_and_scores()[self.player][0]

    def roundplayers(self):
        """
        Returns a QuerySet for the corresponding RoundPlayers.
        """
        return self.player.roundplayer_set.filter(the_round__tournament=self.tournament).distinct()

    def rounds_played(self):
        """
        Returns the number of Rounds in which the Player actually played.
        """
        # I suspect there's some clever QuerySet stuff that could avoid the loop...
        return sum(1 for rp in self.roundplayers() if rp.gameplayers().exists())

    def create_preferences_from_string(self, the_string):
        """
        Create Preferences for the player as specified in the_string

        Given a string like "AEGFIRT", creates the corresponding Preferences
        in the database.
        Powers will be assigned a ranking from 1 for the first.
        Excluded powers will be unranked.
        Any pre-existing preferences for the player will be deleted.
        Raises InvalidPreferenceList if anything is wrong with the string.
        """
        # Convert the preference string to all uppercase
        # TODO This assumes English power abbreviations
        the_string = the_string.upper()
        try:
            validate_preference_string(the_string)
        except ValidationError as e:
            raise InvalidPreferenceList from e
        # Remove any existing preferences for this player
        self.preference_set.all().delete()
        to_power = {}
        for p in GreatPower.objects.all():
            to_power[p.abbreviation] = p
        # Go through the string, creating Preferences
        with transaction.atomic():
            for i, c in enumerate(the_string, 1):
                Preference.objects.create(player=self, power=to_power[c], ranking=i)

    def prefs_string(self):
        """
        Returns the Preferences for this TournamentPlayer as a string.

        More-or-less the inverse of create_preferences_from_string().
        """
        # TODO This returns the preference string in English
        ret = []
        for p in self.preference_set.all():
            ret.append(p.power.abbreviation)
        return ''.join(ret)

    def get_prefs_url(self):
        """
        Returns the absolute URL to update the preferences for this TournamentPlayer.
        """
        if not self.uuid_str:
            self._generate_uuid()
        if self.tournament.power_assignment == PowerAssignMethods.PREFERENCES:
            path = reverse('player_prefs',
                           args=[str(self.tournament.id), self.uuid_str])
        else:
            raise InvalidPowerAssignmentMethod(self.tournament.power_assignment)
        return 'https://%(host)s%(path)s' % {'host': settings.HOSTNAME,
                                             'path': path}

    def _generate_uuid(self):
        """
        Populates the uuid_str attribute.
        """
        self.uuid_str = str(uuid.uuid4())
        self.save(update_fields=['uuid_str'])

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('tournament_player_detail', args=[str(self.tournament.id),
                                                         str(self.id)])

    def __str__(self):
        return _('%(player)s at %(tourney)s') % {'tourney': self.tournament,
                                                 'player': self.player}

    def save(self, *args, **kwargs):
        """Store the TournamentPlayer in the database"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Update Player if things have changed
        if ((self.location != self.player.location) or
            (self.backstabbr_username != self.player.backstabbr_username)):
            self.player.location = self.location
            self.player.backstabbr_username = self.backstabbr_username
            self.player.save(update_fields=['location', 'backstabbr_username'])
        # Update background info when a player is added to the Tournament (only)
        if is_new:
            send_prefs_email(self)
            add_player_bg(self.player, include_wpe=False)


class SeederBias(models.Model):
    """
    Tell the game seeder to avoid putting two players in the same game.
    """
    player1 = models.ForeignKey(TournamentPlayer,
                                on_delete=models.CASCADE)
    player2 = models.ForeignKey(TournamentPlayer,
                                on_delete=models.CASCADE,
                                related_name='second_seederbias_set')

    class Meta:
        verbose_name_plural = 'Seeder biases'
        # Only one weighting per pair of players
        constraints = [
            models.UniqueConstraint(fields=['player1', 'player2'],
                                    name='unique_player_pair'),
        ]

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
        constraints = [
            # Each player can only have one ranking per power
            models.UniqueConstraint(fields=['player', 'power'],
                                    name='unique_player_power'),
            # Every ranking by a player must be unique
            models.UniqueConstraint(fields=['player', 'ranking'],
                                    name='unique_player_ranking'),
        ]
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
    # How do we score games in this round ?
    # This is the name of a GameScoringSystem object
    # There have been tournaments using multiple scoring systems, one per round
    scoring_system = models.CharField(validators=[validate_game_scoring_system],
                                      max_length=GameScoringSystem.MAX_NAME_LENGTH,
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
    enable_check_in = models.BooleanField(default=False,
                                          verbose_name=_(u'Enable self-check-ins'))
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['start']
        constraints = [
            models.CheckConstraint(check=Q(final_year__gte=FIRST_YEAR) | Q(final_year__isnull=True),
                                   name='%(class)s_final_year_valid'),
            models.CheckConstraint(check=(Q(earliest_end_time__isnull=True) & Q(latest_end_time__isnull=True))
                                          | Q(latest_end_time__gte=F('earliest_end_time')),
                                   name='%(class)s_end_times_valid'),
            models.UniqueConstraint(fields=['tournament', 'start'],
                                    name='unique_tournament_start'),
        ]

    def game_scoring_system_obj(self):
        """
        Return the GameScoringSystem for the Round.

        Can raise InvalidScoringSystem.
        """
        # Find the scoring system to score games in this Round
        return find_game_scoring_system(self.scoring_system)

    def scores(self):
        """
        Returns the scores for everyone who played in the round.

        Returns a dict, keyed by Player, of floats.
        """
        retval = {}
        for p in self.roundplayer_set.prefetch_related('player'):
            retval[p.player] = p.score
        return retval

    def update_scores(self):
        """
        Updates every RoundPlayer's score attribute.

        If the Round is ongoing, this will be the "if all games ended now" score.
        """
        system = self.tournament.round_scoring_system_obj()
        if system:
            # Identify any players who were checked in but didn't play
            gps = GamePlayer.objects.filter(game__the_round=self).distinct().prefetch_related('player')
            non_players = self.roundplayer_set.exclude(player__in=[gp.player for gp in gps])
            scores = system.scores(gps, non_players)
            for rp in self.roundplayer_set.prefetch_related('player'):
                rp.score = scores[rp.player]
                rp.save(update_fields=['score'])
        # That could change the Tournament scoring
        self.tournament.update_scores()

    def is_finished(self):
        """
        Is the Round complete?

        Returns True if the Round has games, and they have all finished.
        Returns False otherwise.
        """
        gs = self.game_set.all()
        if not gs:
            # Rounds with no games can't have started
            return False
        return not gs.filter(is_finished=False).exists()

    def in_progress(self):
        """
        Has the Round started but not yet finished?

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
        raise AssertionError("Round doesn't exist within its own tournament")

    def board_call_msg(self):
        """
        The Games in this Round, formatted as a message

        Returns a message listing the boards, players, and powers for the Round,
        suitable for sending by email or posting to discord.
        """
        text = 'Round %(number)d Board Call\n\n' % {'number': self.number()}
        return text + '\n'.join([g.board_call_msg() for g in self.game_set.all()])

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

    def save(self, *args, **kwargs):
        """
        Save the object to the database.

        Updates score attributes of any GamePlayers, RoundPlayers and TournamentPlayers.
        """
        super().save(*args, **kwargs)

        # Change may affect the scoring
        try:
            validate_round_scoring_system(self.tournament.round_scoring_system)
        except ValidationError:
            pass
        else:
            # Re-score all Games. This will call self.update_scores()
            for g in self.game_set.all():
                g.update_scores()

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('round_detail',
                       args=[str(self.tournament.id), str(self.number())])

    def __str__(self):
        return _(u'%(tournament)s round %(round)d') % {'tournament': self.tournament,
                                                       'round': self.number()}


class Game(models.Model):
    """
    A single game of Diplomacy, within a Round
    """
    MAX_NAME_LENGTH=20
    MAX_NOTES_LENGTH=120

    name = models.CharField(max_length=MAX_NAME_LENGTH,
                            validators=[validate_game_name],
                            help_text=_(u'Must be unique within the tournament. No spaces'))
    started_at = models.DateTimeField(default=timezone.now)
    is_finished = models.BooleanField(default=False)
    is_top_board = models.BooleanField(default=False)
    the_round = models.ForeignKey(Round, verbose_name=_(u'round'), on_delete=models.CASCADE)
    the_set = models.ForeignKey(GameSet, verbose_name=_(u'set'), on_delete=models.CASCADE)
    external_url = models.URLField(blank=True,
                                   verbose_name=_('Backstabbr URL'),
                                   help_text=_('Will be included in board call emails and game page'))
    notes = models.CharField(max_length=MAX_NOTES_LENGTH,
                             blank=True,
                             help_text=_('Will be included in board call emails and game page'))

    class Meta:
        ordering = ['name']

    def backstabbr_game(self):
        """
        Returns a backstabbr.Game for the Game, or None.
        """
        try:
            return backstabbr.Game(self.external_url)
        except backstabbr.InvalidGameUrl:
            # external_url may be something other than a backstabbr URL
            pass
        return None

    def webdiplomacy_game(self):
        """
        Returns a webdip.Game for the Game, or None.
        """
        try:
            return webdip.Game(self.external_url)
        except webdip.InvalidGameUrl:
            # external_url may be something other than a WebDiplomacy URL
            pass
        return None

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
        gps = self.gameplayer_set.prefetch_related('player', 'power')
        # Find current tournament positions (and scores)
        ranks = self.the_round.tournament.positions_and_scores()
        # Check for any GamePlayer that already has a power assigned
        # and find the interesting player positions
        for gp in gps:
            if gp.power:
                raise PowerAlreadyAssigned(str(gp) + ' is already assigned ' + str(gp.power))
            pos = ranks[gp.player][0]
            position_to_gps.setdefault(pos, []).append(gp)
        # Starting from the lowest rank, work through the whole list
        for pos in sorted(position_to_gps.keys(), reverse=True):
            # At each rank, order players randomly
            random.shuffle(position_to_gps[pos])
            for gp in position_to_gps[pos]:
                gp.set_power_from_prefs()

    def set_is_finished(self, year=None):
        """
        Set self.is_finished as appropriate

        Checks whether the Game has been soloed or drawn or the final_year has been reached.
        If so, sets is_finished to True.
        Should be called whenever CentreCounts for a year have been added.
        If year is not provided, uses the most recent year for the Game.
        """
        if year is None:
            year = self.final_year()
        if (self.soloer() is not None) or (self.passed_draw() is not None) or (year == self.the_round.final_year):
            self.is_finished = True
            self.save(update_fields=['is_finished'])
        # CentreCounts may have changed, so re-calculate scores
        self.update_scores()

    def create_or_update_sc_counts_from_ownerships(self, year):
        """
        Call this after adding SupplyCentreOwnerships to create/update CentreCounts

        Ensures that there is one CentreCount for each power for the
        specified year, and that the values match those determined by
        looking at the SupplyCentreOwnerships for that year.
        Sets self.is_finished if self.final_year has been reached or
        if the Game has been soloed.
        Can raise SCOwnershipsNotFound.
        """
        all_scos = self.supplycentreownership_set.filter(year=year)
        if not all_scos.exists():
            raise SCOwnershipsNotFound('%d of game %s' % (year, str(self)))
        with transaction.atomic():
            for p in GreatPower.objects.all():
                CentreCount.objects.update_or_create(power=p,
                                                     game=self,
                                                     year=year,
                                                     defaults={'count': all_scos.filter(owner=p).count()})
        self.set_is_finished(year)

    def compare_sc_counts_and_ownerships(self, year):
        """
        Check SupplyCentreOwnerships against CentreCounts

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
                retval.append(ngettext('Missing count of one centre for %(power)s',
                                       'Missing count of %(dots)d centres for %(power)s',
                                       sco_dots)
                              % {'dots': sco_dots,
                                 'power': p})
            else:
                if cc.count != sco_dots:
                    retval.append(ngettext('%(power)s owns one centre in %(year)d, but their centrecount is %(dots)d',
                                           '%(power)s owns %(sco_dots)d centres in %(year)d, but their centrecount is %(dots)d',
                                           sco_dots)
                                  % {'power': p,
                                     'year': year,
                                     'sco_dots': sco_dots,
                                     'dots': cc.count})
        return retval

    def _calc_scores(self):
        """
        Calculate the scores for the Game.

        Return value is a dict, indexed by power id, of scores.
        """
        system = self.the_round.game_scoring_system_obj()
        tgs = TournamentGameState(self.centrecount_set.all())
        return system.scores(tgs)

    def scores(self):
        """
        Returns the Game scores.

        Return value is a dict, indexed by power id, of scores.
        """
        # If we have GamePlayers, and they have assigned powers,
        # we can just retrieve the scores from them
        gps = self.gameplayer_set.prefetch_related('power')
        # Assume that if any GamePlayer has a power assigned, they all do
        if gps and gps.first().power:
            retval = {}
            for gp in gps:
                if gp.power:
                    retval[gp.power] = gp.score
            return retval
        return self._calc_scores()

    def update_scores(self):
        """
        Calculate Game scores and set the GamePlayer's score attributes

        Calculates the scores for the game using the specified ScoringSystem,
        and stores them in the GamePlayers.
        Then calls the equivalent function for the Round this Game is in.
        """
        scores = self._calc_scores()
        for gp in self.gameplayer_set.prefetch_related('power'):
            if gp.power:
                gp.score = scores[gp.power]
                gp.save(update_fields=['score'])
        self.the_round.update_scores()

    def positions(self):
        """
        Returns the positions (ranks) of all the powers.

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
        Returns whether the game Draws must Include All Survivors
        """
        return self.the_round.dias

    def years_played(self):
        """
        Returns a list of years for which there are SC counts for this game
        """
        scs = self.centrecount_set.all()
        return sorted(list({sc.year for sc in scs}))

    def background(self, mask=MASK_ALL_BG):
        """
        Returns a list of strings that give background for the game
        """
        gps = self.gameplayer_set.prefetch_related('power')
        results = []
        for gp in gps:
            results += gp.player.background(gp.power, mask=mask)
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
        Returns the last complete year of the game, whether the game is completed or ongoing
        """
        return self.centrecount_set.aggregate(Max('year'))['year__max']

    def soloer(self):
        """
        Returns either a GamePlayer if somebody soloed the game, or None
        """
        try:
            sc = self.centrecount_set.get(count__gte=WINNING_SCS)
        except CentreCount.DoesNotExist:
            return None
        return self.gameplayer_set.get(power=sc.power)

    def survivors(self, year=None):
        """
        Returns a list of the CentreCounts for the surviving powers.

        If a year is provided, it returns a list of the powers that survived
        that whole year.
        If a year is provided that is after the most recent year for which we have CentreCounts,
        the most recent list will be returned.
        If a year is provided for which there are no CentreCounts, an empty
        list will be returned.
        """
        final_year = self.final_year()
        if year is None:
            year = final_year
        if year > final_year:
            year = final_year
        final_scs = self.centrecount_set.filter(year=year)
        return [sc for sc in final_scs if sc.count > 0]

    def board_call_msg(self):
        """
        The Game name, players, and powers as a message

        Returns a message listing the game name, players, and powers,
        suitable for sending by email or posting to discord.
        """
        game_text = 'Board %(game)s:\n' % {'game': self.name}
        if self.external_url:
            game_text += ' ' + self.external_url + '\n'
        if self.notes:
            game_text += ' ' + self.notes + '\n'
        for gp in self.gameplayer_set.order_by('power').prefetch_related('player', 'power'):
            game_text += ' %(power)s: %(player)s' % {'power': gp.power or 'Power TBD',
                                                     'player': gp.player}
            if self.the_round.tournament.is_virtual():
                bs_un = gp.tournamentplayer().backstabbr_username
                if bs_un:
                    game_text += ' (%(backstabbr)s)\n' % {'backstabbr': bs_un}
                else:
                    game_text += '\n'
            else:
                game_text += '\n'
        return game_text

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
                game_player = self.gameplayer_set.get(power=power)
                winners.append(_(u'%(player)s (%(power)s)') % {'player': game_player.player,
                                                               'power': _(power.abbreviation)})
            return retval + ', '.join(winners)
        # Did a power reach 18 (or more) centres ?
        soloer = self.soloer()
        if soloer:
            return _(u'Game%(game)s won by %(player)s (%(power)s) with %(dots)d centres') % {'game': gn_str,
                                                                                             'player': soloer.player,
                                                                                             'power': _(soloer.power.abbreviation),
                                                                                             'dots': soloer.final_sc_count()}
        # TODO Did the game get to the fixed endpoint ?
        if self.is_finished:
            gps = self.gameplayer_set.all()
            toppers = self.board_toppers()
            first_str = ', '.join([_(u'%(player)s (%(power)s)') % {'player': gps.get(power=scs.power).player,
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
        Updates score attributes of any associated GamePlayers, RoundPlayers, and TournamentPlayers.
        """
        super().save(*args, **kwargs)

        # Auto-create 1900 SC counts (unless they already exist)
        # Auto-create SC Ownership (unless they already exist)
        with transaction.atomic():
            for power in GreatPower.objects.all():
                CentreCount.objects.update_or_create(power=power,
                                                     game=self,
                                                     year=FIRST_YEAR - 1,
                                                     defaults={'count': power.starting_centres})
                for sc in SupplyCentre.objects.filter(initial_owner=power):
                    SupplyCentreOwnership.objects.get_or_create(owner=power,
                                                                game=self,
                                                                year=FIRST_YEAR - 1,
                                                                sc=sc)

        # Auto-create S1901M image (if it doesn't exist)
        GameImage.objects.update_or_create(game=self,
                                           year=FIRST_YEAR,
                                           season=Seasons.SPRING,
                                           phase=Phases.MOVEMENT,
                                           defaults={'image': self.the_set.initial_image})

        # Change may affect the scoring
        try:
            validate_game_scoring_system(self.the_round.scoring_system)
        except ValidationError:
            pass
        else:
            self.update_scores()

    def get_absolute_url(self):
        """Returns the canonical URL for the object."""
        return reverse('game_detail',
                       args=[str(self.the_round.tournament.id), self.name])

    def __str__(self):
        return _('%(game)s at %(tourney)s') % {'game': self.name,
                                               'tourney': self.the_round.tournament}


class SupplyCentreOwnership(models.Model):
    """
    Used to track ownership of SupplyCentres through a Game

    Record of which GreatPower owned a given SupplyCentre
    at the end of a particular game year in a Game.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year_including_start])
    sc = models.ForeignKey(SupplyCentre, on_delete=models.CASCADE)
    owner = models.ForeignKey(GreatPower, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(year__gte=FIRST_YEAR-1),
                                   name='%(class)s_year_valid'),
            models.UniqueConstraint(fields=['sc', 'game', 'year'],
                                    name='unique_sc_game_year'),
        ]
        ordering = ['game', 'year']

    def __str__(self):
        return _("%(dot)s in %(game)s was owned by %(power)s at the end of %(year)d") % {'dot': self.sc,
                                                                                         'game': self.game,
                                                                                         'power': self.owner,
                                                                                         'year': self.year}


class DPPassedField(models.BooleanField):
    """If counts are recorded, derive passed from votes_in_favour and survivor count """
    def pre_save(self, model_instance, add):
        val = super().pre_save(model_instance, add)
        if model_instance.game.the_round.tournament.draw_secrecy == DrawSecrecy.COUNTS:
            survivors = len(model_instance.game.survivors(model_instance.year))
            if model_instance.votes_in_favour:
                # Votes must be unanimous
                val = (model_instance.votes_in_favour == survivors)
                setattr(model_instance, self.attname, val)
        return val


class DrawProposal(models.Model):
    """
    A single draw or concession proposal in a game
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    season = models.CharField(max_length=1, choices=Seasons.choices)
    passed = DPPassedField(blank=True, null=True)
    proposer = models.ForeignKey(GreatPower,
                                 blank=True,
                                 null=True,
                                 related_name='+',
                                 on_delete=models.CASCADE)
    drawing_powers = models.ManyToManyField(GreatPower, related_name='+')
    votes_in_favour = models.PositiveSmallIntegerField(blank=True,
                                                       null=True,
                                                       validators=[validate_vote_count])

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(year__gte=FIRST_YEAR),
                                   name='%(class)s_year_valid'),
            models.CheckConstraint(check=Q(season__in=Seasons.values),
                                   name='%(class)s_season_valid'),
            models.UniqueConstraint(fields=['game'],
                                    condition=models.Q(passed=True),
                                    name='only one passed'),
        ]

    def draw_size(self):
        """
        Returns the number of powers included in the DrawProposal.
        """
        return self.drawing_powers.count()

    def powers(self):
        """
        Returns a list of powers included in the draw proposal.
        """
        return list(self.drawing_powers.all())

    def power_is_part(self, power):
        """
        Returns a Boolean indicating whether the specified power is included.
        """
        return self.drawing_powers.filter(pk=power.pk).exists()

    def votes_against(self):
        """
        Returns the number of votes against the draw proposal.
        """
        # Get the most recent CentreCounts before the DrawProposal
        scs = self.game.centrecount_set.filter(year__lt=self.year)
        survivors = scs.filter(count__gt=0).count()
        try:
            return survivors - self.votes_in_favour
        except TypeError as e:
            raise TypeError(_('This DrawProposal only has pass/fail, not vote counts')) from e

    def clean(self):
        """
        Validate the object.

        Game must not yet have been won.
        Only living powers get to vote.
        Only one DrawProposal for a given Game can be successful.
        A successful DrawProposal for a Game cannot happen prior to any
        CentreCount.
        Dead powers cannot be included.
        If the Tournament has its draw_secrecy attribute set to SECRET,
        the passed attribute must be set.
        If the Tournament has its draw_secrecy attribute set to COUNTS,
        the votes_in_favour attribute must be set.
        """
        final_year = self.game.final_year()
        if self.game.soloer() and (final_year <= self.year):
            raise ValidationError(_(u'Game was soloed in %(year)d'),
                                  params={'year': final_year})
        # Figure out how many powers are still alive
        survivors = len(self.game.survivors(self.year))
        if self.votes_in_favour and (self.votes_in_favour > survivors):
            raise ValidationError(_(u'%(voters)d voters exceeds %(survivors)d surviving powers') % {'voters': self.votes_in_favour,
                                                                                                    'survivors': survivors})
        # Only one successful draw proposal
        if self.passed or (self.votes_in_favour == survivors):
            try:
                p = DrawProposal.objects.get(game=self.game,
                                             passed=True)
                if p != self:
                    raise ValidationError(_(u'Game already has a successful draw proposal'))
            except DrawProposal.DoesNotExist:
                pass
        # No successful proposal prior to the latest SC count
        if (self.passed or
            (self.votes_in_favour == survivors)) and (self.year <= final_year):
            raise ValidationError(_(u'Game already has a centre count for %(year)d'),
                                  params={'year': final_year})
        # No dead powers included
        # We can only use drawing_powers after the pk has been set
        if self.pk is not None:
            # If DIAS, all alive powers must be included
            dias = self.game.is_dias()
            # Get the most recent CentreCounts before the DrawProposal
            scs = self.game.centrecount_set.filter(year__lt=self.year)
            # We will always have at least the 1900 CentreCounts, and DrawProposal.year must be >= 1901
            scs = scs.filter(year=scs.last().year)
            for sc in scs:
                if self.drawing_powers.filter(pk=sc.power.pk).exists():
                    if sc.count == 0:
                        raise ValidationError(_(u'Dead power %(power)s included in proposal'),
                                              params={'power': sc.power})
                else:
                    if dias and sc.count > 0:
                        raise ValidationError(_(u'Missing alive power %(power)s in DIAS game'),
                                              params={'power': sc.power})
        # Ensure that either passed or votes_in_favour, as appropriate, are set
        if self.game.the_round.tournament.draw_secrecy == DrawSecrecy.SECRET:
            if self.passed is None:
                raise ValidationError(_('Passed needs a value'))
        elif self.game.the_round.tournament.draw_secrecy == DrawSecrecy.COUNTS:
            if self.votes_in_favour is None:
                raise ValidationError(_('Votes_in_favour needs a value'))
        else:
            raise AssertionError('Tournament draw secrecy has an unexpected value %c' % self.game.the_round.tournament.draw_secrecy)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Does this complete the game ?
        if self.passed:
            self.game.is_finished = True
            self.game.save(update_fields=['is_finished'])

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
    standby = models.BooleanField(default=False,
                                  help_text=_('check if the player would prefer not to play this round'))
    score = models.FloatField(default=0.0)
    score_dropped = models.BooleanField(default=False,
                                        help_text=_('Set if this score does not contribute towards the tournament score'))
    game_count = models.PositiveIntegerField(default=1,
                                             help_text=_('number of games to play this round'))
    sandboxer = models.BooleanField(default=False,
                                    help_text=_('set if the player is willing to record a game this round'))

    class Meta:
        ordering = ['player', 'the_round__start']
        constraints = [
            models.UniqueConstraint(fields=['player', 'the_round'],
                                    name='unique_player_round'),
        ]

    def score_is_final(self):
        """
        Can self.score change?

        Returns True if the score attribute represents the final score for the RoundPlayer,
        False if it is the "if all games ended now" score.
        """
        if (self.score > 0.0) and not self.the_round.tournament.tournament_scoring_system_obj().uses_round_scores:
            # Any later rounds may change the score for this round
            return self.tournamentplayer().score_is_final()
        if self.the_round.is_finished():
            return True
        # If any of this player's game scores aren't final, the round score isn't final
        for gp in self.gameplayers():
            if not gp.score_is_final():
                return False
        return True

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

    def delete(self, *args, **kwargs):
        ret = super().delete(*args, **kwargs)
        # Force a recalculation of scores, if necessary
        if self.score != 0.0:
            self.the_round.update_scores()
        return ret

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
    score = models.FloatField(default=0.0)
    score_dropped = models.BooleanField(default=False,
                                        help_text=_('Set if this score does not contribute towards the round score'))
    after_action_report = models.TextField(blank=True,
                                           help_text=_("This player's account of the game"))

    class Meta:
        ordering = ['game', 'power']
        constraints = [
            models.UniqueConstraint(fields=['player', 'game'],
                                    name='unique_player_game'),
            models.UniqueConstraint(fields=['power', 'game'],
                                    name='unique_power_game'),
        ]

    def score_is_final(self):
        """
        Can self.score change?

        Returns True if the score attribute represents the final score for the GamePlayer,
        False if it is the "if the game ended now" score.
        """
        if self.game.is_finished:
            return True
        # Game is ongoing - is the player alive?
        if self.elimination_year():
            return not self.game.the_round.game_scoring_system_obj().dead_score_can_change
        return False

    def is_best_country(self):
        """
        Returns True if this GamePlayer is the best result for this power (so far)
        """
        # Check all the other players of this power in the tournament
        t = self.game.the_round.tournament
        gps = GamePlayer.objects.filter(power=self.power,
                                        game__the_round__tournament=t).prefetch_related('player')
        if self.tournamentplayer().unranked:
            # If there are ranked GamePlayers of the same power,
            # they will rank ahead of this GamePlayer.
            # If they're all unranked, fall through to compare scores/dots
            tps = t.tournamentplayer_set.filter(unranked=False)
            for gp in gps:
                if tps.filter(player=gp.player).exists():
                    return False
        if self.game.the_round.tournament.best_country_criterion == BestCountryCriteria.SCORE:
            gp = gps.order_by('-score').first()
            if gp.score > self.score:
                return False
            if (gp.score == self.score) and (gp.final_sc_count() > self.final_sc_count()):
                return False
        else:
            gp = sorted(gps, key=lambda gp: gp.final_sc_count(), reverse=True)[0]
            gp_dots = gp.final_sc_count()
            self_dots = self.final_sc_count()
            if gp_dots > self_dots:
                return False
            if (gp_dots == self_dots) and (gp.score > self.score):
                return False
        return True

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
        Returns the current Preferences for this player, if any, ordered highest-to-lowest.
        """
        return self.tournamentplayer().preference_set.all()

    def elimination_year(self):
        """
        Year in which the player was eliminated, or None.
        """
        sc = self.game.centrecount_set.filter(power=self.power).filter(count=0).order_by('year').first()
        if not sc:
            return None
        return sc.year

    def final_sc_count(self):
        """
        Number of SupplyCentres held at the end of the Game, or currently if the Game is still ongoing.
        """
        game = self.game
        final_year = game.final_year()
        return game.centrecount_set.filter(year__lte=final_year,
                                           power=self.power).last().count

    def set_power_from_prefs(self):
        """
        Set self.power to the preferred GreatPower still available

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
        self.save(update_fields=['power'])

    def result_str_long(self):
        """
        Wrapper for result_str with both parameters set to True, for use by template code.

        Returned string includes an HTML <a> link to the game details page,
        so use the safe filter.
        """
        return self.result_str(include_power=True, include_game_name=True)

    def result_str(self, include_power=False, include_game_name=False):
        """
        Return the result of the Game from this GamePlayer's perspective.

        If the Game is ongoing, this will be the result if the game ended now.
        Returned string includes an HTML <a> link to the game details page,
        if include_game_name=True.
        """
        if not self.power:
            return ''
        g = self.game
        cc_set = g.centrecount_set.all()
        power_cc_set = cc_set.filter(power=self.power)
        # Final CentreCount for this player in this game
        final_sc = power_cc_set.order_by('-year').first()
        if final_sc.count == 0:
            # We need to look back to find the first CentreCount with no dots
            final_sc = power_cc_set.filter(count=0).order_by('year').first()
            if include_power:
                gs = _('Eliminated as %(power)s in %(year)d') % {'year': final_sc.year,
                                                                 'power': _(self.power.name)}
            else:
                gs = _('Eliminated in %(year)d') % {'year': final_sc.year}
        else:
            # Final year of the game as a whole
            final_year = cc_set.order_by('-year').first().year
            # Was the game soloed ?
            soloer = g.soloer()
            if self == soloer:
                if include_power:
                    gs = ngettext('Solo as %(power)s with %(dots)d centre in %(year)d',
                                  'Solo as %(power)s with %(dots)d centres in %(year)d',
                                  final_sc.count) % {'year': final_year,
                                                     'power': _(self.power.name),
                                                     'dots': final_sc.count}
                else:
                    gs = ngettext('Solo with %(dots)d centre in %(year)d',
                                  'Solo with %(dots)d centres in %(year)d',
                                  final_sc.count) % {'year': final_year,
                                                     'dots': final_sc.count}
            elif soloer is not None:
                if include_power:
                    gs = ngettext('Loss as %(power)s with %(dots)d centre in %(year)d',
                                  'Loss as %(power)s with %(dots)d centres in %(year)d',
                                  final_sc.count) % {'year': final_sc.year,
                                                     'power': _(self.power.name),
                                                     'dots': final_sc.count}
                else:
                    gs = ngettext('Loss with %(dots)d centre in %(year)d',
                                  'Loss with %(dots)d centres in %(year)d',
                                  final_sc.count) % {'year': final_sc.year,
                                                     'dots': final_sc.count}
            else:
                # Did a draw vote pass ?
                res = g.passed_draw()
                if res:
                    if self.power in res.powers():
                        if include_power:
                            gs = ngettext('%(n)d-way draw as %(power)s with %(dots)d centre in %(year)d',
                                          '%(n)d-way draw as %(power)s with %(dots)d centres in %(year)d',
                                          final_sc.count) % {'n': res.draw_size(),
                                                             'power': _(self.power.name),
                                                             'dots': final_sc.count,
                                                             'year': final_year}
                        else:
                            gs = ngettext('%(n)d-way draw with %(dots)d centre in %(year)d',
                                          '%(n)d-way draw with %(dots)d centres in %(year)d',
                                          final_sc.count) % {'n': res.draw_size(),
                                                             'dots': final_sc.count,
                                                             'year': final_year}
                    else:
                        if include_power:
                            gs = ngettext('Loss as %(power)s with %(dots)d centre in %(year)d',
                                          'Loss as %(power)s with %(dots)d centres in %(year)d',
                                          final_sc.count) % {'year': final_sc.year,
                                                             'power': _(self.power.name),
                                                             'dots': final_sc.count}
                        else:
                            gs = ngettext('Loss with %(dots)d centre in %(year)d',
                                          'Loss with %(dots)d centres in %(year)d',
                                          final_sc.count) % {'year': final_sc.year,
                                                             'dots': final_sc.count}
                else:
                    # Game is either ongoing or reached a timed end
                    # Is this power topping the board?
                    final_sc_set = cc_set.filter(year=final_sc.year).order_by('-count')
                    topper_dots = final_sc_set.first().count
                    if final_sc.count == topper_dots:
                        topper_count = final_sc_set.filter(count=topper_dots).count()
                        topper_str = ngettext(' (board top)',
                                              ' (%(n)d-way tied board top)',
                                              topper_count) % {'n': topper_count}
                    else:
                        topper_str = ''
                    if include_power:
                        gs = ngettext('%(dots)d centre%(topper)s as %(power)s in %(year)d',
                                      '%(dots)d centres%(topper)s as %(power)s in %(year)d',
                                      final_sc.count) % {'year': final_sc.year,
                                                         'power': _(self.power.name),
                                                         'topper': topper_str,
                                                         'dots': final_sc.count}
                    else:
                        gs = ngettext('%(dots)d centre%(topper)s in %(year)d',
                                      '%(dots)d centres%(topper)s in %(year)d',
                                      final_sc.count) % {'year': final_sc.year,
                                                         'topper': topper_str,
                                                         'dots': final_sc.count}
        # game name and link
        if include_game_name:
            gs += _(' in <a href="%(url)s">%(game)s</a>') % {'game': g.name,
                                                             'url': g.get_absolute_url()}
            # Additional info
            if g.is_top_board:
                gs += _(' [Top Board]')
            if not g.is_finished:
                gs += _(' [Ongoing]')
        return gs

    def clean(self):
        """
        Validate the object.

        There must already be a corresponding TournamentPlayer.
        """
        # Player should already be in the tournament
        t = self.game.the_round.tournament
        if not self.player.tournamentplayer_set.filter(tournament=t).exists():
            raise ValidationError(_(u'Player is not yet in the tournament'))

    def __str__(self):
        if self.power:
            return _('%(player)s as %(power)s in %(game)s') % {'game': self.game,
                                                               'player': self.player,
                                                               'power': self.power}
        return _('%(player)s in %(game)s Power TBD') % {'game': self.game,
                                                        'player': self.player}

    def get_aar_url(self):
        """Returns the canonical URL for the object."""
        return reverse('aar', args=[str(self.game.the_round.tournament.id),
                                        self.game.name,
                                        self.player.id])


class GameImage(models.Model):
    """
    An image depicting a Game at a certain point.

    The year, season, and phase together indicate the phase that is about to
    be played.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(validators=[validate_year])
    season = models.CharField(max_length=1, choices=Seasons.choices, default=Seasons.SPRING)
    phase = models.CharField(max_length=1, choices=Phases.choices, default=Phases.MOVEMENT)
    image = models.ImageField(upload_to=game_image_location)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(year__gte=FIRST_YEAR),
                                   name='%(class)s_year_valid'),
            models.CheckConstraint(check=Q(season__in=Seasons.values),
                                   name='%(class)s_season_valid'),
            models.CheckConstraint(check=Q(phase__in=Phases.values),
                                   name='%(class)s_phase_valid'),
            models.UniqueConstraint(fields=['game', 'year', 'season', 'phase'],
                                    name='unique_game_year_season_phase'),
        ]
        ordering = ['game', 'year', '-season', 'phase']

    def turn_str(self):
        """
        Short string version of season/year/phase

        e.g. 'S1901M'
        """
        return u'%s%d%s' % (self.season, self.year, PHASE_STR[self.phase])

    def clean(self):
        """
        Validate the object.

        The phase attribute can only be set to ADJUSTMENTS when the season
        attribute is set to FALL.
        """
        if self.season == Seasons.SPRING and self.phase == Phases.ADJUSTMENTS:
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
        constraints = [
            models.CheckConstraint(check=Q(year__gte=FIRST_YEAR-1),
                                   name='%(class)s_year_valid'),
            models.CheckConstraint(check=Q(count__lte=TOTAL_SCS),
                                   name='%(class)s_count_valid'),
            models.UniqueConstraint(fields=['power', 'game', 'year'],
                                    name='unique_power_game_year'),
        ]
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
