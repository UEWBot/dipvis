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

import uuid

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy import GameSet, GreatPower
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, TournamentPlayer
from tournament.models import Round, RoundPlayer, Game, GamePlayer
from tournament.models import CentreCount, DrawProposal
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import G_SCORING_SYSTEMS
from tournament.players import Player

class TournamentViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # A regular user with no special permissions or ownership
        cls.USERNAME1 = 'regular'
        cls.PWORD1 = 'CleverPassword'
        u1 = User.objects.create_user(username=cls.USERNAME1, password=cls.PWORD1)
        u1.save()

        # A superuser
        cls.USERNAME2 = 'superuser'
        cls.PWORD2 = 'L33tPw0rd'
        u2 = User.objects.create_user(username=cls.USERNAME2,
                                      password=cls.PWORD2,
                                      is_superuser=True)
        u2.save()

        # A user who is a manager of a tournament (t2)
        # We give managers the appropriate permissions
        cls.USERNAME3 = 'manager'
        cls.PWORD3 = 'MyPassword'
        perm = Permission.objects.get(name='Can change round player')
        u3 = User.objects.create_user(username=cls.USERNAME3,
                                      password=cls.PWORD3)
        u3.user_permissions.add(perm)
        u3.save()

        # Some Players
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
                                   last_name='Heffalump')
        p9 = Player.objects.create(first_name='Iris',
                                   last_name='Ignoramus')
        p10 = Player.objects.create(first_name='Jake',
                                    last_name='Jalopy')

        now = timezone.now()
        # Published Tournament, so it's visible to all
        # Ongoing, one round
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True)
        Round.objects.create(tournament=cls.t1,
                             start=cls.t1.start_date,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True)
        # Pre-generate a UUID for player prefs
        cls.tp11 = TournamentPlayer.objects.create(player=p1,
                                                   tournament=cls.t1,
                                                   uuid_str=str(uuid.uuid4()))
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t1)

        # Unpublished Tournament, with a manager (u3)
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=False)
        cls.r21 = Round.objects.create(tournament=cls.t2,
                                       start=cls.t2.start_date,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=False)
        g21 = Game.objects.create(name='Game1',
                                  the_round=cls.r21,
                                  started_at=cls.r21.start,
                                  the_set=GameSet.objects.first(),
                                  is_finished=False,
                                  is_top_board=True)
        tp = TournamentPlayer.objects.create(player=p1,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p4,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p5,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p6,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p7,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p8,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p9,
                                             tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p10,
                                             tournament=cls.t2)
        RoundPlayer.objects.create(player=p1, the_round=cls.r21)
        RoundPlayer.objects.create(player=p3, the_round=cls.r21)
        RoundPlayer.objects.create(player=p4, the_round=cls.r21)
        RoundPlayer.objects.create(player=p5, the_round=cls.r21)
        RoundPlayer.objects.create(player=p6, the_round=cls.r21)
        RoundPlayer.objects.create(player=p7, the_round=cls.r21)
        RoundPlayer.objects.create(player=p8, the_round=cls.r21)
        RoundPlayer.objects.create(player=p9, the_round=cls.r21)
        RoundPlayer.objects.create(player=p10, the_round=cls.r21)
        GamePlayer.objects.create(player=p1, game=g21, power=cls.austria)
        GamePlayer.objects.create(player=p3, game=g21, power=cls.england)
        GamePlayer.objects.create(player=p4, game=g21, power=cls.france)
        GamePlayer.objects.create(player=p5, game=g21, power=cls.germany)
        GamePlayer.objects.create(player=p6, game=g21, power=cls.italy)
        GamePlayer.objects.create(player=p7, game=g21, power=cls.russia)
        GamePlayer.objects.create(player=p8, game=g21, power=cls.turkey)
        CentreCount.objects.create(power=cls.austria, game=g21, year=1901, count=0)
        CentreCount.objects.create(power=cls.england, game=g21, year=1901, count=4)
        CentreCount.objects.create(power=cls.france, game=g21, year=1901, count=5)
        CentreCount.objects.create(power=cls.germany, game=g21, year=1901, count=5)
        CentreCount.objects.create(power=cls.italy, game=g21, year=1901, count=6)
        CentreCount.objects.create(power=cls.russia, game=g21, year=1901, count=7)
        CentreCount.objects.create(power=cls.turkey, game=g21, year=1901, count=5)
        cls.t2.managers.add(u3)

        # Unpublished Tournament, without a manager
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=False)

        # Published Tournament, without a manager, but not editable
        # One round, tournament complete
        cls.t4 = Tournament.objects.create(name='t4',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True,
                                           editable=False)
        cls.r41 = Round.objects.create(tournament=cls.t4,
                                       start=cls.t4.start_date,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=False)
        g41 = Game.objects.create(name='Game1',
                                  the_round=cls.r41,
                                  started_at=cls.r41.start,
                                  the_set=GameSet.objects.first(),
                                  is_finished=True)
        g42 = Game.objects.create(name='Game2',
                                  the_round=cls.r41,
                                  started_at=cls.r41.start,
                                  the_set=GameSet.objects.first(),
                                  is_finished=True)
        tp = TournamentPlayer.objects.create(player=p1,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p4,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p5,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p6,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p7,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p8,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p9,
                                             tournament=cls.t4)
        tp = TournamentPlayer.objects.create(player=p10,
                                             tournament=cls.t4)
        RoundPlayer.objects.create(player=p1, the_round=cls.r41)
        RoundPlayer.objects.create(player=p3, the_round=cls.r41)
        RoundPlayer.objects.create(player=p4, the_round=cls.r41)
        RoundPlayer.objects.create(player=p5, the_round=cls.r41)
        RoundPlayer.objects.create(player=p6, the_round=cls.r41)
        RoundPlayer.objects.create(player=p7, the_round=cls.r41)
        RoundPlayer.objects.create(player=p8, the_round=cls.r41)
        RoundPlayer.objects.create(player=p9, the_round=cls.r41)
        RoundPlayer.objects.create(player=p10, the_round=cls.r41)
        GamePlayer.objects.create(player=p1, game=g41, power=cls.austria)
        GamePlayer.objects.create(player=p3, game=g41, power=cls.england)
        GamePlayer.objects.create(player=p4, game=g41, power=cls.france)
        GamePlayer.objects.create(player=p5, game=g41, power=cls.germany)
        GamePlayer.objects.create(player=p6, game=g41, power=cls.italy)
        GamePlayer.objects.create(player=p7, game=g41, power=cls.russia)
        GamePlayer.objects.create(player=p8, game=g41, power=cls.turkey)
        GamePlayer.objects.create(player=p10, game=g42, power=cls.austria)
        GamePlayer.objects.create(player=p9, game=g42, power=cls.england)
        GamePlayer.objects.create(player=p8, game=g42, power=cls.france)
        GamePlayer.objects.create(player=p7, game=g42, power=cls.germany)
        GamePlayer.objects.create(player=p6, game=g42, power=cls.italy)
        GamePlayer.objects.create(player=p5, game=g42, power=cls.russia)
        GamePlayer.objects.create(player=p4, game=g42, power=cls.turkey)
        # Add CentreCounts for g41. Draw vote passed. A power on 1 SC, a power eliminated
        CentreCount.objects.create(power=cls.austria, game=g41, year=1901, count=0)
        CentreCount.objects.create(power=cls.england, game=g41, year=1901, count=4)
        CentreCount.objects.create(power=cls.france, game=g41, year=1901, count=5)
        CentreCount.objects.create(power=cls.germany, game=g41, year=1901, count=5)
        CentreCount.objects.create(power=cls.italy, game=g41, year=1901, count=6)
        CentreCount.objects.create(power=cls.russia, game=g41, year=1901, count=7)
        CentreCount.objects.create(power=cls.turkey, game=g41, year=1901, count=5)
        CentreCount.objects.create(power=cls.austria, game=g41, year=1902, count=0)
        CentreCount.objects.create(power=cls.england, game=g41, year=1902, count=7)
        CentreCount.objects.create(power=cls.france, game=g41, year=1902, count=8)
        CentreCount.objects.create(power=cls.germany, game=g41, year=1902, count=1)
        CentreCount.objects.create(power=cls.italy, game=g41, year=1902, count=5)
        CentreCount.objects.create(power=cls.russia, game=g41, year=1902, count=8)
        CentreCount.objects.create(power=cls.turkey, game=g41, year=1902, count=5)
        DrawProposal.objects.create(game=g41,
                                    year=1903,
                                    season='S',
                                    passed=True,
                                    proposer=cls.france,
                                    power_1=cls.england,
                                    power_2=cls.france,
                                    power_3=cls.italy,
                                    power_4=cls.russia,
                                    power_5=cls.turkey)
        # Add CentreCounts for g42 - solo for Russia. Austria eliminated
        CentreCount.objects.create(power=cls.austria, game=g42, year=1901, count=4)
        CentreCount.objects.create(power=cls.england, game=g42, year=1901, count=4)
        CentreCount.objects.create(power=cls.france, game=g42, year=1901, count=5)
        CentreCount.objects.create(power=cls.germany, game=g42, year=1901, count=5)
        CentreCount.objects.create(power=cls.italy, game=g42, year=1901, count=4)
        CentreCount.objects.create(power=cls.russia, game=g42, year=1901, count=8)
        CentreCount.objects.create(power=cls.turkey, game=g42, year=1901, count=4)
        CentreCount.objects.create(power=cls.austria, game=g42, year=1902, count=2)
        CentreCount.objects.create(power=cls.england, game=g42, year=1902, count=3)
        CentreCount.objects.create(power=cls.france, game=g42, year=1902, count=5)
        CentreCount.objects.create(power=cls.germany, game=g42, year=1902, count=4)
        CentreCount.objects.create(power=cls.italy, game=g42, year=1902, count=4)
        CentreCount.objects.create(power=cls.russia, game=g42, year=1902, count=13)
        CentreCount.objects.create(power=cls.turkey, game=g42, year=1902, count=3)
        CentreCount.objects.create(power=cls.austria, game=g42, year=1903, count=0)
        CentreCount.objects.create(power=cls.england, game=g42, year=1903, count=2)
        CentreCount.objects.create(power=cls.france, game=g42, year=1903, count=5)
        CentreCount.objects.create(power=cls.germany, game=g42, year=1903, count=3)
        CentreCount.objects.create(power=cls.italy, game=g42, year=1903, count=4)
        CentreCount.objects.create(power=cls.russia, game=g42, year=1903, count=19)
        CentreCount.objects.create(power=cls.turkey, game=g42, year=1903, count=1)

        # Hopefully this isn't the pk for any Tournament
        cls.INVALID_T_PK = 99999

        # Published Tournament, so it's visible to all
        # Ongoing, one round that has started
        cls.t5 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True)
        cls.r51 = Round.objects.create(tournament=cls.t5,
                                       start=cls.t5.start_date,
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       dias=True)
        # Pre-generate a UUID for player prefs
        cls.tp51 = TournamentPlayer.objects.create(player=p1,
                                                   tournament=cls.t5,
                                                   uuid_str=str(uuid.uuid4()))
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t5)
        g = Game.objects.create(name='Game1',
                                the_round=cls.r51,
                                started_at=cls.r51.start,
                                the_set=GameSet.objects.first(),
                                is_finished=False)

    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Check that we get the right tournaments listed
        self.assertIn(b't1', response.content) # Published
        self.assertNotIn(b't2', response.content) # Unpublished
        self.assertNotIn(b't3', response.content) # Unpublished
        self.assertIn(b't4', response.content) # Published

    def test_index_superuser(self):
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Check that we get the right tournaments listed
        self.assertIn(b't1', response.content) # Published
        self.assertIn(b't2', response.content) # Unpublished
        self.assertIn(b't3', response.content) # Unpublished
        self.assertIn(b't4', response.content) # Published

    def test_index_manager(self):
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Check that we get the right tournaments listed
        self.assertIn(b't1', response.content) # Published
        self.assertIn(b't2', response.content) # Unpublished, manager
        self.assertNotIn(b't3', response.content) # Unpublished
        self.assertIn(b't4', response.content) # Published

    def test_detail_invalid_tournament(self):
        response = self.client.get(reverse('tournament_detail', args=(self.INVALID_T_PK,)))
        self.assertEqual(response.status_code, 404)

    def test_detail_manager_wrong_tournament(self):
        # A manager can't see an unpublished tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a published tournament
        response = self.client.get(reverse('tournament_detail', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_regular_user(self):
        # Any user can see a published tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('tournament_detail', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_superuser(self):
        # A superuser can see any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_detail', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_detail_manager(self):
        # A manager see their unpublished tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_framesets(self):
        response = self.client.get(reverse('framesets', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_3x3(self):
        response = self.client.get(reverse('frameset_3x3', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_top_board(self):
        response = self.client.get(reverse('frameset_top_board', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_2x2(self):
        response = self.client.get(reverse('frameset_2x2', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_frameset_1x1(self):
        response = self.client.get(reverse('frameset_1x1', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_views(self):
        response = self.client.get(reverse('tournament_views', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('tournament_overview', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_overview2(self):
        response = self.client.get(reverse('tournament_overview_2', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_overview3(self):
        response = self.client.get(reverse('tournament_overview_3', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_scores(self):
        # Scores page for an in-progress Tournament
        response = self.client.get(reverse('tournament_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current Scores', response.content)

    def test_scores_completed(self):
        # Scores page for a completed Tournament
        response = self.client.get(reverse('tournament_scores', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Final Scores', response.content)

    def test_scores_refresh(self):
        response = self.client.get(reverse('tournament_scores_refresh', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_game_results(self):
        response = self.client.get(reverse('tournament_game_results', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_results_ongoing(self):
        # Ongoing tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_game_results', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries(self):
        response = self.client.get(reverse('tournament_best_countries', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_best_countries_refresh(self):
        response = self.client.get(reverse('tournament_best_countries_refresh', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_enter_scores_not_logged_in(self):
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_enter_scores_regular_user(self):
        # A regular user can't enter scores for any old tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_enter_scores_manager_wrong_tournament(self):
        # A manager can't enter scores for a tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_archived(self):
        # Nobody can enter scores for an archived tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_superuser(self):
        # A superuser can enter scores for any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_manager(self):
        # A manager can enter scores for their tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_roll_call_not_logged_in(self):
        response = self.client.get(reverse('roll_call', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_current_round(self):
        response = self.client.get(reverse('tournament_round', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_current_round_completed(self):
        # "Current round" for a tournament that has ended
        response = self.client.get(reverse('tournament_round', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_game_image_not_logged_in(self):
        response = self.client.get(reverse('add_game_image', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_news(self):
        response = self.client.get(reverse('tournament_news', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('tournament_news_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_background(self):
        response = self.client.get(reverse('tournament_background', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('tournament_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_background_ticker(self):
        response = self.client.get(reverse('tournament_background_ticker', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta http-equiv="refresh"', response.content)

    def test_rounds(self):
        response = self.client.get(reverse('round_index', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_prefs_not_logged_in(self):
        response = self.client.get(reverse('enter_prefs', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_upload_prefs_not_logged_in(self):
        response = self.client.get(reverse('upload_prefs', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 302)

    def test_prefs_csv(self):
        response = self.client.get(reverse('prefs_csv', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs(self):
        response = self.client.get(reverse('player_prefs', args=(self.t1.pk, self.tp11.uuid_str)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs_invalid_uuid(self):
        # Should get a 404 error if the UUID doesn't correspond to a TournamentPlayer
        response = self.client.get(reverse('player_prefs', args=(self.t1.pk, uuid.uuid4())))
        self.assertEqual(response.status_code, 404)

    def test_player_prefs_too_late(self):
        # Should get a 404 error if the final round has started
        response = self.client.get(reverse('player_prefs', args=(self.t5.pk, self.tp51.uuid_str)))
        self.assertEqual(response.status_code, 404)

    def test_tournament_players(self):
        response = self.client.get(reverse('tournament_players', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)
