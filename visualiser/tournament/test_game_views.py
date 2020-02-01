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

from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy import GameSet, GreatPower
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import Tournament, Round, Game
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import SPRING

class RoundViewTests(TestCase):
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

        # A superuser
        cls.USERNAME1 = 'superuser'
        cls.PWORD1 = 'l33tPw0rd'
        u1 = User.objects.create_user(username=cls.USERNAME1,
                                      password=cls.PWORD1,
                                      is_superuser=True)
        u1.save()

        now = timezone.now()
        # Published Tournament so it's visible to all
        # This one has Secret draw votes
        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=Tournament.SECRET,
                                           is_published=True)
        # One DIAS round, with 1 game
        r = Round.objects.create(tournament=cls.t1,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=cls.t1.start_date)
        cls.g1 = Game.objects.create(name='Game1',
                                     started_at=r.start,
                                     the_round=r,
                                     the_set=GameSet.objects.first())
        # And one non-DIAS round, with 1 game
        r = Round.objects.create(tournament=cls.t1,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=False,
                                 start=cls.t1.start_date)
        cls.g2 = Game.objects.create(name='Game2',
                                     started_at=r.start,
                                     the_round=r,
                                     the_set=GameSet.objects.first())

    def test_detail(self):
        response = self.client.get(reverse('game_detail', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_detail_non_existant_game(self):
        response = self.client.get(reverse('game_detail', args=(self.t1.pk, 'Game42')))
        self.assertEqual(response.status_code, 404)

    def test_sc_chart(self):
        response = self.client.get(reverse('game_sc_chart', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_chart_refresh(self):
        response = self.client.get(reverse('game_sc_chart_refresh', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_enter_scs_not_logged_in(self):
        response = self.client.get(reverse('enter_scs', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_enter_scs(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_scs', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_owners(self):
        response = self.client.get(reverse('game_sc_owners', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_sc_owners_refresh(self):
        response = self.client.get(reverse('game_sc_owners_refresh', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_enter_sc_owners_not_logged_in(self):
        response = self.client.get(reverse('enter_sc_owners', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_enter_sc_owners(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('enter_sc_owners', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_current_game_image(self):
        response = self.client.get(reverse('current_game_image', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_game_image(self):
        response = self.client.get(reverse('game_image', args=(self.t1.pk, 'Game1', 'S1901M')))
        self.assertEqual(response.status_code, 200)

    def test_timelapse(self):
        response = self.client.get(reverse('game_timelapse', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_game_image_seq(self):
        response = self.client.get(reverse('game_image_seq', args=(self.t1.pk, 'Game1', 'S1901M')))
        self.assertEqual(response.status_code, 200)

    def test_add_position_not_logged_in(self):
        response = self.client.get(reverse('add_game_image', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_add_position(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('add_game_image', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_news(self):
        response = self.client.get(reverse('game_news', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_news_ticker(self):
        response = self.client.get(reverse('game_news_ticker', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_background(self):
        response = self.client.get(reverse('game_background', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_background_ticker(self):
        response = self.client.get(reverse('game_background_ticker', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_ticker(self):
        response = self.client.get(reverse('game_ticker', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_draw_vote_not_logged_in(self):
        response = self.client.get(reverse('draw_vote', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 302)

    def test_post_secret_dias_draw_vote(self):
        self.assertEqual(self.g1.drawproposal_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'year': '1902',
                          'season': SPRING,
                          'passed': False,
                          'proposer': str(self.austria)})
        response = self.client.post(reverse('draw_vote', args=(self.t1.pk, 'Game1')),
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the Game page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.g1.get_absolute_url())
        # And the DrawProposal should be added
        self.assertEqual(self.g1.drawproposal_set.count(), 1)
        dp = self.g1.drawproposal_set.get()
        self.assertEqual(dp.game, self.g1)
        self.assertEqual(dp.year, 1902)
        self.assertEqual(dp.season, SPRING)
        self.assertFalse(dp.passed)
        self.assertEqual(dp.proposer, self.austria)
        # Draws in this round are DIAS, and all powers are still alive
        self.assertEqual(dp.draw_size(), 7)
        powers = dp.powers()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                self.assertIn(power, powers)
        # Draws in this tournament are secret
        self.assertIsNone(dp.votes_in_favour)
        self.assertFalse(self.g1.is_finished)
        # Clean up
        dp.delete()

    def test_post_secret_non_dias_draw_vote(self):
        self.assertEqual(self.g2.drawproposal_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'year': '1902',
                          'season': SPRING,
                          'passed': False,
                          'powers': [str(self.england), str(self.turkey)],
                          'proposer': str(self.england)}, True)
        response = self.client.post(reverse('draw_vote', args=(self.t1.pk, 'Game2')),
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the Game page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.g2.get_absolute_url())
        # And the DrawProposal should be added
        self.assertEqual(self.g2.drawproposal_set.count(), 1)
        dp = self.g2.drawproposal_set.get()
        self.assertEqual(dp.game, self.g2)
        self.assertEqual(dp.year, 1902)
        self.assertEqual(dp.season, SPRING)
        self.assertFalse(dp.passed)
        self.assertEqual(dp.proposer, self.england)
        # Draws in this round are non-DIAS
        self.assertEqual(dp.draw_size(), 2)
        powers = dp.powers()
        for power in [self.england, self.turkey]:
            with self.subTest(power=power):
                self.assertIn(power, powers)
        for power in [self.austria, self.france, self.germany, self.italy, self.russia]:
            with self.subTest(power=power):
                self.assertNotIn(power, powers)
        # Draws in this tournament are secret
        self.assertIsNone(dp.votes_in_favour)
        self.assertFalse(self.g2.is_finished)
        # Clean up
        dp.delete()

    def test_post_secret_dias_draw_vote_passed(self):
        self.assertEqual(self.g1.drawproposal_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'year': '1902',
                          'season': SPRING,
                          'passed': True,
                          'proposer': str(self.austria)})
        response = self.client.post(reverse('draw_vote', args=(self.t1.pk, 'Game1')),
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the Game page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.g1.get_absolute_url())
        # And the DrawProposal should be added
        self.assertEqual(self.g1.drawproposal_set.count(), 1)
        dp = self.g1.drawproposal_set.get()
        self.assertEqual(dp.game, self.g1)
        self.assertEqual(dp.year, 1902)
        self.assertEqual(dp.season, SPRING)
        self.assertTrue(dp.passed)
        self.assertEqual(dp.proposer, self.austria)
        # Draws in this round are DIAS, and all powers are still alive
        self.assertEqual(dp.draw_size(), 7)
        powers = dp.powers()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                self.assertIn(power, powers)
        # Draws in this tournament are secret
        self.assertIsNone(dp.votes_in_favour)
        self.g1.refresh_from_db()
        self.assertTrue(self.g1.is_finished)
        # Clean up
        dp.delete()
        self.g1.is_finished = False
        self.g1.save()
        self.g1.refresh_from_db()

    def test_post_secret_non_dias_draw_vote_passed(self):
        self.assertEqual(self.g2.drawproposal_set.count(), 0)
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        data = urlencode({'year': '1902',
                          'season': SPRING,
                          'passed': True,
                          'powers': [str(self.england), str(self.turkey)],
                          'proposer': str(self.austria)}, True)
        response = self.client.post(reverse('draw_vote', args=(self.t1.pk, 'Game2')),
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the Game page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.g2.get_absolute_url())
        # And the DrawProposal should be added
        self.assertEqual(self.g2.drawproposal_set.count(), 1)
        dp = self.g2.drawproposal_set.get()
        self.assertEqual(dp.game, self.g2)
        self.assertEqual(dp.year, 1902)
        self.assertEqual(dp.season, SPRING)
        self.assertTrue(dp.passed)
        self.assertEqual(dp.proposer, self.austria)
        # Draws in this round are non-DIAS, and all powers are still alive
        self.assertEqual(dp.draw_size(), 2)
        powers = dp.powers()
        for power in GreatPower.objects.all():
            with self.subTest(power=power):
                if power in [self.england, self.turkey]:
                    self.assertIn(power, powers)
                else:
                    self.assertNotIn(power, powers)
        # Draws in this tournament are secret
        self.assertIsNone(dp.votes_in_favour)
        self.g2.refresh_from_db()
        self.assertTrue(self.g2.is_finished)
        # Clean up
        dp.delete()
        self.g2.is_finished = False
        self.g2.save()
        self.g2.refresh_from_db()

    def test_draw_vote(self):
        self.client.login(username=self.USERNAME1, password=self.PWORD1)
        response = self.client.get(reverse('draw_vote', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    # TODO check initial value for year and season in draw vote page with and without game images

    # TODO check errors from DrawProposal.clean() get displayed
    # - Second passed DrawProposal for one game
    # - Passed DrawProposal with SC counts afterwards
    # - Dead power in non-DIAS DP

    # TODO what about a DrawProposal for a game that was won outright?

    def test_views(self):
        response = self.client.get(reverse('game_views', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview(self):
        response = self.client.get(reverse('game_overview', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview2(self):
        response = self.client.get(reverse('game_overview_2', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)

    def test_overview3(self):
        response = self.client.get(reverse('game_overview_3', args=(self.t1.pk, 'Game1')))
        self.assertEqual(response.status_code, 200)
