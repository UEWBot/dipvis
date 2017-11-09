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

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from tournament.models import *
from tournament.background import WDD_Background, InvalidWDDId
from tournament.players import PlayerRanking

from datetime import timedelta

HOURS_8 = timedelta(hours=8)
HOURS_9 = timedelta(hours=9)
HOURS_10 = timedelta(hours=10)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

CHRIS_BRAND_WDD_ID = 4173
INVALID_WDD_ID = 1
MATT_SHIELDS_WDD_ID = 588
MATT_SUNDSTROM_WDD_ID = 8355
NATE_COCKERILL_WDD_ID = 5009
SPIROS_BOBETSIS_WDD_ID = 12304

class TournamentModelTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        cls.set1 = GameSet.objects.get(name='Avalon Hill')
        cls.set2 = GameSet.objects.get(name='Gibsons')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=SECRET)
        t2 = Tournament.objects.create(name='t2',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date)
        r12 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_16)
        r14 = Round.objects.create(tournament=t1, scoring_system=s1, dias=True, start=t1.start_date + HOURS_24)
        # Add Rounds to t2
        r21 = Round.objects.create(tournament=t2, scoring_system=s1, dias=False, start=t2.start_date)
        r22 = Round.objects.create(tournament=t2, scoring_system=s1, dias=False, start=t2.start_date + HOURS_8)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3, scoring_system=s1, dias=True, start=t3.start_date, final_year=1907)
        r32 = Round.objects.create(tournament=t3, scoring_system=s1, dias=True, start=t3.start_date + HOURS_8,
                                   earliest_end_time=t3.start_date + HOURS_8, latest_end_time=t3.start_date + HOURS_9)

        # Add Games to r11
        g11 = Game.objects.create(name='g11', started_at=r11.start, the_round=r11, the_set=cls.set1)
        g12 = Game.objects.create(name='g12', started_at=r11.start, the_round=r11, the_set=cls.set1)
        # Add Games to r12
        g13 = Game.objects.create(name='g13', started_at=r12.start, the_round=r12, is_finished=True, the_set=cls.set1)
        g14 = Game.objects.create(name='g14', started_at=r12.start, the_round=r12, the_set=cls.set1)
        # Add Games to r13
        g15 = Game.objects.create(name='g15', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)
        g16 = Game.objects.create(name='g16', started_at=r13.start, the_round=r13, is_finished=True, the_set=cls.set1)
        # Add Games to r21
        g21 = Game.objects.create(name='g21', started_at=r21.start, the_round=r21, the_set=cls.set1)
        # Add Games to r22
        g22 = Game.objects.create(name='g22', started_at=r22.start, the_round=r22, the_set=cls.set1)
        # Add Games to r31
        g31 = Game.objects.create(name='g31', started_at=r31.start, the_round=r31, is_finished=True, the_set=cls.set1)
        # Add Games to r32
        g32 = Game.objects.create(name='g32', started_at=r32.start, the_round=r32, is_finished=True, the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Add CentreCounts to g11
        sc1101a = CentreCount.objects.create(power=cls.austria, game=g11, year=1901, count=5)
        sc1101e = CentreCount.objects.create(power=cls.england, game=g11, year=1901, count=4)
        sc1101f = CentreCount.objects.create(power=cls.france, game=g11, year=1901, count=5)
        sc1101g = CentreCount.objects.create(power=cls.germany, game=g11, year=1901, count=5)
        sc1101i = CentreCount.objects.create(power=cls.italy, game=g11, year=1901, count=4)
        sc1101r = CentreCount.objects.create(power=cls.russia, game=g11, year=1901, count=5)
        sc1101t = CentreCount.objects.create(power=cls.turkey, game=g11, year=1901, count=4)

        sc1104a = CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        sc1104e = CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        sc1104f = CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=2)
        sc1104g = CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        sc1104i = CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=2)
        sc1104r = CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=3)
        sc1104t = CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=5)

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        gp11a1 = GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g11, power=cls.austria, last_year=1903, last_season='F')
        gp11a2 = GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g11, power=cls.austria, first_year=1903, first_season='X')
        gp11e1 = GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g11, power=cls.england)
        gp11f1 = GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g11, power=cls.france)
        gp11g1 = GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g11, power=cls.germany)
        gp11i1 = GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g11, power=cls.italy)
        gp11r1 = GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g11, power=cls.russia)
        gp11t1 = GamePlayer.objects.create(player=Player.objects.get(pk=8), game=g11, power=cls.turkey)
        # Add GamePlayers to g12
        gp12a = GamePlayer.objects.create(player=Player.objects.get(pk=7), game=g12, power=cls.austria)
        gp12e = GamePlayer.objects.create(player=Player.objects.get(pk=6), game=g12, power=cls.england)
        gp12f = GamePlayer.objects.create(player=Player.objects.get(pk=5), game=g12, power=cls.france)
        gp12g = GamePlayer.objects.create(player=Player.objects.get(pk=4), game=g12, power=cls.germany)
        gp12i = GamePlayer.objects.create(player=Player.objects.get(pk=3), game=g12, power=cls.italy)
        gp12r = GamePlayer.objects.create(player=Player.objects.get(pk=2), game=g12, power=cls.russia)
        gp12t = GamePlayer.objects.create(player=Player.objects.get(pk=1), game=g12, power=cls.turkey)

        # For t3 (the finished tournament), we want TournamentPlayers and RoundPlayers
        # Unfortunately, adding these slows down the test dramatically
        # due to adding background?
        # Add a TournamentPlayer to t3
        tp1 = TournamentPlayer.objects.create(player=Player.objects.get(pk=1), tournament=t3, score=147.3)
        # Add a RoundPlayer to r31
        rp1 = RoundPlayer.objects.create(player=Player.objects.get(pk=1), the_round=r31, score=100.0)
        # Add a RoundPlayer to r32
        rp2 = RoundPlayer.objects.create(player=Player.objects.get(pk=1), the_round=r32, score=47.3)

    # GScoringSolos
    def test_g_scoring_solos_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 0)

    def test_g_scoring_solos_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Solo or bust')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    # GScoringDrawSize
    def test_g_scoring_draws_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)

    def test_g_scoring_draws_7way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for s in scores.values():
            self.assertEqual(s, 100.0/7)

    def test_g_scoring_draws_4way_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.russia,
                                         power_4=self.germany)
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p in GreatPower.objects.all():
            if (p == self.austria) or (p == self.england) or (p == self.russia) or (p == self.germany):
                self.assertEqual(scores[p], 100.0/4)
            else:
                self.assertEqual(scores[p], 0.0)

    def test_g_scoring_draws_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Draw size')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    # GScoringCDiplo
    def test_g_scoring_cdiplo_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 1 + 4)
            else:
                self.assertEqual(s, 1 + (38 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 100-2=98
        self.assertEquals(sum(scores.values()), 100 - 2)

    def test_g_scoring_cdiplo_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('CDiplo 100')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    def test_g_scoring_cdiplo80_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 4)
            else:
                self.assertEqual(s, (25 + 14 + 7) / 4 + 5)
        # With 2 neutrals, the total of all scores should be 80-2=78
        self.assertEquals(sum(scores.values()), 80 - 2)

    def test_g_scoring_cdiplo80_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('CDiplo 80')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 80)
            else:
                self.assertEqual(s, 0)

    # GScoringSumOfSquares
    def test_g_scoring_squares_no_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, 100.0 * 16 / 148)
            else:
                self.assertEqual(s, 100.0 * 25 / 148)
        # Total of all scores should always be very close to 100
        self.assertAlmostEqual(sum(scores.values()), 100)

    def test_g_scoring_squares_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Sum of Squares')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 100)
            else:
                self.assertEqual(s, 0)

    # GScoringCarnage
    def test_g_scoring_carnage_simple(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1901)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            # 4 powers equal on 5 SCs, and 3 equal on 4 SCs
            if sc.count == 4:
                self.assertEqual(s, (3000 + 2000 + 1000) / 3 + 4)
            else:
                self.assertEqual(s, (7000 + 6000 + 5000 + 4000) / 4 + 5)
        self.assertEquals(sum(scores.values()), 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS - 2)

    def test_g_scoring_carnage_solo(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        scs = g.centrecount_set.filter(year=1904)
        system = find_game_scoring_system('Carnage with dead equal')
        scores = system.scores(scs)
        self.assertEqual(7, len(scores))
        for p,s in scores.items():
            sc = scs.get(power=p)
            if sc.count == 18:
                self.assertEqual(s, 7000 + 6000 + 5000 + 4000 + 3000 + 2000 + 1000 + TOTAL_SCS)
            else:
                self.assertEqual(s, 0)

    # TODO test Carnage scoring with eliminations but no solo

    # TODO RScoringBest

    # TODO TScoringSum

    # find_scoring_system()
    # Mostly tested implicitly, but we do want to check the error case
    def test_find_g_scoring_system_invalid(self):
        self.assertEqual(None, find_game_scoring_system('Invalid System'))

    def test_find_r_scoring_system_invalid(self):
        self.assertEqual(None, find_round_scoring_system('Invalid System'))

    def test_find_t_scoring_system_invalid(self):
        self.assertEqual(None, find_tournament_scoring_system('Invalid System'))

    # validate_year()
    def test_validate_year_negative(self):
        self.assertRaises(ValidationError, validate_year, -1)

    def test_validate_year_1899(self):
        self.assertRaises(ValidationError, validate_year, 1899)

    def test_validate_year_1900(self):
        self.assertRaises(ValidationError, validate_year, 1900)

    def test_validate_year_1901(self):
        self.assertIsNone(validate_year(1901))

    # validate_year_including_start()
    def test_validate_year_inc_start_negative(self):
        self.assertRaises(ValidationError, validate_year_including_start, -1)

    def test_validate_year_inc_start_1899(self):
        self.assertRaises(ValidationError, validate_year_including_start, 1899)

    def test_validate_year_inc_start_1900(self):
        self.assertIsNone(validate_year_including_start(1900))

    def test_validate_year_inc_start_1901(self):
        self.assertIsNone(validate_year_including_start(1901))

    # validate_sc_count()
    def test_validate_sc_count_negative(self):
        self.assertRaises(ValidationError, validate_sc_count, -1)

    def test_validate_sc_count_0(self):
        self.assertIsNone(validate_sc_count(0))

    def test_validate_sc_count_34(self):
        self.assertIsNone(validate_sc_count(34))

    def test_validate_sc_count_35(self):
        self.assertRaises(ValidationError, validate_sc_count, 35)

    # validate_wdd_id()
    def test_validate_wdd_id_me(self):
        self.assertIsNone(validate_wdd_id(CHRIS_BRAND_WDD_ID))

    def test_validate_wdd_id_1(self):
        # 1 is known to be unused
        # Note that this test will fail if the WDD can't be reached
        # (in that case, we assume the id is valid)
        self.assertRaises(ValidationError, validate_wdd_id, 1)

    # validate_game_name()
    def test_validate_game_name_spaces(self):
        self.assertRaises(ValidationError, validate_game_name, u'space name')

    def test_validate_game_name_valid(self):
        self.assertIsNone(validate_game_name(u'ok'))

    # Player.wdd_name()
    def test_player_wdd_name(self):
        p = Player.objects.get(pk=1)
        # TODO Validate results
        p.wdd_name()

    def test_player_wdd_name_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_name()

    # Player.wdd_url()
    def test_player_wdd_url(self):
        p = Player.objects.get(pk=1)
        # TODO Validate results
        p.wdd_url()

    def test_player_wdd_url_no_id(self):
        p = Player.objects.create(first_name='John', last_name='Smith')
        # TODO Validate results
        p.wdd_url()

    # Player.background()
    def test_player_background(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        # TODO Validate results
        p.background()

    def test_player_background_no_wins(self):
        # Spiros has yet to win a tournament
        p, created = Player.objects.get_or_create(first_name='Spiros',
                                                  last_name='Bobetsis',
                                                  wdd_player_id=SPIROS_BOBETSIS_WDD_ID)
        p.save()
        add_player_bg(p)
        # TODO Validate results
        p.background()
        p.delete()

    def test_player_background_mask(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        self.assertEqual([], p.background(mask=0))

    def test_player_background_with_power(self):
        p = Player.objects.get(wdd_player_id=CHRIS_BRAND_WDD_ID)
        add_player_bg(p)
        # TODO Validate results
        p.background(power=self.germany)

    def test_player_background_td(self):
        # Matt has tournaments listings for tournaments when he was TD
        p, created = Player.objects.get_or_create(first_name='Matt',
                                                  last_name='Shields',
                                                  wdd_player_id=MATT_SHIELDS_WDD_ID)
        p.save()
        add_player_bg(p)
        # TODO Validate results
        # WAC 10 he played Germany
        p.background(power=self.germany)
        p.delete()

    def test_player_background_non_std(self):
        # Matt has tournaments listings for non-Standard games
        p, created = Player.objects.get_or_create(first_name='Matt',
                                                  last_name='Sundstrom',
                                                  wdd_player_id=MATT_SUNDSTROM_WDD_ID)
        p.save()
        add_player_bg(p)
        # TODO Validate results
        # Windy City Weasels 2012 he played United Kingdom
        p.background()
        p.delete()

    def test_player_background_non_std_2(self):
        # Nate has tournaments listings for non-Standard games,
        # where power names match Standard powers (France)
        p, created = Player.objects.get_or_create(first_name='Nate',
                                                  last_name='Cockerill',
                                                  wdd_player_id=NATE_COCKERILL_WDD_ID)
        p.save()
        add_player_bg(p)
        # TODO Validate results
        # Windy City Weasels 2012 he played France
        p.background(power=self.france)
        p.delete()

    def test_player_background_unknown(self):
        p, created = Player.objects.get_or_create(first_name='Unknown', last_name='Player')
        add_player_bg(p)
        # TODO Validate results
        p.background()

    # Tournament.scores()
    def test_tournament_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system='Invalid System',
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        self.assertRaises(InvalidScoringSystem, t.scores)

    def test_tournament_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.scores()

    def test_tournament_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.scores()

    def test_tournament_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.scores(True)

    # Tournament.positions()
    def test_tournament_positions_finished(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.positions()

    def test_tournament_positions_unfinished(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.positions()

    # Tournament.round_numbered()
    def test_tourney_round_numbered_negative(self):
        t = Tournament.objects.get(name='t1')
        self.assertRaises(Round.DoesNotExist, t.round_numbered, -1)

    def test_tourney_round_numbered_3(self):
        t = Tournament.objects.get(name='t1')
        self.assertEqual(t.round_numbered(3).number(), 3)

    # Tournament.best_countries()
    def test_tournament_best_countries_with_games(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.best_countries()

    def test_tournament_best_countries_without_games(self):
        t = Tournament.objects.get(name='t3')
        self.assertEqual({}, t.best_countries())

    # Tournament.background()
    def test_tournament_background_without_players(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.background()

    def test_tournament_background_with_players(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.background()

    # Tournament.news()
    def test_tournament_news_in_progress(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        t.news()

    def test_tournament_news_ended(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        t.news()

    # Tournament.current_round()
    def test_tourney_current_round_none(self):
        # All games in t3 are finished
        t = Tournament.objects.get(name='t3')
        self.assertIsNone(t.current_round())

    def test_tourney_current_round(self):
        t = Tournament.objects.get(name='t1')
        r = t.current_round()
        # All earlier rounds should be finished
        for i in range(1, r.number()):
            # TODO coverage shows that this line is never hit
            self.assertTrue(t.round_numbered(i).is_finished(), 'round %d' % i)
        # This round should be unfinished
        self.assertFalse(r.is_finished())

    # Tournament.is_finished()
    def test_tourney_is_finished_some_rounds_over(self):
        t = Tournament.objects.get(name='t1')
        self.assertFalse(t.is_finished())

    def test_tourney_is_finished_no_rounds_over(self):
        t = Tournament.objects.get(name='t2')
        self.assertFalse(t.is_finished())

    def test_tourney_is_finished_all_rounds_over(self):
        t = Tournament.objects.get(name='t3')
        self.assertTrue(t.is_finished())

    def test_tourney_is_finished_no_rounds(self):
        t = Tournament.objects.create(name='Roundless',
                                      start_date=timezone.now(),
                                      end_date=timezone.now(),
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name)
        self.assertFalse(t.is_finished())

    # TournamentPlayer.position()
    def test_tournamentplayer_position_finished(self):
        t = Tournament.objects.get(name='t3')
        tp = t.tournamentplayer_set.filter(player__pk=1).get()
        self.assertEquals(tp.position(), 1)

    # Round.scores()
    def test_round_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system='Invalid System')
        r = Round.objects.create(tournament=t, scoring_system=G_SCORING_SYSTEMS[0].name, dias=True, start=t.start_date)
        self.assertRaises(InvalidScoringSystem, r.scores)

    def test_round_scores_finished(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores()

    def test_round_scores_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores()

    def test_round_scores_recalculate(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.scores(True)

    # Round.is_finished()
    def test_round_is_finished_no_games_over(self):
        t = Tournament.objects.get(name='t1')
        r1 = t.round_numbered(1)
        self.assertFalse(r1.is_finished())

    def test_round_is_finished_some_games_over(self):
        t = Tournament.objects.get(name='t1')
        r2 = t.round_numbered(2)
        self.assertFalse(r2.is_finished())

    def test_round_is_finished_all_games_over(self):
        t = Tournament.objects.get(name='t1')
        r3 = t.round_numbered(3)
        self.assertTrue(r3.is_finished())

    def test_round_is_finished_no_games(self):
        """
        Rounds with no games can't have started, let alone finished
        """
        t = Tournament.objects.get(name='t1')
        r4 = t.round_numbered(4)
        self.assertFalse(r4.is_finished())

    # Round.number()
    def test_round_number_11(self):
        t = Tournament.objects.get(name='t1')
        r11 = t.round_set.all()[0]
        self.assertEqual(r11.number(), 1)

    def test_round_number_12(self):
        t = Tournament.objects.get(name='t1')
        r12 = t.round_set.all()[1]
        self.assertEqual(r12.number(), 2)

    def test_round_number_13(self):
        t = Tournament.objects.get(name='t1')
        r13 = t.round_set.all()[2]
        self.assertEqual(r13.number(), 3)

    def test_round_number_14(self):
        t = Tournament.objects.get(name='t1')
        r14 = t.round_set.all()[3]
        self.assertEqual(r14.number(), 4)

    def test_round_number_21(self):
        t = Tournament.objects.get(name='t2')
        r21 = t.round_set.all()[0]
        self.assertEqual(r21.number(), 1)

    def test_round_number_22(self):
        t = Tournament.objects.get(name='t2')
        r22 = t.round_set.all()[1]
        self.assertEqual(r22.number(), 2)

    # Round.leader_str()
    def test_round_leader_str_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.leader_str()

    def test_round_leader_str_finished(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.leader_str()

    # Round.news()
    def test_round_news_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.news()

    # Round.background()
    def test_round_background(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.background()

    def test_round_background_final_year(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        r.background()

    def test_round_background_timed_end(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[1]
        # TODO Validate results
        r.background()

    # Round.clean()
    def test_round_clean_missing_earliest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=t.start_date + HOURS_8,
                  earliest_end_time=t.start_date + HOURS_9)
        self.assertRaises(ValidationError, r.clean)

    def test_round_clean_missing_latest_end(self):
        t = Tournament.objects.get(name='t1')
        s1 = G_SCORING_SYSTEMS[0].name
        r = Round(tournament=t,
                  scoring_system=s1,
                  dias=True,
                  start=t.start_date + HOURS_8,
                  latest_end_time=t.start_date + HOURS_10)
        self.assertRaises(ValidationError, r.clean)

    # Game.scores
    def test_game_scores_invalid(self):
        t, created = Tournament.objects.get_or_create(name='Invalid Tournament',
                                                      start_date=timezone.now(),
                                                      end_date=timezone.now(),
                                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name)
        r = Round.objects.create(tournament=t, scoring_system='Invalid System', dias=True, start=t.start_date)
        g = Game.objects.create(name='gamey', started_at=r.start, the_round=r, the_set=self.set1)
        self.assertRaises(InvalidScoringSystem, g.scores)

    # Game.positions()
    def test_game_positions(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.positions()

    # Game.is_dias()
    def test_game_is_dias(self):
        for g in Game.objects.all():
            self.assertEqual(g.is_dias(), g.the_round.dias)

    # Game.years_played()
    def test_game_years_played_first(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.years_played()[0], 1900)

    def test_game_years_played_last(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.years_played()[-1], 1904)

    def test_game_years_played_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.years_played()[0], 1900)

    # Game.players()
    def test_game_players_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.players()), 7)
        for gp in g.players().values():
            self.assertEqual(len(gp), 1)

    def test_game_players_all(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.players(False)), 7)
        players = g.players(False)
        for power in players.keys():
            if power.abbreviation == u'A':
                self.assertEqual(len(players[power]), 2)
            else:
                self.assertEqual(len(players[power]), 1)

    def test_game_players_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        self.assertEqual(len(g.players()), 7)
        for gp in g.players().values():
            self.assertEqual(len(gp), 0)

    # Game.news()
    def test_game_news(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.news()

    def test_game_news_with_name(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.news(include_game_name=True)

    # Game.background()
    def test_game_background(self):
        g = Game.objects.get(pk=1)
        # TODO Validate results
        g.background()

    # Game.passed_draw()
    def test_game_passed_draw_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIsNone(g.passed_draw())
        dp.delete()

    def test_game_passed_draw_other_game(self):
        t = Tournament.objects.get(name='t1')
        g2 = t.round_numbered(2).game_set.get(name='g13')
        g1 = t.round_numbered(2).game_set.get(name='g14')
        dp = DrawProposal.objects.create(game=g1, year=1905, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIsNone(g2.passed_draw())
        dp.delete()

    def test_game_passed_draw_one(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1905, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(g.passed_draw(), dp)
        dp.delete()

    def test_game_passed_draw_two(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp1 = DrawProposal.objects.create(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        dp2 = DrawProposal.objects.create(game=g, year=1905, season='F', passed=True, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(g.passed_draw(), dp2)
        dp1.delete()
        dp2.delete()

    # Game.board_toppers()
    def test_game_board_toppers_soloed(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        bt = g.board_toppers()
        self.assertEqual(len(bt), 1)
        bt = bt[0]
        self.assertEqual(bt.game, g)
        self.assertEqual(bt.year, 1904)
        self.assertEqual(bt.power, self.germany)
        self.assertEqual(bt.count, 18)

    def test_game_board_toppers_start(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        bt = g.board_toppers()
        self.assertEqual(len(bt), 1)
        bt = bt[0]
        self.assertEqual(bt.game, g)
        self.assertEqual(bt.year, 1900)
        self.assertEqual(bt.power, self.russia)
        self.assertEqual(bt.count, 4)

    # TODO Test board_toppers() returning more than one CentreCount

    # Game.neutrals()
    def test_game_neutrals_1900(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1900), 34 - (6*3 + 4))

    def test_game_neutrals_1901(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1901), 34 - (4*5 + 3*4))

    def test_game_neutrals_1899(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertRaises(InvalidYear, g.neutrals, 1899)

    def test_game_neutrals_1904(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(1904), 0)

    def test_game_neutrals_1905(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertRaises(InvalidYear, g.neutrals, 1905)

    def test_game_neutrals_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.neutrals(), 0)

    def test_game_neutrals_none_default(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.neutrals(), 34 - (6*3 + 4))

    # Game.final_year()
    def test_game_final_year_1904(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.final_year(), 1904)

    def test_game_final_year_none(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertEqual(g.final_year(), 1900)

    # Game.soloer()
    def test_game_soloer_somebody(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(g.soloer().player, Player.objects.get(pk=5))
        self.assertEqual(g.soloer().game, g)

    def test_game_soloer_nobody(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertIsNone(g.soloer())

    # Game.survivors()
    def test_game_survivors(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # survivors() just returns surviving players, regardless of whether they
        # lost to a solo or were excluded from a draw
        self.assertEqual(len(g.survivors()), 6)

    def test_game_survivors_year_1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.survivors(1901)), 7)

    def test_game_survivors_year_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # survivors() just returns surviving players, regardless of whether they
        # lost to a solo or were excluded from a draw
        self.assertEqual(len(g.survivors(1904)), 6)

    def test_game_survivors_invalid_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertEqual(len(g.survivors(1905)), 0)

    # Game.result_str()
    def test_game_result_str_soloed(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        self.assertIn(' won by ', g.result_str())

    def test_game_result_str_in_progress(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        self.assertIsNone(g.result_str())

    def test_game_result_str_passed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertIn('Vote passed ', g.result_str())

    def test_game_result_str_conceded(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=True, proposer=self.england,
                                         power_1=self.england)
        self.assertIn('conceded ', g.result_str())

    def test_game_result_str_failed_draw(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        dp = DrawProposal.objects.create(game=g, year=1901, season='S', passed=False, proposer=self.austria,
                                         power_1=self.austria, power_2=self.england, power_3=self.france,
                                         power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        # Game is still ongoing
        self.assertIsNone(g.result_str())

    # TODO Add test of game that reached fixed endpoint

    # Game.clean()
    def test_game_clean_non_unique_name(self):
        g1 = Game.objects.get(pk=1)
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(4)
        g2 = Game(name='g13',
                  started_at=g1.started_at + HOURS_8,
                  the_round=r,
                  is_finished=False,
                  the_set=g1.the_set)
        self.assertRaises(ValidationError, g2.clean)

    # DrawProposal.draw_size()
    def test_draw_proposal_draw_size_one(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(dp.draw_size(), 1)

    def test_draw_proposal_draw_size_all(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.draw_size(), 7)

    # DrawProposal.powers()
    def test_draw_proposal_powers_one(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(len(dp.powers()), 1)

    def test_draw_proposal_powers_all(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(len(dp.powers()), 7)

    # DrawProposal.power_is_part()
    def test_draw_proposal_power_is_part_one(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria)
        self.assertEqual(dp.power_is_part(self.austria), True)
        self.assertEqual(dp.power_is_part(self.england), False)
        self.assertEqual(dp.power_is_part(self.france), False)
        self.assertEqual(dp.power_is_part(self.germany), False)
        self.assertEqual(dp.power_is_part(self.italy), False)
        self.assertEqual(dp.power_is_part(self.russia), False)
        self.assertEqual(dp.power_is_part(self.turkey), False)

    def test_draw_proposal_power_is_part_all(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.power_is_part(self.austria), True)
        self.assertEqual(dp.power_is_part(self.england), True)
        self.assertEqual(dp.power_is_part(self.france), True)
        self.assertEqual(dp.power_is_part(self.germany), True)
        self.assertEqual(dp.power_is_part(self.italy), True)
        self.assertEqual(dp.power_is_part(self.russia), True)
        self.assertEqual(dp.power_is_part(self.turkey), True)

    # DrawProposal.votes_against()
    def test_draw_proposal_votes_against_none(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1910, season='F', votes_in_favour=7, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.votes_against(), 0)

    def test_draw_proposal_votes_against_some(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        dp = DrawProposal(game=g, year=1910, season='F', votes_in_favour=2, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertEqual(dp.votes_against(), 5)

    def test_draw_proposal_votes_against_exception(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(TypeError, dp.votes_against)

    # DrawProposal.clean()
    def test_draw_proposal_clean_with_duplicates(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.austria)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_clean_with_gap(self):
        g = Game.objects.get(pk=1)
        dp = DrawProposal(game=g, year=1910, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_3=self.england)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_with_dead_powers(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1905, season='S', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_missing_power_dias(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1901, season='F', passed=False, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_too_late(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp = DrawProposal(game=g, year=1903, season='F', passed=True, proposer=self.austria,
                          power_1=self.austria, power_2=self.england, power_3=self.france,
                          power_4=self.germany, power_5=self.italy, power_6=self.russia)
        self.assertRaises(ValidationError, dp.clean)

    def test_draw_proposal_multiple_successful(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        dp1 = DrawProposal.objects.create(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                                          power_1=self.austria, power_2=self.england, power_3=self.france,
                                          power_4=self.germany, power_5=self.italy, power_6=self.russia,
                                          power_7=self.turkey)
        dp2 = DrawProposal(game=g, year=1901, season='F', passed=True, proposer=self.austria,
                           power_1=self.austria, power_2=self.england, power_3=self.france,
                           power_4=self.germany, power_5=self.italy, power_6=self.russia, power_7=self.turkey)
        self.assertRaises(ValidationError, dp2.clean)
        dp1.delete()

    # TODO DrawProposal.clean() with passed not set in a tournament with SECRET draw votes
    # TODO DrawProposal.clean() with votes_in_favour not set in a tournament with COUNTS draw votes
    # TODO DrawProposal.clean() sets passed from votes_in_favour correctly

    # RoundPlayer.clean()
    def test_roundplayer_clean(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_numbered(1)
        p = Player.objects.get(pk=1)
        rp = RoundPlayer(player=p, the_round=r)
        self.assertRaises(ValidationError, rp.clean)

    # GamePlayer.elimination_year()
    def test_gameplayer_elimination_year_replacement(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.filter(power=self.austria).first()
        self.assertEquals(gp.elimination_year(), None)
        gp = g.gameplayer_set.filter(power=self.austria).last()
        self.assertEquals(gp.elimination_year(), 1904)

    def test_gameplayer_elimination_year_not_eliminated(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        gp = g.gameplayer_set.get(power=self.england)
        self.assertEquals(gp.elimination_year(), None)

    # GamePlayer.clean()
    def test_gameplayer_clean_player_not_in_tournament(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        gp = GamePlayer(player=Player.objects.get(pk=1),
                        game=g,
                        power=self.austria)
        self.assertRaises(ValidationError, gp.clean)

    def test_gameplayer_clean_player_missing_last_year(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p = Player.objects.get(pk=1)
        tp = TournamentPlayer(player=p, tournament=t)
        gp = GamePlayer(player=p,
                        game=g,
                        power=self.austria,
                        last_year=1909)
        tp.save()
        self.assertRaises(ValidationError, gp.clean)
        tp.delete()

    def test_gameplayer_clean_player_missing_last_season(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p = Player.objects.get(pk=1)
        tp = TournamentPlayer(player=p, tournament=t)
        gp = GamePlayer(player=p,
                        game=g,
                        power=self.austria,
                        last_season='S')
        tp.save()
        self.assertRaises(ValidationError, gp.clean)
        tp.delete()

    def test_gameplayer_clean_overlap_1(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p1 = Player.objects.get(pk=1)
        p2 = Player.objects.get(pk=2)
        tp1 = TournamentPlayer(player=p1, tournament=t)
        tp2 = TournamentPlayer(player=p2, tournament=t)
        gp1 = GamePlayer(player=p1,
                         game=g,
                         power=self.austria)
        gp2 = GamePlayer(player=p2,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_2(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p1 = Player.objects.get(pk=1)
        p2 = Player.objects.get(pk=2)
        tp1 = TournamentPlayer(player=p1, tournament=t)
        tp2 = TournamentPlayer(player=p2, tournament=t)
        gp1 = GamePlayer(player=p1,
                         game=g,
                         power=self.austria,
                         last_year=1902,
                         last_season='S')
        gp2 = GamePlayer(player=p2,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_3(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p1 = Player.objects.get(pk=1)
        p2 = Player.objects.get(pk=2)
        tp1 = TournamentPlayer(player=p1, tournament=t)
        tp2 = TournamentPlayer(player=p2, tournament=t)
        gp1 = GamePlayer(player=p1,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=p2,
                         game=g,
                         power=self.austria,
                         last_year=1902,
                         last_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_4(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p1 = Player.objects.get(pk=1)
        p2 = Player.objects.get(pk=2)
        tp1 = TournamentPlayer(player=p1, tournament=t)
        tp2 = TournamentPlayer(player=p2, tournament=t)
        gp1 = GamePlayer(player=p1,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=p2,
                         game=g,
                         power=self.austria)
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    def test_gameplayer_clean_overlap_5(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(2).game_set.get(name='g13')
        p1 = Player.objects.get(pk=1)
        p2 = Player.objects.get(pk=2)
        tp1 = TournamentPlayer(player=p1, tournament=t)
        tp2 = TournamentPlayer(player=p2, tournament=t)
        gp1 = GamePlayer(player=p1,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        gp2 = GamePlayer(player=p2,
                         game=g,
                         power=self.austria,
                         first_year=1902,
                         first_season='S')
        tp1.save()
        tp2.save()
        gp1.clean()
        gp1.save()
        self.assertRaises(ValidationError, gp2.clean)
        gp1.delete()
        tp2.delete()
        tp1.delete()

    # GameImage.turn_str()
    def test_gameimage_turn_str(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi = GameImage.objects.get(game=g)
        self.assertEqual(gi.turn_str(), 'S1901M')

    # GameImage.clean()
    def test_gameimage_clean(self):
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        gi1 = GameImage.objects.get(game=g)
        gi2 = GameImage(game=g, year=1902, season=SPRING, phase=ADJUSTMENTS, image=gi1.image)
        self.assertRaises(ValidationError, gi2.clean)

    # CentreCount.clean()
    def test_centrecount_clean_past_final_year(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc = CentreCount(power=self.austria, game=g, year=1908, count=7)
        self.assertRaises(ValidationError, cc.clean)

    def test_centrecount_clean_up_from_zero(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc1 = CentreCount(power=self.austria, game=g, year=1902, count=0)
        cc2 = CentreCount(power=self.austria, game=g, year=1903, count=1)
        cc1.save()
        self.assertRaises(ValidationError, cc2.clean)
        cc1.delete()

    def test_centrecount_clean_more_than_double(self):
        t = Tournament.objects.get(name='t3')
        g = t.round_numbered(1).game_set.get(name='g31')
        cc1 = CentreCount(power=self.austria, game=g, year=1902, count=5)
        cc2 = CentreCount(power=self.austria, game=g, year=1903, count=11)
        cc1.save()
        self.assertRaises(ValidationError, cc2.clean)
        cc1.delete()

    # Wikipedia_Background.titles() gets tested implicitly

    # WDD_Background mostly gets tested implictly. Explicitly test invalid wdd ids
    # WDD_Background.wdd_name()
    def test_wdd_background_wdd_name_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.wdd_name)

    # WDD_Background.finishes()
    def test_wdd_background_finishes_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.finishes)

    # WDD_Background.tournaments()
    def test_wdd_background_tournaments_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.tournaments)

    # WDD_Background.boards()
    def test_wdd_background_boards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.boards)

    # WDD_Background.awards()
    def test_wdd_background_awards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.awards)

    # WDD_Background.rankings()
    def test_wdd_background_awards_invalid(self):
        b = WDD_Background(INVALID_WDD_ID)
        self.assertRaises(InvalidWDDId, b.rankings)

    # PlayerRanking.national_str()
    def test_playerranking_national_str(self):
        pr = PlayerRanking.objects.get(pk=1)
        # TODO Validate results
        pr.national_str()
