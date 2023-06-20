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
import uuid
from urllib.parse import urlencode

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.models import Award, DrawSecrecy, PowerAssignMethods
from tournament.models import Tournament, TournamentPlayer, SeederBias, Team
from tournament.models import Preference, Round, RoundPlayer, Game, GamePlayer
from tournament.models import CentreCount, DrawProposal
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import G_SCORING_SYSTEMS, NO_SCORING_SYSTEM_STR
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
        perm = Permission.objects.get(name='Can change tournament player')
        cls.u3.user_permissions.add(perm)
        perm = Permission.objects.get(name='Can add team')
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

        today = date.today()
        # Published Tournament, so it's visible to all
        # Ongoing, one round
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=True)
        cls.t1.awards.add(cls.a1)
        cls.t1.awards.add(cls.a2)
        cls.t1.awards.add(cls.a3)
        cls.t1.save()
        Round.objects.create(tournament=cls.t1,
                             start=datetime.combine(cls.t1.start_date, time(hour=8, tzinfo=timezone.utc)),
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
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=NO_SCORING_SYSTEM_STR,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           power_assignment=PowerAssignMethods.PREFERENCES,
                                           is_published=False)
        cls.r21 = Round.objects.create(tournament=cls.t2,
                                       start=datetime.combine(cls.t2.start_date, time(hour=8, tzinfo=timezone.utc)),
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
        # Explicitly call get_prefs_url() to generate a UUID
        tp.get_prefs_url()
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
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=False)

        # Published Tournament, without a manager, but not editable
        # One round, tournament complete
        cls.t4 = Tournament.objects.create(name='t4',
                                           start_date=today,
                                           end_date=today + timedelta(hours=24),
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=DrawSecrecy.SECRET,
                                           is_published=True,
                                           editable=False)
        cls.r41 = Round.objects.create(tournament=cls.t4,
                                       start=datetime.combine(cls.t4.start_date,
                                                              time(hour=16, tzinfo=timezone.utc)),
                                       scoring_system=G_SCORING_SYSTEMS[0].name,
                                       is_finished=True,
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
        # A manager can see their unpublished tournament
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_handicap(self):
        # Check for link to handicaps page
        self.assertFalse(self.t2.handicaps)
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'andicap')
        self.t2.handicaps = True
        self.t2.save()
        response = self.client.get(reverse('tournament_detail',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'andicap')
        # Cleanup
        self.t2.handicaps = False
        self.t2.save()

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
        self.assertTrue(self.t4.is_finished)
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
        self.assertFalse(self.t1.handicaps)
        self.assertTrue(self.t1.tournament_scoring_system_obj().uses_round_scores)
        self.assertTrue(self.t1.show_current_scores)
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, 'Current Scores')
        self.assertNotContains(response, 'Handicap')
        self.assertTemplateUsed(response, 'tournaments/scores.html')

    def test_scores_old(self):
        # Scores page for an in-progress Tournament
        self.assertTrue(self.t1.tournament_scoring_system_obj().uses_round_scores)
        self.assertTrue(self.t1.show_current_scores)
        self.t1.show_current_scores = False
        self.t1.save()
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertTemplateUsed(response, 'tournaments/scores.html')
        # Cleanup
        self.t1.show_current_scores = True
        self.t1.save()

    def test_scores_old2(self):
        # Scores page for an in-progress Tournament
        self.assertTrue(self.t4.tournament_scoring_system_obj().uses_round_scores)
        self.assertTrue(self.t4.show_current_scores)
        self.t4.show_current_scores = False
        self.t4.save()
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertTemplateUsed(response, 'tournaments/scores.html')
        # Cleanup
        self.t4.show_current_scores = True
        self.t4.save()

    def test_scores_no_rounds(self):
        # Scores page for an in-progress Tournament that doesn't use Rounds
        self.assertTrue(self.t1.tournament_scoring_system_obj().uses_round_scores)
        rss = self.t1.round_scoring_system
        tss = self.t1.tournament_scoring_system
        self.t1.round_scoring_system = 'None'
        self.t1.tournament_scoring_system = 'Sum best 3 games in any rounds'
        self.t1.save()
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, 'Current Scores')
        self.assertTemplateUsed(response, 'tournaments/scores_no_round_scores.html')
        # Cleanup
        self.t1.roundscoring_system = rss
        self.t1.tournament_scoring_system = tss
        self.t1.save()

    def test_scores_completed(self):
        # Scores page for a completed Tournament
        self.assertFalse(self.t4.handicaps)
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertContains(response, 'Final Scores')
        self.assertNotContains(response, 'Handicap')

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

    def test_scores_handicap(self):
        # Scores page for an in-progress Tournament with handicaps
        self.assertFalse(self.t1.handicaps)
        self.t1.handicaps = True
        self.t1.save()
        tp = self.t1.tournamentplayer_set.first()
        self.assertEqual(tp.handicap, 0.0)
        tp.handicap = 123.0
        tp.save()
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, 'Handicap')
        self.assertNotContains(response, '123.0')
        # Clean up
        self.t1.handicaps = False
        self.t1.save()
        tp.handicap = 0.0
        tp.save()

    def test_scores_completed_handicap(self):
        # Scores page for a completed Tournament with handicaps
        self.assertFalse(self.t4.handicaps)
        self.t4.handicaps = True
        self.t4.save()
        tp = self.t4.tournamentplayer_set.first()
        self.assertEqual(tp.handicap, 0.0)
        tp.handicap = 123.0
        tp.save()
        response = self.client.get(reverse('tournament_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertContains(response, 'Handicap')
        self.assertContains(response, '123.0')
        # Clean up
        self.t4.handicaps = False
        self.t4.save()
        tp.handicap = 0.0
        tp.save()

    def test_scores_refresh(self):
        response = self.client.get(reverse('tournament_scores_refresh',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertContains(response, '<meta http-equiv="refresh"')

    def test_team_scores(self):
        """No refresh, team tournament, showing current scores"""
        self.t4.team_size = 2
        self.t4.save()
        self.r41.is_team_round = True
        self.r41.is_finished = False
        self.r41.save()
        for g in self.r41.game_set.all():
            self.assertTrue(g.is_finished)
            g.is_finished = False
            g.save()
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('team_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        # TODO Check result
        self.assertContains(response, TEAM_NAME)
        # Clean up
        tm.delete()
        for g in self.r41.game_set.all():
            g.is_finished = True
            g.save()
        self.r41.is_finished = True
        self.r41.is_team_round = False
        self.r41.save()
        self.t4.team_size = None
        self.t4.save()

    def test_team_scores_old(self):
        """Refresh, team tournament, showing scores after last finished round"""
        self.t4.team_size = 2
        self.t4.show_current_scores = False
        self.t4.save()
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('team_scores_refresh',
                                           args=(self.t4.pk,)),
                                   secure=True)
        # TODO Check result
        self.assertContains(response, TEAM_NAME)
        # Clean up
        tm.delete()
        self.t4.team_size = None
        self.t4.show_current_scores = True
        self.t4.save()

    def test_team_scores_refresh_first_team_round(self):
        """Refresh, currently playing the first team round, non-current scores"""
        self.t4.team_size = 2
        self.t4.is_finished = False
        self.t4.show_current_scores = False
        self.t4.save()
        self.r41.is_team_round = True
        self.r41.is_finished = False
        self.r41.save()
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('tournament_overview_4',
                                           args=(self.t4.pk,)),
                                   secure=True)
        # TODO Check result
        self.assertContains(response, TEAM_NAME)
        self.assertNotContains(response, '123.4')
        # Clean up
        tm.delete()
        self.r41.is_finished = True
        self.r41.is_team_round = False
        self.r41.save()
        self.t4.team_size = None
        self.t4.show_current_scores = True
        self.t4.is_finished = True
        self.t4.save()

    def test_team_score_no_teams(self):
        """No refresh, non-team tournament should return 404"""
        self.assertIsNone(self.t4.team_size)
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('team_scores',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_team_score_refresh(self):
        """Refresh to a different page, after team round, should not skip quickly"""
        self.t4.team_size = 2
        self.t4.save()
        self.r41.is_team_round = True
        self.r41.save()
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('tournament_overview_4',
                                           args=(self.t4.pk,)),
                                   secure=True)
        # TODO Check result
        self.assertContains(response, TEAM_NAME)
        # Clean up
        tm.delete()
        self.r41.is_team_round = False
        self.r41.save()
        self.t4.team_size = None
        self.t4.save()

    def test_team_score_refresh_early(self):
        """Refresh to a different page, prior to team round, should skip quickly"""
        self.t4.team_size = 2
        self.t4.save()
        # Add a second round that is a team round
        r42 = Round.objects.create(tournament=self.t4,
                                   start=datetime.combine(self.t4.start_date,
                                                          time(hour=8,
                                                               tzinfo=timezone.utc)),
                                   scoring_system=G_SCORING_SYSTEMS[0].name,
                                   is_team_round=True,
                                   dias=False)
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('tournament_overview_4',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        # Clean up
        tm.delete()
        r42.delete()
        self.t4.team_size = None
        self.t4.save()

    def test_team_score_refresh_no_team_round(self):
        """Refresh to a different page, team-free tournament, should redirect"""
        self.assertIsNone(self.t4.team_size)
        TEAM_NAME = 'Spam, eggs, and spam'
        tm = Team.objects.create(tournament=self.t4,
                                 score=123.4,
                                 name=TEAM_NAME)
        tm.players.add(self.p1)
        response = self.client.get(reverse('tournament_overview_4',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        # Clean up
        tm.delete()
        self.t4.team_size = None
        self.t4.save()

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

    def test_best_countries_old(self):
        self.assertTrue(self.t4.show_current_scores)
        self.t4.show_current_scores = False
        self.t4.save()
        response = self.client.get(reverse('tournament_best_countries',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t4.show_current_scores = True
        self.t4.save()

    def test_best_countries_old2(self):
        self.assertTrue(self.t1.show_current_scores)
        self.t1.show_current_scores = False
        self.t1.save()
        response = self.client.get(reverse('tournament_best_countries',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t1.show_current_scores = True
        self.t1.save()

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
        for i, tp2 in enumerate(self.t2.tournamentplayer_set.all()):
            data['form-%d-tp' % i] = str(tp2.pk)
            data['form-%d-game_scores_1' % i] = '0.0'
            data['form-%d-round_1' % i] = '37.5'
            data['form-%d-overall_score' % i] = '124.8'
        i += 1
        data['form-TOTAL_FORMS'] = '%d' % i
        data['form-INITIAL_FORMS'] = '%d' % i
        # Give a unique value to the first TournamentPlayer
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
        tp.save(update_fields=['score'])
        rp.score = rp_score
        rp.save(update_fields=['score'])

    def test_enter_handicaps_not_logged_in(self):
        self.assertFalse(self.t1.handicaps)
        self.t1.handicaps = True
        self.t1.save()
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        # Cleanup
        self.t1.handicaps = False
        self.t1.save()

    def test_enter_handicaps_regular_user(self):
        # A regular user can't enter handicaps for any old tournament
        self.assertFalse(self.t1.handicaps)
        self.t1.handicaps = True
        self.t1.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        # Cleanup
        self.t1.handicaps = False
        self.t1.save()

    def test_enter_handicaps_manager_wrong_tournament(self):
        # A manager can't enter handicaps for a tournament that isn't theirs
        self.assertFalse(self.t3.handicaps)
        self.t3.handicaps = True
        self.t3.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t3.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Cleanup
        self.t3.handicaps = False
        self.t3.save()

    def test_enter_handicaps_archived(self):
        # Nobody can enter handicaps for an archived tournament
        self.assertFalse(self.t4.handicaps)
        self.t4.handicaps = True
        self.t4.save()
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Cleanup
        self.t4.handicaps = False
        self.t4.save()

    def test_enter_handicaps_superuser(self):
        # A superuser can enter handicaps for any tournament
        self.assertFalse(self.t1.handicaps)
        self.t1.handicaps = True
        self.t1.save()
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t1.handicaps = False
        self.t1.save()

    def test_enter_handicaps_manager(self):
        # A manager can enter handicaps for their tournament
        self.assertFalse(self.t2.handicaps)
        self.t2.handicaps = True
        self.t2.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t2.handicaps = False
        self.t2.save()

    def test_enter_handicaps_not_applicable(self):
        # Nobody can enter handicaps if the tournament doesn't use them
        self.assertFalse(self.t2.handicaps)
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_handicaps',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_enter_handicaps_post(self):
        # A manager can enter handicaps for their tournament
        for tp in self.t2.tournamentplayer_set.all():
            self.assertEqual(tp.handicap, 0.0)
        self.assertFalse(self.t2.handicaps)
        self.t2.handicaps = True
        self.t2.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        data = {'form-MAX_NUM_FORMS': '1000'}
        # Update most handicaps to a different value
        for i, tp in enumerate(self.t2.tournamentplayer_set.all()):
            if i == 1:
                data['form-%d-handicap' % i] = '0.0'
            else:
                data['form-%d-handicap' % i] = '%f' % float(i)
        i += 1
        data['form-TOTAL_FORMS'] = '%d' % i
        data['form-INITIAL_FORMS'] = '%d' % i
        data = urlencode(data)
        response = self.client.post(reverse('enter_handicaps', args=(self.t2.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the tournament player index page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tournament_players', args=(self.t2.pk,)))
        # And the handicaps entered should be saved
        tp.refresh_from_db()
        for i, tp in enumerate(self.t2.tournamentplayer_set.all()):
            if i == 1:
                self.assertAlmostEqual(tp.handicap, 0.0)
            else:
                self.assertAlmostEqual(tp.handicap, float(i))
        # Clean up
        for tp in self.t2.tournamentplayer_set.all():
            tp.handicap = 0.0
            tp.save()
        self.t2.handicaps = False
        self.t2.save()

    def test_teams(self):
        self.t1.team_size = 3
        self.t1.save()
        tm = Team.objects.create(name="The test team",
                                 tournament=self.t1)
        tm.players.add(self.p1)
        response = self.client.get(reverse('teams',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        tm.delete()
        self.t1.team_size = None
        self.t1.save()

    def test_teams_invalid(self):
        """Teams view should give 404 if there's no team round"""
        response = self.client.get(reverse('teams',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_enter_teams_not_logged_in(self):
        self.assertIsNone(self.t1.team_size)
        self.t1.team_size = 3
        self.t1.save()
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        # Cleanup
        self.t1.team_size = None
        self.t1.save()

    def test_enter_teams_regular_user(self):
        # A regular user can't enter teams for any old tournament
        self.assertIsNone(self.t1.team_size)
        self.t1.team_size = 3
        self.t1.save()
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        # Cleanup
        self.t1.team_size = None
        self.t1.save()

    def test_enter_teams_manager_wrong_tournament(self):
        # A manager can't enter teams for a tournament that isn't theirs
        self.assertIsNone(self.t3.team_size)
        self.t3.team_size = 3
        self.t3.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t3.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Cleanup
        self.t3.team_size = None
        self.t3.save()

    def test_enter_teams_archived(self):
        # Nobody can enter teams for an archived tournament
        self.assertIsNone(self.t4.team_size)
        self.t4.team_size = 3
        self.t4.save()
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Cleanup
        self.t4.team_size = None
        self.t4.save()

    def test_enter_teams_superuser(self):
        # A superuser can enter teams for any tournament
        self.assertIsNone(self.t1.team_size)
        self.t1.team_size = 3
        self.t1.save()
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t1.team_size = None
        self.t1.save()

    def test_enter_teams_manager(self):
        # A manager can enter teams for their tournament
        self.assertIsNone(self.t2.team_size)
        self.t2.team_size = 3
        self.t2.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # Cleanup
        self.t2.team_size = None
        self.t2.save()

    def test_enter_teams_not_applicable(self):
        # Nobody can enter teams if the tournament doesn't use them
        self.assertIsNone(self.t2.team_size)
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_teams',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_enter_teams_create(self):
        # A manager can enter teams for their tournament
        self.assertEqual(0, self.t2.team_set.count())
        self.assertIsNone(self.t2.team_size)
        self.t2.team_size = 3
        self.t2.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        data = {'form-MAX_NUM_FORMS': '1000'}
        # Create a number of teams
        tps = list(self.t2.tournamentplayer_set.all())
        teams = []
        while len(tps) > 3:
            members = []
            members.append(tps.pop().player)
            members.append(tps.pop().player)
            members.append(tps.pop().player)
            teams.append(members.copy())
        for i in range(len(teams)):
            data[f'form-{i}-name'] = f'Team {i}'
            for n, p in enumerate(teams[i]):
                data[f'form-{i}-player_{n}'] = str(p.pk)
        i += 1
        data['form-TOTAL_FORMS'] = f'{i}'
        data['form-INITIAL_FORMS'] = f'{i}'
        data = urlencode(data)
        response = self.client.post(reverse('enter_teams', args=(self.t2.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the tournament teams page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('teams', args=(self.t2.pk,)))
        # And the teams entered should be created
        team_set = list(self.t2.team_set.all())
        self.assertEqual(len(teams), len(team_set))
        for tm in team_set:
            self.assertEqual(tm.players.count(), 3)
        # Clean up
        self.t2.team_set.all().delete()
        self.t2.team_size = None
        self.t2.save()

    def test_enter_teams_change(self):
        # A manager can modify teams for their tournament
        self.assertIsNone(self.t2.team_size)
        self.t2.team_size = 3
        self.t2.save()
        self.assertEqual(0, self.t2.team_set.count())
        # Create two teams
        tps = list(self.t2.tournamentplayer_set.all())
        tm1 = Team.objects.create(tournament=self.t2,
                                 name='Existing Team 1')
        tm1.players.add(tps.pop().player)
        tm1.players.add(tps.pop().player)
        tm1.players.add(tps.pop().player)
        tm2 = Team.objects.create(tournament=self.t2,
                                 name='Existing Team 2')
        tm2.players.add(tps.pop().player)
        tm2.players.add(tps.pop().player)
        tm2.players.add(tps.pop().player)
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        data = {'form-MAX_NUM_FORMS': '1000'}
        # Leave one team unchanged, modify another, and create a new one
        i = 0
        data[f'form-{i}-name'] = tm1.name
        for n, p in enumerate(tm1.players.all()):
            data[f'form-{i}-player_{n}'] = str(p.pk)
        i += 1
        data[f'form-{i}-name'] = tm2.name
        for n, p in enumerate(tm2.players.all()):
            if n == 2:
                # Swap the second player into Team #3
                data[f'form-{i+1}-player_{n}'] = str(p.pk)
                player_swapped_to_3 = p
            else:
                data[f'form-{i}-player_{n}'] = str(p.pk)
        i += 1
        data[f'form-{i}-name'] = f'Team {i}'
        members = []
        members.append(tps.pop().player)
        members.append(tps.pop().player)
        members.append(tps.pop().player)
        for n, p in enumerate(members):
            if n == 2:
                # Swap the second player into Team #3
                data[f'form-{i-1}-player_{n}'] = str(p.pk)
                player_swapped_to_2 = p
            else:
                data[f'form-{i}-player_{n}'] = str(p.pk)
        i += 1
        data['form-TOTAL_FORMS'] = f'{i}'
        data['form-INITIAL_FORMS'] = f'{i}'
        data = urlencode(data)
        response = self.client.post(reverse('enter_teams', args=(self.t2.pk,)),
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the tournament teams page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('teams', args=(self.t2.pk,)))
        # And the teams should be modified/created
        team_set = list(self.t2.team_set.all())
        self.assertEqual(3, len(team_set))
        for tm in team_set:
            self.assertEqual(tm.players.count(), 3)
        self.assertIn(player_swapped_to_2, tm2.players.all())
        self.assertIn(player_swapped_to_3, team_set[2].players.all())
        # Clean up
        self.t2.team_set.all().delete()
        self.t2.team_size = None
        self.t2.save()

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
        response = self.client.get(reverse('add_any_game_image',
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

    def test_game_links(self):
        # Add an external URL to one game
        r = self.t4.round_set.first()
        for g in r.game_set.all():
            self.assertEqual(g.external_url, '')
        url = 'http://example.com/game'
        g.external_url = url
        g.save()
        response = self.client.get(reverse('tournament_game_links',
                                           args=(self.t4.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        # One game has a sandbox link, the other doesn't
        self.assertContains(response, url)
        self.assertContains(response, 'No sandbox link')
        # Clean up
        g.external_url = ''
        g.save()

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

    def test_enter_prefs_no_prefs(self):
        # Even a manager can't enter preferences for a tournament that uses another power assignment method
        self.assertEqual(self.t2.power_assignment, PowerAssignMethods.PREFERENCES)
        self.t2.power_assignment = PowerAssignMethods.AUTO
        self.t2.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_prefs',
                                           args=(self.t2.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)
        # Clean up
        self.t2.power_assignment = PowerAssignMethods.PREFERENCES
        self.t2.save()

    def test_enter_prefs(self):
        # A manager can enter preferences for players in their Tournament
        self.assertFalse(Preference.objects.filter(player__tournament=self.t2).exists())
        # Add a Preference for one Player
        tp = self.t2.tournamentplayer_set.last()
        tp.create_preferences_from_string('ART')
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        data = {'form-MAX_NUM_FORMS': '1000'}
        for i, tp2 in enumerate(self.t2.tournamentplayer_set.all()):
            data['form-%d-prefs' % i] = 'FART'
        i += 1
        data['form-TOTAL_FORMS'] = '%d' % i
        data['form-INITIAL_FORMS'] = '%d' % i
        data = urlencode(data)

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
        self.assertContains(response, 'players_must_differ')
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
        perm = Permission.objects.get(name='Can change tournament player')
        self.u3.user_permissions.remove(perm)
        self.u3.save()
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('enter_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        # TODO This isn't right given that they are logged in...
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        # Cleanup
        perm = Permission.objects.get(name='Can change tournament player')
        self.u3.user_permissions.add(perm)
        self.u3.save()

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


    def test_tournament_wdd_awards(self):
        # Should be viewable without logging in
        response = self.client.get(reverse('tournament_wdd_awards',
                                           args=(self.t1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
