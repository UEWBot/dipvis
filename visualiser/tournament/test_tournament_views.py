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
from urllib.parse import urlencode

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.models import Award, DrawSecrecy, PowerAssignMethods
from tournament.models import Tournament, TournamentPlayer, SeederBias
from tournament.models import Preference, Round, RoundPlayer, Game, GamePlayer
from tournament.models import CentreCount, DrawProposal
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import G_SCORING_SYSTEMS
from tournament.models import Seasons
from tournament.players import Player

@override_settings(HOSTNAME='example.com')
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
        cls.u3 = User.objects.create_user(username=cls.USERNAME3,
                                          password=cls.PWORD3)
        perm = Permission.objects.get(name='Can change round player')
        cls.u3.user_permissions.add(perm)
        perm = Permission.objects.get(name='Can add preference')
        cls.u3.user_permissions.add(perm)
        perm = Permission.objects.get(name='Can add tournament player')
        cls.u3.user_permissions.add(perm)
        cls.u3.save()

        # Some Players
        cls.p1 = Player.objects.create(first_name='Angela',
                                       last_name='Ampersand',
                                       email='a.ampersand@example.com')
        cls.p2 = Player.objects.create(first_name='Bobby',
                                       last_name='Bandersnatch')
        # One with a really long name
        p3 = Player.objects.create(first_name='Cassandra'.ljust(Player._meta.get_field('first_name').max_length,'.'),
                                   last_name='Cucumber'.ljust(Player._meta.get_field('last_name').max_length,'.'))
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
        # Player that is also u3 (manager of t2)
        cls.p11 = Player.objects.create(first_name='Kathryn',
                                        last_name='Krispy',
                                        user = cls.u3)

        # A few awards
        cls.a1 = Award.objects.create(name='Longest Hair',
                                      description='Player whose hair is longer than the rest')
        cls.a2 = Award.objects.create(name='Greenest Shirt',
                                      description='Player with the greenest shirt')
        cls.a3 = Award.objects.create(name='Best Italy',
                                      description='Player who got the best result playing Italy',
                                      power=cls.italy)
        # This one should not be associated with any Tournament
        cls.a4 = Award.objects.create(name='Whitest Teeth',
                                      description='Player whose teeth are whiter than the rest')

        now = timezone.now()
        # Published Tournament, so it's visible to all
        # Ongoing, one round
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=True)
        cls.t1.awards.add(cls.a1)
        cls.t1.awards.add(cls.a2)
        cls.t1.awards.add(cls.a3)
        cls.t1.save()
        Round.objects.create(tournament=cls.t1,
                             start=cls.t1.start_date,
                             scoring_system=G_SCORING_SYSTEMS[0].name,
                             dias=True)
        # Pre-generate a UUID for player prefs
        cls.tp11 = TournamentPlayer.objects.create(player=cls.p1,
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
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           power_assignment=PowerAssignMethods.PREFERENCES,
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
        tp = TournamentPlayer.objects.create(player=cls.p1,
                                             tournament=cls.t2)
        # Explicitly call save() to generate a UUID
        tp.save()
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
        cls.tp29 = TournamentPlayer.objects.create(player=p9,
                                                   tournament=cls.t2)
        tp = TournamentPlayer.objects.create(player=p10,
                                             tournament=cls.t2)
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r21)
        RoundPlayer.objects.create(player=p3, the_round=cls.r21)
        RoundPlayer.objects.create(player=p4, the_round=cls.r21)
        RoundPlayer.objects.create(player=p5, the_round=cls.r21)
        RoundPlayer.objects.create(player=p6, the_round=cls.r21)
        RoundPlayer.objects.create(player=p7, the_round=cls.r21)
        RoundPlayer.objects.create(player=p8, the_round=cls.r21)
        RoundPlayer.objects.create(player=p9, the_round=cls.r21)
        RoundPlayer.objects.create(player=p10, the_round=cls.r21)
        GamePlayer.objects.create(player=cls.p1, game=g21, power=cls.austria)
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
        cls.t2.managers.add(cls.u3)

        # Unpublished Tournament, without a manager
        cls.t3 = Tournament.objects.create(name='t3',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=False)

        # Published Tournament, without a manager, but not editable
        # One round, tournament complete
        cls.t4 = Tournament.objects.create(name='t4',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
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
        cls.tp41 = TournamentPlayer.objects.create(player=cls.p1,
                                                   tournament=cls.t4,
                                                   uuid_str=str(uuid.uuid4()))
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
        RoundPlayer.objects.create(player=cls.p1, the_round=cls.r41)
        RoundPlayer.objects.create(player=p3, the_round=cls.r41)
        RoundPlayer.objects.create(player=p4, the_round=cls.r41)
        RoundPlayer.objects.create(player=p5, the_round=cls.r41)
        RoundPlayer.objects.create(player=p6, the_round=cls.r41)
        RoundPlayer.objects.create(player=p7, the_round=cls.r41)
        RoundPlayer.objects.create(player=p8, the_round=cls.r41)
        RoundPlayer.objects.create(player=p9, the_round=cls.r41)
        RoundPlayer.objects.create(player=p10, the_round=cls.r41)
        GamePlayer.objects.create(player=cls.p1, game=g41, power=cls.austria)
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
        dp = DrawProposal.objects.create(game=g41,
                                         year=1903,
                                         season=Seasons.SPRING,
                                         passed=True,
                                         proposer=cls.france)
        dp.drawing_powers.add(cls.england)
        dp.drawing_powers.add(cls.france)
        dp.drawing_powers.add(cls.italy)
        dp.drawing_powers.add(cls.russia)
        dp.drawing_powers.add(cls.turkey)
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

    def test_index(self):
        response = self.client.get(reverse('index'),
                                   secure=True)
        # Check that we get the right tournaments listed
        self.assertContains(response, 't1') # Published
        self.assertNotContains(response, 't2') # Unpublished
        self.assertNotContains(response, 't3') # Unpublished
        self.assertContains(response, 't4') # Published

    def test_index_superuser(self):
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('index'),
                                   secure=True)
        # Check that we get the right tournaments listed
        self.assertContains(response, 't1') # Published
        self.assertContains(response, 't2') # Unpublished
        self.assertContains(response, 't3') # Unpublished
        self.assertContains(response, 't4') # Published

    def test_index_manager(self):
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('index'),
                                   secure=True)
        # Check that we get the right tournaments listed
        self.assertContains(response, 't1') # Published
        self.assertContains(response, 't2') # Unpublished, manager
        self.assertNotContains(response, 't3') # Unpublished
        self.assertContains(response, 't4') # Published

    def test_detail_invalid_tournament(self):
        self.assertFalse(Tournament.objects.filter(pk=self.INVALID_T_PK).exists())
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.INVALID_T_PK,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail_manager_wrong_tournament(self):
        # A manager can't see an unpublished tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t3.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        # Don't have to be logged in to see a published tournament
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_regular_user(self):
        # Any user can see a published tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_superuser(self):
        # A superuser can see any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t3.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_manager(self):
        # A manager see their unpublished tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_framesets(self):
        response = self.client.get(reverse('framesets',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_3x3(self):
        response = self.client.get(reverse('frameset_3x3',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_3_games(self):
        response = self.client.get(reverse('frameset_3_games',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_2_games(self):
        response = self.client.get(reverse('frameset_2_games',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_top_board(self):
        response = self.client.get(reverse('frameset_top_board',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_2x2(self):
        response = self.client.get(reverse('frameset_2x2',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_frameset_1x1(self):
        response = self.client.get(reverse('frameset_1x1',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_views(self):
        response = self.client.get(reverse('tournament_views',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_views_finished(self):
        self.assertEqual(self.t4.is_finished(), True)
        response = self.client.get(reverse('tournament_views',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('tournament_overview',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_overview2(self):
        response = self.client.get(reverse('tournament_overview_2',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_overview3(self):
        response = self.client.get(reverse('tournament_overview_3',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_scores(self):
        # Scores page for an in-progress Tournament
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, 'Current Scores')

    def test_scores_completed(self):
        # Scores page for a completed Tournament
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertContains(response, 'Final Scores')

    def test_scores_with_sitter(self):
        # Scores page for a Tournament where somebody sat out a round
        # Add a sitting-out player
        tp = TournamentPlayer.objects.create(player=self.p2,
                                             tournament=self.t4)
        rp = RoundPlayer.objects.create(player=self.p2, the_round=self.r41, game_count=0)
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertContains(response, 'Final Scores')
        rp.delete()
        tp.delete()

    def test_scores_refresh(self):
        response = self.client.get(reverse('tournament_scores_refresh',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_game_results(self):
        response = self.client.get(reverse('tournament_game_results',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_game_results_ongoing(self):
        # Ongoing tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_game_results',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_best_countries(self):
        response = self.client.get(reverse('tournament_best_countries',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_best_countries_refresh(self):
        response = self.client.get(reverse('tournament_best_countries_refresh',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_enter_scores_not_logged_in(self):
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_enter_scores_regular_user(self):
        # A regular user can't enter scores for any old tournament
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_enter_scores_manager_wrong_tournament(self):
        # A manager can't enter scores for a tournament that isn't theirs
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t3.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_archived(self):
        # Nobody can enter scores for an archived tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_enter_scores_superuser(self):
        # A superuser can enter scores for any tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_manager(self):
        # A manager can enter scores for their tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_scores',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_enter_scores_post(self):
        # A manager can enter scores for their tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        tp = self.t2.tournamentplayer_set.first()
        tp_score = tp.score
        rp = self.t2.round_numbered(1).roundplayer_set.get(player=tp.player)
        rp_score = rp.score
        data = {'form-MAX_NUM_FORMS': '1000'}
        for i, tp in enumerate(self.t2.tournamentplayer_set.all()):
            data['form-%d-tp' % i] = str(tp.pk)
            data['form-%d-game_scores_1' % i] = '0.0'
            data['form-%d-round_1' % i] = '73.5'
            data['form-%d-overall_score' % i] = '142.8'
        i += 1
        data['form-TOTAL_FORMS'] = '%d' % i
        data['form-INITIAL_FORMS'] = '%d' % i
        data['form-0-round_1'] = '73.5'
        data['form-0-overall_score'] = '142.8'
        data = urlencode(data)
        response = self.client.post(reverse('enter_scores', args=(self.t2.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the scores page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_scores', args=(self.t2.pk,)))
        # And the scores entered should be saved
        tp.refresh_from_db()
        rp.refresh_from_db()
        self.assertEqual(rp.score, 73.5)
        self.assertEqual(tp.score, 142.8)
        # Clean up
        tp.score = tp_score
        tp.save()
        rp.score = rp_score
        rp.save()

    def test_current_round(self):
        response = self.client.get(reverse('tournament_round',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_current_round_completed(self):
        # "Current round" for a tournament that has ended
        response = self.client.get(reverse('tournament_round',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_game_image_not_logged_in(self):
        response = self.client.get(reverse('add_game_image',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_news(self):
        response = self.client.get(reverse('tournament_news',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('tournament_news_ticker',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_background(self):
        response = self.client.get(reverse('tournament_background',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('tournament_ticker',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_background_ticker(self):
        response = self.client.get(reverse('tournament_background_ticker',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_rounds(self):
        response = self.client.get(reverse('round_index',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_enter_prefs_not_logged_in(self):
        response = self.client.get(reverse('enter_prefs',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_enter_prefs_manager(self):
        # A manager can enter preferences for players in their Tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_prefs',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_enter_prefs(self):
        # A manager can enter preferences for players in their Tournament
        self.assertFalse(Preference.objects.filter(player__tournament=self.t2).exists())
        # Add a Preference for one Player
        tp = self.t2.tournamentplayer_set.last()
        tp.create_preferences_from_string('FART')
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        data = urlencode({'form-TOTAL_FORMS': '9',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 9,
                          'form-0-prefs': 'FART',
                          'form-1-prefs': 'FART',
                          'form-2-prefs': 'FART',
                          'form-3-prefs': 'FART',
                          'form-4-prefs': 'FART',
                          'form-5-prefs': 'FART',
                          'form-6-prefs': 'FART',
                          'form-7-prefs': 'FART',
                          'form-8-prefs': 'FART'})
        response = self.client.post(reverse('enter_prefs', args=(self.t2.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the tournament_detail page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_detail', args=(self.t2.pk,)))
        # ... and the preferences should have been set
        for tp in self.t2.tournamentplayer_set.all():
            self.assertEqual(tp.prefs_string(), 'FART')
        # Clean up
        Preference.objects.filter(player__tournament=self.t2).all().delete()

    def test_upload_prefs_not_logged_in(self):
        response = self.client.get(reverse('upload_prefs',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_prefs_csv(self):
        response = self.client.get(reverse('prefs_csv',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_seeder_bias_not_logged_in(self):
        response = self.client.get(reverse('seeder_bias',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_seeder_bias_missing_perm(self):
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('seeder_bias',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_seeder_bias(self):
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t1).count(), 0)
        # Add a SeederBias for t1
        tp1 = self.t1.tournamentplayer_set.first()
        tp2 = self.t1.tournamentplayer_set.last()
        SeederBias.objects.create(player1=tp1, player2=tp2)
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('seeder_bias',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean up
        SeederBias.objects.filter(player1__tournament=self.t1).delete()

    def test_seeder_bias_add(self):
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t2).count(), 0)
        # TODO Should be able to use USERNAME3 and PASSWORD3 here, but it fails the permission check
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        # Pick two suitable TournamentPlayers
        tp1 = self.t2.tournamentplayer_set.first()
        tp2 = self.t2.tournamentplayer_set.last()
        url = reverse('seeder_bias', args=(self.t2.pk,))
        data = urlencode({'player1': str(tp1.pk),
                          'player2': str(tp2.pk)})
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # it should redirect back to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the SeederBias should be created
        sb_qs = SeederBias.objects.filter(player1__tournament=self.t2)
        self.assertEqual(sb_qs.count(), 1)
        sb = sb_qs.get()
        self.assertEqual(sb.player1, tp1)
        self.assertEqual(sb.player2, tp2)
        # Clean up
        sb.delete()

    def test_seeder_bias_add_error(self):
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t2).count(), 0)
        # TODO Should be able to use USERNAME3 and PASSWORD3 here, but it fails the permission check
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        # Pick two suitable TournamentPlayers
        tp1 = self.t2.tournamentplayer_set.first()
        url = reverse('seeder_bias', args=(self.t2.pk,))
        data = urlencode({'player1': str(tp1.pk),
                          'player2': str(tp1.pk)})
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # page should contain an error
        self.assertContains(response, 'players must differ')
        # ... and no SeederBias should be created
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t2).count(), 0)

    def test_seeder_bias_remove(self):
        # Add two SeederBias objects just for this test
        sb1 = SeederBias.objects.create(player1=self.t2.tournamentplayer_set.first(),
                                        player2=self.t2.tournamentplayer_set.last())
        sb2 = SeederBias.objects.create(player1=self.t2.tournamentplayer_set.first(),
                                        player2=self.tp29)
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t2).count(), 2)
        # TODO Should be able to use USERNAME3 and PASSWORD3 here, but it fails the permission check
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        url = reverse('seeder_bias', args=(self.t2.pk,))
        data = urlencode({'delete_%d' % sb2.pk: 'Remove Bias'})
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # it should redirect back to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the SeederBias should be deleted
        self.assertEqual(SeederBias.objects.filter(player1__tournament=self.t2).count(), 1)
        self.assertFalse(SeederBias.objects.filter(pk=sb2.pk).exists())
        # Clean up
        sb1.delete()

    def test_seeder_bias_archived(self):
        # Try to add SeederBias to an archived Tournament
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        # Pick two suitable TournamentPlayers
        tp1 = self.t4.tournamentplayer_set.first()
        tp2 = self.t4.tournamentplayer_set.last()
        url = reverse('seeder_bias', args=(self.t4.pk,))
        data = urlencode({'player1': str(tp1.pk),
                          'player2': str(tp2.pk)})
        response = self.client.post(url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 404)


    def test_tournament_awards(self):
        # Should be viewable without logging in
        response = self.client.get(reverse('tournament_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)


    def test_tournament_awards_afterwards(self):
        # For a finished Tournament, it should show who received the awards
        self.assertEqual(self.t4.awards.count(), 0)
        for tp in self.t4.tournamentplayer_set.all():
            self.assertEqual(tp.awards.count(), 0)
        # Give some awards out
        self.t4.awards.add(self.a1)
        self.t4.awards.add(self.a2)
        self.t4.save()
        self.tp41.awards.add(self.a1)
        self.tp41.awards.add(self.a2)
        self.tp41.save()
        tp = self.t4.tournamentplayer_set.get(player__first_name='Derek')
        tp.awards.add(self.a2)
        tp.save()
        response = self.client.get(reverse('tournament_awards',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Clean up
        self.t4.awards.clear()
        self.tp41.awards.clear()
        tp.awards.clear()


    def test_enter_awards_post_not_logged_in(self):
        response = self.client.get(reverse('enter_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_enter_awards_post_missing_perms(self):
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        # TODO This isn't right given that they are logged in...
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_enter_awards_get(self):
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_enter_awards_post(self):
        # Give some awards to players beforehand
        self.t1.tournamentplayer_set.last().awards.add(self.t1.awards.first())
        self.t1.tournamentplayer_set.first().awards.add(self.t1.awards.last())
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        tp = self.t1.tournamentplayer_set.first()
        data = {'form-MAX_NUM_FORMS': '1000'}
        for i, a in enumerate(self.t1.awards.all()):
            data['form-%d-award' % i] = str(a.id)
            data['form-%d-players' % i] = [str(tp.id)]
        i += 1
        data['form-TOTAL_FORMS'] = '%d' % i
        data['form-INITIAL_FORMS'] = '%d' % i
        data = urlencode(data, doseq=True)
        response = self.client.post(reverse('enter_awards', args=(self.t1.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_awards', args=(self.t1.pk,)))
        # Check what awards the players now have
        for a in self.t1.awards.all():
            self.assertIn(a, tp.awards.all())
            self.assertEqual(a.tournamentplayer_set.count(), 1)
        # Cleanup
        tp.awards.clear()
