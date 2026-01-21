# Diplomacy Tournament Visualiser
# Copyright (C) 2019 Chris Brand
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

from datetime import date, datetime, time, timedelta, timezone

from django_countries.fields import Country
from django.test import TestCase
from django.urls import reverse

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.game_scoring.g_scoring_systems import G_SCORING_SYSTEMS
from tournament.models import DrawSecrecy
from tournament.models import Tournament, Round, Game, Team
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import CentreCount, DrawProposal, Seasons
from tournament.players import Player

class WddViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # Easy access to all the GreatPowers
        austria = GreatPower.objects.get(abbreviation='A')
        england = GreatPower.objects.get(abbreviation='E')
        france = GreatPower.objects.get(abbreviation='F')
        germany = GreatPower.objects.get(abbreviation='G')
        italy = GreatPower.objects.get(abbreviation='I')
        russia = GreatPower.objects.get(abbreviation='R')
        turkey = GreatPower.objects.get(abbreviation='T')

        today = date.today()

        # Published Tournament so it's visible to all
        cls.t = Tournament.objects.create(name='t1',
                                          start_date=today,
                                          end_date=today + timedelta(hours=24),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          is_published=True)
        # Awards
        cls.t.awards.create(name='Meanest Player',
                            description='Who was mean')
        a1 = cls.t.awards.create(name='Nicest Player',
                                 description='Who bought the most drinks')
        a2 = cls.t.awards.create(name='Best Russia',
                                 description='Russia is the only country we care about',
                                 power=russia)
        cls.t.awards.create(name='Best Germany',
                            description='Germany is another country we care about',
                            power=england)
        # Two Rounds
        r1 = Round.objects.create(tournament=cls.t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=False,
                                  start=datetime.combine(cls.t.start_date, time(hour=8, tzinfo=timezone.utc)))
        r2 = Round.objects.create(tournament=cls.t,
                                  scoring_system=G_SCORING_SYSTEMS[0].name,
                                  dias=True,
                                  start=r1.start + timedelta(hours=24),
                                  final_year=1907)
        # Two Games in the first Round, top board in the second
        g1 = Game.objects.create(name="R1G1",
                                 started_at=r1.start,
                                 the_round=r1,
                                 the_set=GameSet.objects.first())
        g2 = Game.objects.create(name="R1G2",
                                 started_at=r1.start,
                                 the_round=r1,
                                 the_set=GameSet.objects.first())
        g3 = Game.objects.create(name="TopBoard",
                                 started_at=r2.start + timedelta(hours=24),
                                 the_round=r2,
                                 the_set=GameSet.objects.first(),
                                 is_top_board=True)
        # Players, RoundPlayers, and GamePlayers
        p1 = Player.objects.create(first_name='Angela',
                                   last_name='Ampersand')
        p2 = Player.objects.create(first_name='Bobby',
                                   last_name='Bandersnatch')
        p3 = Player.objects.create(first_name='Cassandra',
                                   last_name='Cucumber')
        p4 = Player.objects.create(first_name='Derek',
                                   last_name='Dromedary')
        p5 = Player.objects.create(first_name='Ethel',
                                   last_name='Elephant')
        p6 = Player.objects.create(first_name='Frank',
                                   last_name='Frankfurter')
        p7 = Player.objects.create(first_name='Georgette',
                                   last_name='Grape')
        p8 = Player.objects.create(first_name='Harry',
                                   last_name='Heffalump',
                                   nationalities=Country('GB'))
        p9 = Player.objects.create(first_name='Iris',
                                   last_name='Ignoramus')
        p10 = Player.objects.create(first_name='Jake',
                                    last_name='Jalopy',
                                    nationalities=[Country('US'), Country('KR')])
        p11 = Player.objects.create(first_name='Katrina',
                                    last_name='Kingpin')
        p12 = Player.objects.create(first_name='Lucas',
                                    last_name='Lemon',
                                    nationalities=Country('ES'))
        p13 = Player.objects.create(first_name='Margaret',
                                    last_name='Maleficent')
        p14 = Player.objects.create(first_name='Nigel',
                                    last_name='Notorious')
        p15 = Player.objects.create(first_name='Oscar',
                                    last_name='Ostentatious')
        TournamentPlayer.objects.create(player=p1,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p1,
                                   the_round=r1)
        GamePlayer.objects.create(player=p1,
                                  game=g1,
                                  power=turkey)
        TournamentPlayer.objects.create(player=p2,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p2,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p2,
                                   the_round=r2)
        GamePlayer.objects.create(player=p2,
                                  game=g1,
                                  power=russia)
        GamePlayer.objects.create(player=p2,
                                  game=g3,
                                  power=italy)
        TournamentPlayer.objects.create(player=p3,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p3,
                                   the_round=r1)
        GamePlayer.objects.create(player=p3,
                                  game=g2,
                                  power=austria)
        TournamentPlayer.objects.create(player=p4,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p4,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p4,
                                   the_round=r2)
        GamePlayer.objects.create(player=p4,
                                  game=g2,
                                  power=england)
        GamePlayer.objects.create(player=p4,
                                  game=g3,
                                  power=turkey)
        TournamentPlayer.objects.create(player=p5,
                                        tournament=cls.t,
                                        location='Spain')
        RoundPlayer.objects.create(player=p5,
                                   the_round=r1)
        GamePlayer.objects.create(player=p5,
                                  game=g1,
                                  power=italy)
        TournamentPlayer.objects.create(player=p6,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p6,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p6,
                                   the_round=r2)
        GamePlayer.objects.create(player=p6,
                                  game=g1,
                                  power=germany)
        GamePlayer.objects.create(player=p6,
                                  game=g3,
                                  power=france)
        TournamentPlayer.objects.create(player=p7,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p7,
                                   the_round=r1)
        GamePlayer.objects.create(player=p7,
                                  game=g1,
                                  power=france)
        cls.tp8 = TournamentPlayer.objects.create(player=p8,
                                                  tournament=cls.t,
                                                  location='California, USA')
        RoundPlayer.objects.create(player=p8,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p8,
                                   the_round=r2)
        GamePlayer.objects.create(player=p8,
                                  game=g2,
                                  power=france)
        GamePlayer.objects.create(player=p8,
                                  game=g3,
                                  power=russia)
        TournamentPlayer.objects.create(player=p9,
                                        tournament=cls.t,
                                        unranked=True)
        RoundPlayer.objects.create(player=p9,
                                   the_round=r1)
        GamePlayer.objects.create(player=p9,
                                  game=g2,
                                  power=germany)
        tp10 = TournamentPlayer.objects.create(player=p10,
                                               tournament=cls.t,
                                               location='London, England')
        RoundPlayer.objects.create(player=p10,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p10,
                                   the_round=r2)
        GamePlayer.objects.create(player=p10,
                                  game=g2,
                                  power=italy)
        GamePlayer.objects.create(player=p10,
                                  game=g3,
                                  power=germany)
        TournamentPlayer.objects.create(player=p11,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p11,
                                   the_round=r1)
        GamePlayer.objects.create(player=p11,
                                  game=g1,
                                  power=england)
        TournamentPlayer.objects.create(player=p12,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p12,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p12,
                                   the_round=r2)
        GamePlayer.objects.create(player=p12,
                                  game=g2,
                                  power=russia)
        GamePlayer.objects.create(player=p12,
                                  game=g3,
                                  power=austria)
        TournamentPlayer.objects.create(player=p13,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p13,
                                   the_round=r1)
        GamePlayer.objects.create(player=p13,
                                  game=g1,
                                  power=austria)
        TournamentPlayer.objects.create(player=p14,
                                        tournament=cls.t)
        RoundPlayer.objects.create(player=p14,
                                   the_round=r1)
        RoundPlayer.objects.create(player=p14,
                                   the_round=r2)
        GamePlayer.objects.create(player=p14,
                                  game=g2,
                                  power=turkey)
        GamePlayer.objects.create(player=p14,
                                  game=g3,
                                  power=england)
        # One TournamentPlayer who didn't actually play
        TournamentPlayer.objects.create(player=p15,
                                        tournament=cls.t)
        # Hand out one non-best-country award
        tp10.awards.add(a1)
        # and one best-country award
        # for a power that they actually played
        played = [gp.power for gp in GamePlayer.objects.filter(player=cls.tp8.player)]
        if a2.power not in played:
            raise AssertionError(f"{str(cls.tp8.player)} didn't play {str(a2.power)}")
        cls.tp8.awards.add(a2)
        # CentreCounts and DrawProposals
        # One game ends in a solo
        CentreCount.objects.create(power=austria,
                                   game=g1,
                                   year=1903,
                                   count=0)
        CentreCount.objects.create(power=england,
                                   game=g1,
                                   year=1903,
                                   count=4)
        CentreCount.objects.create(power=france,
                                   game=g1,
                                   year=1903,
                                   count=5)
        CentreCount.objects.create(power=germany,
                                   game=g1,
                                   year=1903,
                                   count=7)
        CentreCount.objects.create(power=italy,
                                   game=g1,
                                   year=1903,
                                   count=4)
        CentreCount.objects.create(power=russia,
                                   game=g1,
                                   year=1903,
                                   count=10)
        CentreCount.objects.create(power=turkey,
                                   game=g1,
                                   year=1903,
                                   count=4)
        CentreCount.objects.create(power=austria,
                                   game=g1,
                                   year=1909,
                                   count=0)
        CentreCount.objects.create(power=england,
                                   game=g1,
                                   year=1909,
                                   count=0)
        CentreCount.objects.create(power=france,
                                   game=g1,
                                   year=1909,
                                   count=4)
        CentreCount.objects.create(power=germany,
                                   game=g1,
                                   year=1909,
                                   count=12)
        CentreCount.objects.create(power=italy,
                                   game=g1,
                                   year=1909,
                                   count=0)
        CentreCount.objects.create(power=russia,
                                   game=g1,
                                   year=1909,
                                   count=18)
        CentreCount.objects.create(power=turkey,
                                   game=g1,
                                   year=1909,
                                   count=0)
        g1.update_scores()
        # Another with an elimination and a draw
        dp = DrawProposal.objects.create(game=g2,
                                         year=1908,
                                         season=Seasons.FALL,
                                         passed=False,
                                         proposer=germany)
        dp.drawing_powers.add(germany)
        dp.drawing_powers.add(france)
        dp.drawing_powers.add(england)
        dp = DrawProposal.objects.create(game=g2,
                                         year=1910,
                                         season=Seasons.FALL,
                                         passed=True,
                                         proposer=france)
        dp.drawing_powers.add(england)
        dp.drawing_powers.add(france)
        CentreCount.objects.create(power=austria,
                                   game=g2,
                                   year=1908,
                                   count=3)
        CentreCount.objects.create(power=england,
                                   game=g2,
                                   year=1908,
                                   count=8)
        CentreCount.objects.create(power=france,
                                   game=g2,
                                   year=1908,
                                   count=7)
        CentreCount.objects.create(power=germany,
                                   game=g2,
                                   year=1908,
                                   count=7)
        CentreCount.objects.create(power=italy,
                                   game=g2,
                                   year=1908,
                                   count=2)
        CentreCount.objects.create(power=russia,
                                   game=g2,
                                   year=1908,
                                   count=4)
        CentreCount.objects.create(power=turkey,
                                   game=g2,
                                   year=1908,
                                   count=3)
        CentreCount.objects.create(power=austria,
                                   game=g2,
                                   year=1910,
                                   count=1)
        CentreCount.objects.create(power=england,
                                   game=g2,
                                   year=1910,
                                   count=12)
        CentreCount.objects.create(power=france,
                                   game=g2,
                                   year=1910,
                                   count=13)
        CentreCount.objects.create(power=germany,
                                   game=g2,
                                   year=1910,
                                   count=1)
        CentreCount.objects.create(power=italy,
                                   game=g2,
                                   year=1910,
                                   count=2)
        CentreCount.objects.create(power=russia,
                                   game=g2,
                                   year=1910,
                                   count=2)
        CentreCount.objects.create(power=turkey,
                                   game=g2,
                                   year=1910,
                                   count=3)
        g2.update_scores()
        # Top board ends after 1907
        CentreCount.objects.create(power=austria,
                                   game=g3,
                                   year=1907,
                                   count=7)
        CentreCount.objects.create(power=england,
                                   game=g3,
                                   year=1907,
                                   count=0)
        CentreCount.objects.create(power=france,
                                   game=g3,
                                   year=1907,
                                   count=6)
        CentreCount.objects.create(power=germany,
                                   game=g3,
                                   year=1907,
                                   count=4)
        CentreCount.objects.create(power=italy,
                                   game=g3,
                                   year=1907,
                                   count=6)
        CentreCount.objects.create(power=russia,
                                   game=g3,
                                   year=1907,
                                   count=4)
        CentreCount.objects.create(power=turkey,
                                   game=g3,
                                   year=1907,
                                   count=7)
        g3.update_scores()

    def test_classification(self):
        response = self.client.get(reverse('csv_classification',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Check CSV file content
        # first, last, homonym, rank, exaequo, location, nationality
        self.assertContains(response, 'Cassandra,Cucumber,1,8,1,')
        self.assertContains(response, 'Harry,Heffalump,1,3,1,USA,ANG,')
        self.assertContains(response, 'Iris,Ignoramus,1,999,1,')

    def test_classification_no_top_board(self):
        # Switch the top board to a regular board
        g = Game.objects.get(is_top_board=True)
        g.is_top_board=False
        g.save(update_fields=['is_top_board'])
        response = self.client.get(reverse('csv_classification',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # TODO Check CSV file content
        # Clean up
        g.is_top_board=True
        g.save(update_fields=['is_top_board'])

    def test_classification_many_awards(self):
        """Tournament with more than the 12 (non-best country) awards supported by the WDD"""
        awards = self.t.awards.all()
        orig_awards = list(awards)
        for n in range(13 - awards.filter(power=None).count()):
            # Add awards that will get a lower number (later in the alphabet)
            self.t.awards.create(name=f'AAA Award {n}',
                                 description='Everyone gets an award!')
        # Check that the last award has been given to a player
        self.assertEqual(self.t.awards.last().tournamentplayer_set.exists(), True)
        response = self.client.get(reverse('csv_classification',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean up
        self.t.awards.exclude(pk__in=[a.pk for a in orig_awards]).delete()

    def test_classification_tied_best_country(self):
        a = self.t.awards.filter(power__isnull=False).first()
        orig_tps = list(a.tournamentplayer_set.all())
        for gp in GamePlayer.objects.filter(power=a.power,
                                            game__the_round__tournament=self.t).all():
            # Add this player to the list
            tp = gp.tournamentplayer()
            tp.awards.add(a)
        response = self.client.get(reverse('csv_classification',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean up
        for tp in a.tournamentplayer_set.exclude(pk__in=[tp.pk for tp in orig_tps]).all():
            a.tournamentplayer_set.remove(tp)

    def test_classification_with_teams(self):
        """classification for tournament with teams"""
        self.t.team_size = 2
        self.t.save()
        r = self.t.round_set.first()
        r.is_team_round = True
        r.save()
        tm1 = Team.objects.create(tournament=self.t,
                                  name="Team 1")
        tm2 = Team.objects.create(tournament=self.t,
                                  name="Team 2")
        # add players to teams
        for rp in r.roundplayer_set.all():
            if tm1.players.count() < 2:
                tm1.players.add(rp.player)
            elif tm2.players.count() < 2:
                tm2.players.add(rp.player)
            else:
                break
        response = self.client.get(reverse('csv_classification',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # TODO Check CSV file content
        # Clean up
        r.is_team_round = False
        r.save()
        self.t.team_set.all().delete()
        self.t.team_size = None
        self.t.save()

    def test_boards(self):
        response = self.client.get(reverse('csv_boards',
                                           args=(self.t.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # TODO Check CSV file content

