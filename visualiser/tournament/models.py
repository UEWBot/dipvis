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

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Max, Min, Sum, Q
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.contrib.auth.models import User

from tournament.diplomacy import GameSet, GreatPower, SupplyCentre
from tournament.diplomacy import FIRST_YEAR, WINNING_SCS, TOTAL_SCS
from tournament.diplomacy import validate_year_including_start, validate_year
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.players import Player, MASK_ALL_BG, add_player_bg, position_str, MASK_ROUND_ENDPOINTS
from tournament.players import PlayerTournamentRanking, PlayerAward, PlayerGameResult
from tournament.players import validate_wdd_id, player_picture_location, TO_GAME_RESULT, LOSS

import urllib.request, random, os
from operator import attrgetter, itemgetter
from math import isclose

SPRING = 'S'
FALL = 'F'
SEASONS = (
    (SPRING, _('spring')),
    (FALL, _('fall')),
)
MOVEMENT = 'M'
RETREATS = 'R'
# Use X for adjustments to simplify sorting
ADJUSTMENTS = 'X'
PHASES = (
    (MOVEMENT, _('movement')),
    (RETREATS, _('retreats')),
    (ADJUSTMENTS, _('adjustments')),
)
phase_str = {
    MOVEMENT: 'M',
    RETREATS: 'R',
    ADJUSTMENTS: 'A',
}

# Power assignment methods
RANDOM = 'R'
FRENCH_METHOD = 'F'
POWER_ASSIGNS =  (
    (RANDOM, _('Random')),
    (FRENCH_METHOD, _('French method')),
)

# Draw secrecy levels
SECRET = 'S'
COUNTS = 'C'
DRAW_SECRECY = (
    (SECRET, _('Pass/Fail')),
    (COUNTS, _('Numbers for and against')),
)

# Mask values to choose which news strings to include
MASK_BOARD_TOP = 1<<0
MASK_GAINERS = 1<<1
MASK_LOSERS = 1<<2
MASK_DRAW_VOTES = 1<<3
MASK_ELIMINATIONS = 1<<4
MASK_ALL_NEWS = (1<<5)-1

class InvalidScoringSystem(Exception):
    pass

class InvalidYear(Exception):
    pass

class SCOwnershipsNotFound(Exception):
    pass

class RoundScoringSystem():
    """
    A scoring system for a Round.
    Provides a method to calculate a score for each player of one round.
    """
    name = u''
    # True for classes that provide building blocks rather than full scoring systems
    is_abstract = True

    def scores(self, game_players):
        """
        Takes the set of GamePlayer objects of interest.
        Returns a dict, indexed by player key, of scores.
        """
        return {}

class RScoringBest(RoundScoringSystem):
    """
    Take the best of any game scores for that round.
    """
    def __init__(self):
        self.is_abstract = False
        self.name = _(u'Best game counts')

    def scores(self, game_players):
        """
        If any player played multiple games, take the best game score.
        Otherwise, just take their game score.
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
            player_games = game_players.filter(player=p)
            # Find the highest score
            retval[p] = max(game_scores[g.game][g.power] for g in player_games)
        return retval

# All the round scoring systems we support
R_SCORING_SYSTEMS = [
    RScoringBest(),
]

class TournamentScoringSystem():
    """
    A scoring system for a Tournament.
    Provides a method to calculate a score for each player of tournament.
    """
    name = u''
    # True for classes that provide building blocks rather than full scoring systems
    is_abstract = True

    def scores(self, round_players):
        """
        Takes the set of RoundPlayer objects of interest.
        Combines the score attribute of ones for each player into an overall score for that player.
        Returns a dict, indexed by player key, of scores.
        """
        return {}

class TScoringSum(TournamentScoringSystem):
    """
    Just add up the best N round scores.
    """
    scored_rounds = 0

    def __init__(self, name, scored_rounds):
        self.is_abstract = False
        self.name = name
        self.scored_rounds = scored_rounds

    def scores(self, round_players):
        """
        If a player played more than N rounds, sum the best N round scores.
        Otherwise, sum all their round scores.
        Return a dict, indexed by player key, of scores.
        """
        retval = {}
        # Retrieve all the scores for all the rounds involved.
        # This will give us "if the round ended now" scores for in-progress round(s)
        round_scores = {}
        for r in Round.objects.filter(roundplayer__in=round_players).distinct():
            round_scores[r] = r.scores()
        # for each player who played any of the specified rounds
        for p in Player.objects.filter(roundplayer__in=round_players).distinct():
            if p in retval:
                continue
            score = 0
            # Find just their rounds
            player_rounds = round_players.filter(player=p)
            # Extract the scores into a sorted list, highest first
            player_scores = []
            for r in player_rounds:
                try:
                    player_scores.append(round_scores[r.the_round][r.player])
                except KeyError:
                    pass
            player_scores.sort(reverse=True)
            # Add up the first N
            retval[p] = sum(player_scores[:self.scored_rounds])
        return retval

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
        if not s.is_abstract and s.name == name:
            return s
    return None

def find_game_scoring_system(name):
    return find_scoring_system(name, G_SCORING_SYSTEMS)

def find_round_scoring_system(name):
    return find_scoring_system(name, R_SCORING_SYSTEMS)

def find_tournament_scoring_system(name):
    return find_scoring_system(name, T_SCORING_SYSTEMS)

def get_scoring_systems(systems):
    return sorted([(s.name, s.name) for s in systems if not s.is_abstract])

def validate_sc_count(value):
    """
    Checks for a valid SC count
    """
    if value < 0 or value > TOTAL_SCS:
        raise ValidationError(_(u'%(value)d is not a valid SC count'), params = {'value': value})

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
        raise VaidationError(_('%(value)d is not a valid vote count'), {'value': value})

def game_image_location(instance, filename):
    """
    Function that determines where to store the file.
    """
    # We expect instance to be a GameImage
    game = instance.game
    tournament = game.the_round.tournament
    directory = os.path.join(tournament.name, str(tournament.start_date), game.name)
    return os.path.join('games', directory, filename)

def add_local_player_bg(player):
    """
    Add background for the player from earlier tournaments in the system,
    unless they have already been added (e.g. because those results are
    in the WDD).
    """
    for t in Tournament.objects.all():
        # Not interested in ongoing tournaments
        if not t.is_finished():
            continue
        # Get the corresponding TournamentPlayer (if any)
        try:
            tp = t.tournamentplayer_set.filter(player=player).get()
        except TournamentPlayer.DoesNotExist:
            continue
        # Add a PlayerTournamentRanking
        i, created = PlayerTournamentRanking.objects.get_or_create(player=player,
                                                                   tournament=t.name,
                                                                   position=tp.position(),
                                                                   year=t.start_date.year)
        # Ensure that the date is set
        i.date = t.start_date
        i.save()
        # Add a PlayerAward for each best country
        for power, gps in t.best_countries().items():
            for gp in gps:
                if gp.player == player:
                    sc = gp.game.centrecount_set.filter(year=gp.game.final_year()).filter(power=power).get()
                    i, created = PlayerAward.objects.get_or_create(player=player,
                                                                   tournament = t.name,
                                                                   date=t.start_date,
                                                                   name=_('Best %(country)s') % {'country': power})
                    i.power = power
                    i.score = gp.score
                    i.final_sc_count = sc.count
                    i.save()
        # Also add PlayerGameResult for each board played
        for gp in GamePlayer.objects.filter(player=player).filter(game__the_round__tournament=t).distinct():
            pos = gp.game.positions()
            i,created = PlayerGameResult.objects.get_or_create(tournament_name=t.name,
                                                               game_name=gp.game.name,
                                                               player=player,
                                                               power=gp.power,
                                                               date = gp.game.the_round.start.date(),
                                                               position = pos[gp.power])
            # Set additional info
            i.score = gp.score
            i.year_eliminated = gp.elimination_year()
            i.final_sc_count = gp.game.centrecount_set.filter(power=gp.power).order_by('-year').first().count
            s = gp.game.soloer()
            d = gp.game.passed_draw()
            if s:
                if s == gp:
                    i.result = WIN
                else:
                    i.result = LOSS
            elif d:
                if d.power_is_part(gp.power):
                    i.result = TO_GAME_RESULT[d.draw_size()]
                else:
                    i.result = LOSS
            else:
                if i.year_eliminated:
                    i.result = LOSS
                else:
                    i.result = TO_GAME_RESULT[len(gp.game.survivors())]
            # TODO This is broken if there were replacement players, but so is scoring...
            i.position_equals = len([v for v in pos.values() if v == pos[gp.power]])
            i.save()

class Tournament(models.Model):
    """
    A Diplomacy tournament
    """
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
    is_published = models.BooleanField(default=False, help_text=_(u'Whether the tournament is visible to all site visitors'))
    managers = models.ManyToManyField(User, help_text=_(u'Which users can modify the tournament,<br/> and see it while it is unpublished.<br/>'))

    class Meta:
        ordering = ['-start_date']

    def scores(self, force_recalculation=False):
        """
        Returns the scores for everyone who played in the tournament.
        Dict, keyed by player, of floats.
        """
        # If the tournament is over, report the stored scores unless we're told to recalculate
        if self.is_finished() and not force_recalculation:
            retval = {}
            for p in self.tournamentplayer_set.all():
                retval[p.player] = p.score
            return retval

        # Find the scoring system to combine round scores into a tournament score
        system = find_tournament_scoring_system(self.tournament_scoring_system)
        if not system:
            raise InvalidScoringSystem(self.tournament_scoring_system)
        return system.scores(RoundPlayer.objects.filter(the_round__tournament=self).distinct())

    def positions_and_scores(self):
        """
        Returns the positions and scores of all the players.
        Dict, keyed by player, of 2-tuples containing integer rankings (1 for first place, etc) and float scores.
        """
        result = {}
        scores = self.scores()
        last_score = None
        for i,(k,v) in enumerate(sorted([(k,v) for k,v in scores.items()], key=itemgetter(1), reverse=True)):
            if v != last_score:
                place, last_score = i + 1, v
            result[k] = (place, v)
        return result

    def round_numbered(self, number):
        """
        Return the Round (if any) of the tournament with the specified number.
        """
        for r in self.round_set.all():
            if r.number() == int(number):
                return r
        # This allows this function to be used like QuerySet.get()
        raise Round.DoesNotExist

    def best_countries(self):
        """
        Returns a dict, indexed by GreatPower, of lists of the GamePlayers with the best scores for each country
        """
        retval = {}
        # Populate retval. Dict, keyed by GreatPower, of lists of GamePlayers
        for r in self.round_set.all():
            for g in r.game_set.all():
                for gp in g.gameplayer_set.all():
                    try:
                        retval[gp.power].append(gp)
                    except KeyError:
                        retval[gp.power] = [gp]
        for power in retval.keys():
            # Find the best score for this power in the whole tournament
            # First, sort by descending score
            retval[power].sort(key=attrgetter('score'), reverse=True)
            best = retval[power][0].score
            # Throw away all but the top scores
            retval[power] = [gp for gp in retval[power] if gp.score == best]
            # Do we need to resolve a tie ?
            if len(retval[power]) > 1:
                # Resolve the tie by comparing centrecounts
                best_dots = 0
                for gp in retval[power]:
                    sc = gp.game.centrecount_set.filter(year=gp.game.final_year()).filter(power=power).get()
                    best_dots = max([best_dots, sc.count])
                winners = [gp for gp in retval[power] if gp.game.centrecount_set.filter(year=gp.game.final_year()).filter(power=power).get().count == best_dots]
                retval[power] = winners
        return retval

    def background(self, mask=MASK_ALL_BG):
        """
        Returns a list of background strings for the tournament
        """
        players = Player.objects.filter(tournamentplayer__tournament = self).distinct()
        results = []
        for p in players:
            results += p.background(mask=mask)
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
        results.append(_('%(count)d players %(are)s registered to play in the tournament.') % {'count': self.tournamentplayer_set.count(),
                                                                                               'are': tense_str})
        if current_round:
            # Include who is leading the tournament
            include_leader = True
            # And which round is currently being played
            results.append(_(u'Round %(r_num)d of %(rounds)d is currently being played.') % {'r_num': current_round.number(),
                                                                                             'rounds': self.round_set.count()})
            # Get the news for the current round
            results += current_round.news()
        # If the tournament is over, just report the top three players, plus best countries
        elif self.is_finished():
            # TODO There are potentially ties here
            for scores_reported, p in enumerate(self.tournamentplayer_set.all().order_by('-score')[:3], 1):
                results.append(_(u'%(player)s came %(pos)s, with a score of %(score).2f.') % {'player': str(p.player),
                                                                                              'pos':  position_str(scores_reported),
                                                                                              'score':  p.score})
            # Add best countries
            for power, gps in self.best_countries().items():
                gp = gps[0]
                if len(gps) == 1:
                    sc = gp.game.centrecount_set.filter(year=gp.game.final_year()).filter(power=power).get()
                    results.append(_(u'%(player)s won Best %(country)s with %(dots)d centres and a score of %(score).2f in game %(game)s of round %(round)d.') % {'player': str(gp.player),
          'country': power.name,
          'dots': sc.count,
          'score': gp.score,
          'game': gp.game.name,
          'round': gp.game.the_round.number()})
                else:
                    # Tie for best power
                    winner_str = ', '.join([str(p.player) for p in gps])
                    results.append(_(u'Best %(country)s was jointly won by %(winner_str)s with %(dots)d centres and a score of %(score).2f.') % {'country': power.name,
                   'winner_str': winner_str,
                   'dots': gp.game.centrecount_set.filter(year=gp.game.final_year()).filter(power=power).get().count,
                   'score': gp.score})
        else:
            # which rounds have been played ?
            played_rounds = len([r for r in self.round_set.all() if r.is_finished()])
            if played_rounds == 0:
                results.append(_(u'Tournament has yet to start.'))
            else:
                if played_rounds == 1:
                    have_str = u'has'
                else:
                    have_str = u'have'
                results.append(_(u'%(r_num)d of %(rounds)d rounds %(have)s been played.') % {'r_num': played_rounds,
                                                                                             'rounds': self.round_set.count(),
                                                                                             'have': have_str})
                # Include who is leading the tournament
                include_leader = True
        if include_leader:
            the_scores = self.scores()
            if len(the_scores) > 0:
                max_score = max(the_scores.values())
                winners = [str(k) for k,v in the_scores.items() if v == max_score]
                player_str = ', '.join(winners)
                results.append(_(u'If the tournament ended now, the winning score would be %(score).2f for %(players)s.') % { 'score': max_score,
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
        rds = self.round_set.all()
        for r in rds:
            if not r.is_finished():
                return r
        return None

    def is_finished(self):
        rds = self.round_set.all()
        # If there are no rounds, the tournament can't have started
        if len(rds) == 0:
            return False
        # Look for any unfinished round
        for r in rds:
            if not r.is_finished():
                return False
        return True

    def get_absolute_url(self):
        return reverse('tournament_detail', args=[str(self.id)])

    def __str__(self):
        return self.name

class TournamentPlayer(models.Model):
    """
    One player in a tournament
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ['player']
        # Each player can only be in each tournament once
        unique_together = ('player', 'tournament')

    def position(self):
        """
        Where is the player (currently) ranked overall in the tournament?
        """
        return self.tournament.positions_and_scores()[self.player][0]

    def __str__(self):
        return u'%s %s %f' % (self.tournament, self.player, self.score)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(TournamentPlayer, self).save(*args, **kwargs)
        # Update background info when a player is added to the Tournament (only)
        if is_new:
            add_player_bg(self.player)
            add_local_player_bg(self.player)

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
    final_year = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_year])
    earliest_end_time = models.DateTimeField(blank=True, null=True)
    latest_end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['start']

    def scores(self, force_recalculation=False):
        """
        Returns the scores for everyone who played in the round.
        """
        # If the round is over, report the stored scores unless we're told to recalculate
        if self.is_finished() and not force_recalculation:
            retval = {}
            for p in self.roundplayer_set.all():
                retval[p.player] = p.score
            return retval

        # Find the scoring system to combine game scores into a round score
        system = find_round_scoring_system(self.tournament.round_scoring_system)
        if not system:
            raise InvalidScoringSystem(self.tournament.round_scoring_system)
        return system.scores(GamePlayer.objects.filter(game__the_round=self).distinct())

    def is_finished(self):
        gs = self.game_set.all()
        if len(gs) == 0:
            # Rounds with no games can't have started
            return False
        for g in gs:
            if not g.is_finished:
                return False
        return True

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
        Returns a news string detailing the person with the best score for the round.
        """
        the_scores = self.scores()
        if len(the_scores) == 0:
            return None
        max_score = max(the_scores.values())
        winners = [k for k,v in the_scores.items() if v == max_score]
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
        results.append(_('%(count)d players %(are)s registered to play in the round.') % {'count': self.roundplayer_set.count(),
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
        else:
            # Otherwise, add a count of completed games
            if done_games == 0:
                done_str = _(u'None')
            else:
                done_str = u'%d' % done_games
            results.append(_(u'%(done)s of the %(total_num)d games in round %(r_num)d have ended.') % {'done': done_str,
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
            results.append(_(u'Round %(round)d could end as early as %(time)s.') % {'round': self.number(),
                                                                                    'time': self.earliest_end_time.strftime("%H:%M")})
        if (mask & MASK_ROUND_ENDPOINTS) != 0 and self.latest_end_time:
            results.append(_(u'Round %(round)d could end as late as %(time)s.') % {'round': self.number(),
                                                                                   'time': self.latest_end_time.strftime("%H:%M")})
        if (mask & MASK_ROUND_ENDPOINTS) != 0 and self.final_year:
            results.append(_(u'Round %(round)d will end after playing year %(year)d.') % {'round': self.number(),
                                                                                          'year': self.final_year})
        # Shuffle the resulting list
        random.shuffle(results)
        return results

    def clean(self):
        # Must provide either both end times, or neither
        if self.earliest_end_time and not self.latest_end_time:
            raise ValidationError(_(u'Earliest end time specified without latest end time'))
        if self.latest_end_time and not self.earliest_end_time:
            raise ValidationError(_(u'Latest end time specified without earliest end time'))

    def get_absolute_url(self):
        return reverse('round_detail',
                       args=[str(self.tournament.id), str(self.number())])

    def __str__(self):
        return _(u'%(tournament)s Round %(round)d') % {'tournament': self.tournament, 'round': self.number()}

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
    # TODO Use this
    power_assignment = models.CharField(max_length=1,
                                        verbose_name=_(u'Power assignment method'),
                                        choices=POWER_ASSIGNS,
                                        default=RANDOM)

    class Meta:
        ordering = ['name']

    def create_or_update_sc_counts_from_ownerships(self, year):
        """
        Ensures that there is one CentreCount for each power for the specified year,
        and that the values match those determined by looking at the SupplyCentreOwnerships
        for that year.
        """
        all_scos = self.supplycentreownership_set.filter(year=year)
        if not all_scos.exists():
            raise SCOwnershipsNotFound('%d of game %s' % (year, str(self)))
        for p in GreatPower.objects.all():
            # We can't use get_or_create() here because count may not match
            try:
                i = CentreCount.objects.get(power=p,
                                            game=self,
                                            year=year)
                i.count = len(all_scos.filter(owner=p))
            except CentreCount.DoesNotExist:
                i = CentreCount(power=p,
                                game=self,
                                year=year,
                                count=len(all_scos.filter(owner=p)))
            i.save()

    def scores(self, force_recalculation=False):
        """
        If the game has ended and force_recalculation is False, report the recorded scores.
        If the game has not ended or force_recalculation is True, calculate the scores if
        the game were to end now.
        Return value is a dict, indexed by power id, of scores.
        """
        if self.is_finished and not force_recalculation:
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
        Dict, keyed by power id, of integer rankings (1 for first place, 2 for second place, etc)
        """
        result = {}
        last_score = None
        for i,(k,v) in enumerate(sorted([(k,v) for k,v in self.scores().items()], key=itemgetter(1), reverse=True)):
            if v != last_score:
                place, last_score = i + 1, v
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
        return sorted(list(set([sc.year for sc in scs])))

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
        player_dict = self.players(latest=True)
        centres_set = self.centrecount_set.order_by('-year')
        last_year = centres_set[0].year
        current_scs = centres_set.filter(year=last_year)
        results = []
        if (mask & MASK_BOARD_TOP) != 0:
            # Who's topping the board ?
            max_scs = current_scs.order_by('-count')[0].count
            first = current_scs.order_by('-count').filter(count=max_scs)
            first_str = ', '.join(['%s (%s)' % (player_dict[scs.power][0],
                                                _(scs.power.abbreviation)) for scs in list(first)])
            results.append(_(u'Highest SC count%(game)s is %(dots)d, for %(player)s.') % {'game': gn_str,
                                                                                          'dots': max_scs,
                                                                                          'player': first_str})
        if last_year > 1900:
            prev_scs = centres_set.filter(year=last_year-1)
        else:
            # We only look for differences, so just force no differences
            prev_scs = current_scs
        for scs in current_scs:
            power = scs.power
            prev = prev_scs.get(power=power)
            # Who gained 2 or more centres in the last year ?
            if (mask & MASK_GAINERS) != 0:
                if scs.count - prev.count > 1:
                    results.append(_(u'%(player)s (%(power)s) grew from %(old)d to %(new)d centres%(game)s.') % {'player': player_dict[power][0],
                                                                                                                 'power': _(power.abbreviation),
                                                                                                                 'old': prev.count,
                                                                                                                 'new': scs.count,
                                                                                                                 'game': gn_str})
            # Who lost 2 or more centres in the last year ?
            if (mask & MASK_LOSERS) != 0:
                if prev.count - scs.count > 1:
                    results.append(_(u'%(player)s (%(power)s) shrank from %(old)d to %(new)d centres%(game)s.') % {'player': player_dict[power][0],
                                                                                                                   'power': _(power.abbreviation),
                                                                                                                   'old': prev.count,
                                                                                                                   'new': scs.count,
                                                                                                                   'game': gn_str})
        if (mask & MASK_DRAW_VOTES) != 0:
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
                    game_player = self.gameplayer_set.filter(power=power).get()
                    incl.append(_(u'%(player)s (%(power)s)') % {'player': game_player.player,
                                                                'power': _(power.abbreviation)})
                incl_str = ', '.join(incl)
                if self.the_round.tournament.draw_secrecy == COUNTS:
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
            while len(zeroes):
                scs = zeroes[0]
                power = scs.power
                zeroes = zeroes.exclude(power=power)
                results.append(_(u'%(player)s (%(power)s) was eliminated in %(year)d%(game)s.') % {'player': player_dict[power][0],
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
        for c,players in players_by_power.items():
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
            return self.drawproposal_set.filter(passed=True).get()
        except DrawProposal.DoesNotExist:
            return None

    def board_toppers(self):
        """
        Returns a list of CentreCounts for the current leader(s)
        """
        centres_set = self.centrecount_set.order_by('-year')
        last_year = centres_set[0].year
        current_scs = centres_set.filter(year=last_year)
        max_scs = current_scs.order_by('-count')[0].count
        first = current_scs.order_by('-count').filter(count=max_scs)
        return list(first)

    def neutrals(self, year=None):
        """How many neutral SCs are/were there ?"""
        if not year:
            year = self.final_year()
        scs = self.centrecount_set.filter(year=year)
        if not scs.exists():
            raise InvalidYear(year)
        return TOTAL_SCS - scs.aggregate(Sum('count'))['count__sum']

    def final_year(self):
        """
        Returns the last complete year of the game, whether the game is completed or ongoing
        """
        return self.years_played()[-1]

    def soloer(self):
        """
        Returns either a GamePlayer if somebody soloed the game, or None
        """
        # Just order by SC count, and check the first (highest)
        scs = self.centrecount_set.order_by('-count')
        if scs[0].count >= WINNING_SCS:
            # TODO This looks like it fails if the soloer was a replacement player
            return self.gameplayer_set.filter(power=scs[0].power).get()
        return None

    def survivors(self, year=None):
        """
        Returns a list of the CentreCounts for the surviving powers.
        If a year is provided, it returns a list of the powers that survived that whole year.
        If a year is provided for which there are no CentreCounts, an empty list will be returned.
        """
        scs = self.centrecount_set.all().order_by('-year')
        if not year:
            year = scs.first().year
        final_scs = scs.filter(year = year)
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
                retval = _(u'Vote passed to end game%(game)s as a %(n)d-way draw between ') % {'game': gn_str, 'n': sz}
            winners = []
            for power in powers:
                # TODO This looks broken if there were replacements
                game_player = self.gameplayer_set.filter(power=power).get()
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
        # Game names must be unique within the tournament
        games = Game.objects.filter(the_round__tournament=self.the_round.tournament).distinct()
        for g in games:
            if (self != g) and (self.name == g.name):
                raise ValidationError(_('Game names must be unique within the tournament'))

    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)

        # Auto-create 1900 SC counts (unless they already exist)
        # Auto-create SC Ownership (unless they already exist)
        for power in GreatPower.objects.all():
            i, created = CentreCount.objects.get_or_create(power=power,
                                                           game=self,
                                                           year=FIRST_YEAR-1,
                                                           count=power.starting_centres)
            i.save()
            for sc in SupplyCentre.objects.filter(initial_owner=power):
                i, created = SupplyCentreOwnership.objects.get_or_create(owner=power,
                                                                         game=self,
                                                                         year=FIRST_YEAR-1,
                                                                         sc=sc)
                i.save()

        # Auto-create S1901M image (if it doesn't exist)
        i, created = GameImage.objects.get_or_create(game=self,
                                                     year=FIRST_YEAR,
                                                     season=SPRING,
                                                     phase=MOVEMENT,
                                                     image=self.the_set.initial_image)
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
                scores = r.scores(True)
                for p in r.roundplayer_set.all():
                    try:
                        p.score = scores[p.player]
                    except KeyError:
                        # Player was checked at roll call but didn't play
                        # TODO May want to add a way to give them some points
                        pass
                    p.save()

            # if the tournament is (now) finished, store the player scores
            t = self.the_round.tournament
            if t.is_finished():
                scores = t.scores(True)
                for p in t.tournamentplayer_set.all():
                    try:
                        p.score = scores[p.player]
                    except KeyError:
                        # Player was added to the tournament but didn't play
                        pass
                    p.save()

    def get_absolute_url(self):
        return reverse('game_detail',
                       args=[str(self.the_round.tournament.id), self.name])

    def __str__(self):
        return self.name

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
        return "%s in %s was owned by %s at the end of %d" % (self.sc, self.game, self.owner, self.year)

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
    power_2 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    power_3 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    power_4 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    power_5 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    power_6 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    power_7 = models.ForeignKey(GreatPower, blank=True, null=True, related_name='+', on_delete=models.CASCADE)
    votes_in_favour = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_vote_count])

    def draw_size(self):
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
        Returns a Boolean indicating whether the specified power is included or not.
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
        survivors = len([sc for sc in scs if sc.count > 0])
        try:
            return survivors - self.votes_in_favour
        except TypeError:
            raise TypeError(_('This DrawProposal only has pass/fail, not vote counts'))

    def clean(self):
        # No skipping powers
        found_null = False
        for n in range(1,8):
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
                    raise ValidationError(_(u'%(power)s present more than once'), params = {'power':  power})
                powers.add(power)
        # Only one successful draw proposal
        if self.passed:
            try:
                p = DrawProposal.objects.filter(game=self.game, passed=True).get()
                if p != self:
                    raise ValidationError(_(u'Game already has a successful draw proposal'))
            except DrawProposal.DoesNotExist:
                pass
        # No successful proposal prior to the latest SC count
        final_year = self.game.final_year()
        if self.passed and (self.year <= final_year):
            raise ValidationError(_(u'Game already has a centre count for %(year)d'), params = {'year': final_year})
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
                    raise ValidationError(_(u'Dead power %(power)s included in proposal'), params = {'power': sc.power})
            else:
                if dias and sc.count > 0:
                    raise ValidationError(_(u'Missing alive power %(power)s in DIAS game'), params = {'power': sc.power})
        # Ensure that either passed or votes_in_favour, as appropriate, are set
        if self.game.the_round.tournament.draw_secrecy == SECRET:
            if not self.passed:
                raise ValidationError(_('Passed needs a value'))
        elif self.game.the_round.tournament.draw_secrecy == COUNTS:
            if not self.votes_in_favour:
                raise ValidationError(_('Votes_in_favour needs a value'))
            # Derive passed from votes_in_favour and survivor count
            survivors = len([sc for sc in scs if sc.count > 0])
            if self.votes_in_favour:
                # Votes must be unanimous
                self.passed = (self.votes_in_favour == survivors)
        else:
            assert 0, 'Tournament draw secrecy has an unexpected value %c' % self.game.the_round.tournament.draw_secrecy

    def save(self, *args, **kwargs):
        super(DrawProposal, self).save(*args, **kwargs)
        # Does this complete the game ?
        if self.passed:
            self.game.is_finished = True
            self.game.save()

    def __str__(self):
        return u'%s %d%s' % (self.game, self.year, self.season)

class RoundPlayer(models.Model):
    """
    A person who played a round in a tournament
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    the_round = models.ForeignKey(Round, verbose_name=_(u'round'), on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ['player']

    def clean(self):
        # Player should already be in the tournament
        t = self.the_round.tournament
        if not self.player.tournamentplayer_set.filter(tournament=t).exists():
            raise ValidationError(_(u'Player is not yet in the tournament'))

    def __str__(self):
        return _(u'%(player)s in %(round)s') % {'player': self.player, 'round': self.the_round}

class GamePlayer(models.Model):
    """
    A person who played a Great Power in a Game
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    power = models.ForeignKey(GreatPower, related_name='+', on_delete=models.CASCADE)
    first_year = models.PositiveSmallIntegerField(default=FIRST_YEAR, validators=[validate_year])
    first_season = models.CharField(max_length=1, choices=SEASONS, default=SPRING)
    last_year = models.PositiveSmallIntegerField(blank=True, null=True, validators=[validate_year])
    last_season = models.CharField(max_length=1, choices=SEASONS, blank=True)
    score = models.FloatField(default=0.0)
    # What order did this player choose their GreatPower ?
    # 1 => first, 7 => seventh, 0 => assigned rather than chosen
    # TODO Use this
    # TODO Add validators
    power_choice_order = models.PositiveSmallIntegerField(default=1)

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
        elif e_year == self.last_year and self.last_season == SPRING:
            return None
        return e_year

    def clean(self):
        # Player should already be in the tournament
        t = self.game.the_round.tournament
        tp = self.player.tournamentplayer_set.filter(tournament=t)
        if not tp:
            raise ValidationError(_(u'Player is not yet in the tournament'))
        # Need either both or neither of last_year and last_season
        if self.last_season == '' and self.last_year:
            raise ValidationError(_(u'Final season played must also be specified'))
        if self.last_season != '' and not self.last_year:
            raise ValidationError(_(u'Final year must be specified with final season'))
        # Check for overlap with another player
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
                                          params = {'player1': other.player,
                                                    'player2': self.player,
                                                    'power': self.power,
                                                    'season': self.first_season,
                                                    'year': self.first_year})
                if self.first_season == SPRING:
                    we_were_first = True
                else:
                    we_were_first = False
            else:
                we_were_first = False
            if we_were_first:
                # Our term must finish before theirs started
                err_str = _(u'%(player)s is listed as playing %(power)s in game %(game)s from %(season)s %(year)d')
                if not self.last_year or self.last_year > other.first_year:
                    raise ValidationError(err_str,
                                          params = {'player': other.player,
                                                    'power': other.power,
                                                    'game': other.game.name,
                                                    'season': other.first_season,
                                                    'year': other.first_year})
                if self.last_year == other.first_year:
                    if self.last_season != SPRING or other.first_season != FALL:
                        raise ValidationError(err_str,
                                              params = {'player': other.player,
                                                        'power': other.power,
                                                        'game': other.game.name,
                                                        'season': other.first_season,
                                                        'year': other.first_year})
            else:
                # Their term must finish before ours started
                err_str = _(u'%(player)s is listed as still playing %(power)s in game %(game)s from %(season)s %(year)d')
                if not other.last_year or other.last_year > self.first_year:
                    raise ValidationError(err_str,
                                          params = {'player': other.player,
                                                    'power': other.power,
                                                    'game': other.game,
                                                    'season': other.first_season,
                                                    'year': other.first_year})
                if other.last_year == self.first_year:
                    if other.last_season != SPRING or self.first_season != FALL:
                        raise ValidationError(err_str,
                                              params = {'player': other.player,
                                                        'power': other.power,
                                                        'game': other.game,
                                                        'season': other.first_season,
                                                        'year': other.first_year})
        # TODO Ensure no gaps - may have to be done elsewhere

    def __str__(self):
        return u'%s %s %s' % (self.game, self.player, self.power)

class GameImage(models.Model):
    """
    An image depicting a Game at a certain point.
    The year, season, phase together indicate the phase that is about to played.
    """
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
        return u'%s%d%s' % (self.season, self.year, phase_str[self.phase])

    def clean(self):
        if self.season == SPRING and self.phase == ADJUSTMENTS:
            raise ValidationError(_(u'No adjustment phase in spring'))

    def get_absolute_url(self):
        return reverse('game_image', args=[str(self.game.the_round.tournament.id), self.game.name, self.turn_str()])

    def __str__(self):
        return _(u'%(game)s %(turn)s image') % {'game': self.game, 'turn': self.turn_str()}

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
        # Is this for a year that is supposed to be played ?
        final_year = self.game.the_round.final_year
        if final_year and self.year > final_year:
                raise ValidationError(_(u'Games in this round end with %(year)d'), params = {'year': final_year})
        # Not possible to more than double your count in one year
        # or to recover from an elimination
        try:
            prev = CentreCount.objects.filter(power=self.power, game=self.game, year=self.year-1).get()
        except CentreCount.DoesNotExist:
            # We're either missing a year, or this is the first year - let that go
            return
        if (prev.count == 0) and (self.count > 0):
            raise ValidationError(_(u'SC count for a power cannot increase from zero'))
        elif self.count > 2 * prev.count:
            raise ValidationError(_(u'SC count for a power cannot more than double in a year'))

    def save(self, *args, **kwargs):
        super(CentreCount, self).save(*args, **kwargs)
        # Does this complete the game ?
        final_year = self.game.the_round.final_year
        if final_year and self.year == final_year:
            # Final game year has been played
            self.game.is_finished = True
            self.game.save()
        if self.count >= WINNING_SCS:
            # Somebody won the game
            self.game.is_finished = True
            self.game.save()

    def __str__(self):
        return u'%s %d %s %d' % (self.game, self.year, _(self.power.abbreviation), self.count)

