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

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import DrawSecrecy
from tournament.models import Tournament, Round, Game
from tournament.models import SupplyCentreOwnership, CentreCount
from tournament.models import TournamentPlayer, RoundPlayer, GamePlayer
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.players import Player

from tournament.news import _tournament_news, _round_leader_str, _round_news, _game_news
from tournament.news import news, MASK_ALL_NEWS

HOURS_8 = timedelta(hours=8)
HOURS_9 = timedelta(hours=9)
HOURS_10 = timedelta(hours=10)
HOURS_16 = timedelta(hours=16)
HOURS_24 = timedelta(hours=24)

class NewsTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    @classmethod
    def setUpTestData(cls):
        # TODO This was copied from test_models. A lot likely isn't needed here.
        cls.set1 = GameSet.objects.get(name='Avalon Hill')
        cls.set2 = GameSet.objects.get(name='Gibsons')

        s1 = G_SCORING_SYSTEMS[0].name

        now = timezone.now()

        t1 = Tournament.objects.create(name='t1',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.SECRET)
        t3 = Tournament.objects.create(name='t3',
                                       start_date=now,
                                       end_date=now,
                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                       tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                       draw_secrecy=DrawSecrecy.COUNTS)

        # Add Rounds to t1
        r11 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date)
        r12 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date + HOURS_8)
        r13 = Round.objects.create(tournament=t1,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t1.start_date + HOURS_16)
        Round.objects.create(tournament=t1,
                             scoring_system=s1,
                             dias=True,
                             start=t1.start_date + HOURS_24)
        # Add Rounds to t3
        r31 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t3.start_date,
                                   final_year=1907)
        r32 = Round.objects.create(tournament=t3,
                                   scoring_system=s1,
                                   dias=True,
                                   start=t3.start_date + HOURS_8,
                                   earliest_end_time=t3.start_date + HOURS_8,
                                   latest_end_time=t3.start_date + HOURS_9)

        # Add Games to r11
        g11 = Game.objects.create(name='g11',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        g12 = Game.objects.create(name='g12',
                                  started_at=r11.start,
                                  the_round=r11,
                                  the_set=cls.set1)
        # Add Games to r12
        g13 = Game.objects.create(name='g13',
                                  started_at=r12.start,
                                  the_round=r12,
                                  is_finished=True,
                                  the_set=cls.set1)
        g14 = Game.objects.create(name='g14',
                                  started_at=r12.start,
                                  the_round=r12,
                                  the_set=cls.set1)
        # Add Games to r13
        Game.objects.create(name='g15',
                            started_at=r13.start,
                            the_round=r13,
                            is_finished=True,
                            the_set=cls.set1)
        Game.objects.create(name='g16',
                            started_at=r13.start,
                            the_round=r13,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r31
        Game.objects.create(name='g31',
                            started_at=r31.start,
                            the_round=r31,
                            is_finished=True,
                            the_set=cls.set1)
        # Add Games to r32
        Game.objects.create(name='g32',
                            started_at=r32.start,
                            the_round=r32,
                            is_finished=True,
                            the_set=cls.set1)

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # Add CentreCounts to g11
        CentreCount.objects.create(power=cls.austria, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1901, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1901, count=4)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1901, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1901, count=4)

        # Eliminate Italy in 1903
        CentreCount.objects.create(power=cls.austria, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.england, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.france, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1903, count=10)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1903, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1903, count=5)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1903, count=4)

        # Solo victory for Germany in 1904
        CentreCount.objects.create(power=cls.austria, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.england, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.france, game=g11, year=1904, count=4)
        CentreCount.objects.create(power=cls.germany, game=g11, year=1904, count=18)
        CentreCount.objects.create(power=cls.italy, game=g11, year=1904, count=0)
        CentreCount.objects.create(power=cls.russia, game=g11, year=1904, count=3)
        CentreCount.objects.create(power=cls.turkey, game=g11, year=1904, count=5)

        # Create some players
        # Avoid hitting the WDD by not providing a WDD id
        cls.p1 = Player.objects.create(first_name='Abbey', last_name='Brown')
        cls.p2 = Player.objects.create(first_name='Charles', last_name='Dog')
        cls.p3 = Player.objects.create(first_name='Ethel', last_name='Frankenstein')
        cls.p4 = Player.objects.create(first_name='George', last_name='Hotel')
        cls.p5 = Player.objects.create(first_name='Iris', last_name='Jackson')
        cls.p6 = Player.objects.create(first_name='Kevin', last_name='Lame')
        cls.p7 = Player.objects.create(first_name='Michelle', last_name='Nobody')
        cls.p8 = Player.objects.create(first_name='Owen', last_name='Pennies')
        # These last two are deliberately not in any tournaments
        cls.p9 = Player.objects.create(first_name='Queenie', last_name='Radiation')
        cls.p10 = Player.objects.create(first_name='Sebastian', last_name='Twinkie')

        # Tournament.news() will call Game.news() for all games in the current round,
        # which will need a player for every country
        # TODO These should really error out with no corresponding RoundPlayer. I guess clean() is not called ?
        # Add GamePlayers to g11
        GamePlayer.objects.create(player=cls.p1,
                                  game=g11,
                                  power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=g11, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g11, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g11, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g11, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g11, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g11, power=cls.turkey)
        # Add GamePlayers to g12
        GamePlayer.objects.create(player=cls.p7, game=g12, power=cls.austria)
        GamePlayer.objects.create(player=cls.p6, game=g12, power=cls.england)
        GamePlayer.objects.create(player=cls.p5, game=g12, power=cls.france)
        GamePlayer.objects.create(player=cls.p4, game=g12, power=cls.germany)
        GamePlayer.objects.create(player=cls.p3, game=g12, power=cls.italy)
        GamePlayer.objects.create(player=cls.p2, game=g12, power=cls.russia)
        GamePlayer.objects.create(player=cls.p1, game=g12, power=cls.turkey)
        # Add GamePlayers to g13
        GamePlayer.objects.create(player=cls.p1,
                                  game=g13,
                                  power=cls.austria)
        GamePlayer.objects.create(player=cls.p3, game=g13, power=cls.england)
        GamePlayer.objects.create(player=cls.p4, game=g13, power=cls.france)
        GamePlayer.objects.create(player=cls.p5, game=g13, power=cls.germany)
        GamePlayer.objects.create(player=cls.p6, game=g13, power=cls.italy)
        GamePlayer.objects.create(player=cls.p7, game=g13, power=cls.russia)
        GamePlayer.objects.create(player=cls.p8, game=g13, power=cls.turkey)
        # Add GamePlayers to g14
        GamePlayer.objects.create(player=cls.p7, game=g14, power=cls.austria)
        GamePlayer.objects.create(player=cls.p6, game=g14, power=cls.england)
        GamePlayer.objects.create(player=cls.p5, game=g14, power=cls.france)
        GamePlayer.objects.create(player=cls.p4, game=g14, power=cls.germany)
        GamePlayer.objects.create(player=cls.p3, game=g14, power=cls.italy)
        GamePlayer.objects.create(player=cls.p2, game=g14, power=cls.russia)
        GamePlayer.objects.create(player=cls.p1, game=g14, power=cls.turkey)
        # And the corresponding RoundPlayers
        RoundPlayer.objects.create(player=cls.p1, the_round=r11)
        RoundPlayer.objects.create(player=cls.p2, the_round=r11)
        RoundPlayer.objects.create(player=cls.p3, the_round=r11)
        RoundPlayer.objects.create(player=cls.p4, the_round=r11)
        RoundPlayer.objects.create(player=cls.p5, the_round=r11)
        RoundPlayer.objects.create(player=cls.p6, the_round=r11)
        RoundPlayer.objects.create(player=cls.p7, the_round=r11)
        RoundPlayer.objects.create(player=cls.p8, the_round=r11)
        RoundPlayer.objects.create(player=cls.p1, the_round=r12)
        RoundPlayer.objects.create(player=cls.p2, the_round=r12)
        RoundPlayer.objects.create(player=cls.p3, the_round=r12)
        RoundPlayer.objects.create(player=cls.p4, the_round=r12)
        RoundPlayer.objects.create(player=cls.p5, the_round=r12)
        RoundPlayer.objects.create(player=cls.p6, the_round=r12)
        RoundPlayer.objects.create(player=cls.p7, the_round=r12)
        RoundPlayer.objects.create(player=cls.p8, the_round=r12)
        # And TournamentPlayers
        TournamentPlayer.objects.create(player=cls.p1, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p2, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p3, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p4, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p5, tournament=t1, unranked=True)
        TournamentPlayer.objects.create(player=cls.p6, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p7, tournament=t1)
        TournamentPlayer.objects.create(player=cls.p8, tournament=t1)

        # Add a TournamentPlayer to t3
        TournamentPlayer.objects.create(player=cls.p5, tournament=t3, score=147.3)
        # Add a RoundPlayer to r31
        RoundPlayer.objects.create(player=cls.p5, the_round=r31, score=0.0)
        # Add a RoundPlayer to r32
        RoundPlayer.objects.create(player=cls.p5, the_round=r32, score=47.3)


    # _tournament_news()
    def test_tournament_news_in_progress(self):
        t = Tournament.objects.get(name='t1')
        # TODO Validate results
        _tournament_news(t)

    def test_tournament_news_ended(self):
        t = Tournament.objects.get(name='t3')
        # TODO Validate results
        _tournament_news(t)

    # _round_leader_str()
    def test_round_leader_str_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        _round_leader_str(r)

    def test_round_leader_str_finished(self):
        t = Tournament.objects.get(name='t3')
        r = t.round_set.all()[0]
        # TODO Validate results
        _round_leader_str(r)

    # _round_news()
    def test_round_news_unfinished(self):
        t = Tournament.objects.get(name='t1')
        r = t.round_set.all()[0]
        # TODO Validate results
        _round_news(r)

    # _game_news()
    def test_game_news(self):
        g = Game.objects.first()
        # TODO Validate results
        _game_news(g)

    def test_game_news_with_name(self):
        g = Game.objects.first()
        # TODO Validate results
        _game_news(g, include_game_name=True)

    def test_game_news_mask(self):
        g = Game.objects.first()
        # Test each mask bit individually
        mask = 1
        while mask <= MASK_ALL_NEWS:
            with self.subTest(mask=mask):
                # TODO Validate results
                _game_news(g, mask=mask)
            mask *= 2

    def test_game_news_year_too_late(self):
        g = Game.objects.first()
        _game_news(g, for_year=1920)

    def test_game_news_without_ownerships(self):
        # Test with no SupplyCentreOwnership objects
        # We need a year with CentreCounts but no SupplyCentreOwnerships,
        # where the previous year *does* have SupplyCentreOwnerships.
        # 1900 always has the latter.
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g11')
        # TODO Validate results
        _game_news(g, for_year=1901)

    def test_game_news_sc_gains_losses(self):
        # Austria lost three, flagging it as interesting
        # France gained three, making it interesting
        # Germany gained two and lost two, making it interesting
        # Italy gained three, and so is interesting
        # The rest are uninteresting, having only gained one or two
        # Both neutral dots and owned dots make powers interesting
        test_data = {
                     SupplyCentre.objects.get(abbreviation='Lon'): self.england,
                     SupplyCentre.objects.get(abbreviation='Lvp'): self.england,
                     SupplyCentre.objects.get(abbreviation='Edi'): self.england,
                     SupplyCentre.objects.get(abbreviation='Nwy'): self.england,
                     SupplyCentre.objects.get(abbreviation='Bre'): self.france,
                     SupplyCentre.objects.get(abbreviation='Par'): self.france,
                     SupplyCentre.objects.get(abbreviation='Mar'): self.france,
                     SupplyCentre.objects.get(abbreviation='Spa'): self.france,
                     SupplyCentre.objects.get(abbreviation='Por'): self.france,
                     SupplyCentre.objects.get(abbreviation='Mun'): self.france,
                     SupplyCentre.objects.get(abbreviation='Den'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Hol'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Kie'): self.germany,
                     SupplyCentre.objects.get(abbreviation='Ven'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Rom'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Nap'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Tri'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Vie'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Gre'): self.italy,
                     SupplyCentre.objects.get(abbreviation='Ber'): self.russia,
                     SupplyCentre.objects.get(abbreviation='StP'): self.russia,
                     SupplyCentre.objects.get(abbreviation='War'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Mos'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Sev'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Bud'): self.russia,
                     SupplyCentre.objects.get(abbreviation='Con'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Ank'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Smy'): self.turkey,
                     SupplyCentre.objects.get(abbreviation='Bul'): self.turkey,
                    }
        t = Tournament.objects.get(name='t1')
        g = t.round_numbered(1).game_set.get(name='g12')
        # Add some SC ownerships that give us gains and losses
        for k,v in test_data.items():
            sco = SupplyCentreOwnership(sc=k, owner=v, year=1901, game=g)
            sco.save()
        g.create_or_update_sc_counts_from_ownerships(1901)
        # TODO Validate the result
        _game_news(g)
        # Remove everything we added to the database
        for sco in g.supplycentreownership_set.filter(year=1901):
            sco.delete()
        for sc in g.centrecount_set.filter(year=1901):
            sc.delete()

    # news()
    def test_news_for_tournament(self):
        t = Tournament.objects.first()
        # TODO Validate results
        news(t)

    def test_news_for_round(self):
        r = Round.objects.first()
        # TODO Validate results
        news(r)

    def test_news_for_game(self):
        g = Game.objects.first()
        # TODO Validate results
        news(g)
