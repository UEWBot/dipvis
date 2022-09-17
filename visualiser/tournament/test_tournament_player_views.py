# Diplomacy Tournament Visualiser
# Copyright (C) 2019-2021 Chris Brand
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
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.models import Tournament, TournamentPlayer
from tournament.models import Round, RoundPlayer, Game, GamePlayer
from tournament.models import CentreCount, DrawProposal
from tournament.models import R_SCORING_SYSTEMS, T_SCORING_SYSTEMS
from tournament.models import G_SCORING_SYSTEMS
from tournament.players import Player

@override_settings(HOSTNAME='example.com')
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TournamentPlayerViewTests(TestCase):
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
        perm = Permission.objects.get(name='Can delete tournament player')
        cls.u3.user_permissions.add(perm)
        cls.u3.save()

        # Some Players
        cls.p1 = Player.objects.create(first_name='Angela',
                                       last_name='Ampersand',
                                       email='a.ampersand@example.com')
        cls.p2 = Player.objects.create(first_name='Bobby',
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
        # Player that is also u3 (manager of t2)
        cls.p11 = Player.objects.create(first_name='Kathryn',
                                        last_name='Krispy',
                                        user = cls.u3)

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
                                           draw_secrecy=Tournament.SECRET,
                                           power_assignment=Tournament.PREFERENCES,
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
        # And this one for any TournamentPlayer
        cls.INVALID_TP_PK = 99999

        # Published Tournament, so it's visible to all
        # Ongoing, one round that has started
        cls.t5 = Tournament.objects.create(name='t5',
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
        cls.tp51 = TournamentPlayer.objects.create(player=cls.p1,
                                                   tournament=cls.t5,
                                                   uuid_str=str(uuid.uuid4()))
        tp = TournamentPlayer.objects.create(player=p3,
                                             tournament=cls.t5)
        Game.objects.create(name='Game1',
                            the_round=cls.r51,
                            started_at=cls.r51.start,
                            the_set=GameSet.objects.first(),
                            is_finished=False)

    def test_index_invalid(self):
        self.assertFalse(Tournament.objects.filter(pk=self.INVALID_T_PK).exists())
        response = self.client.get(reverse('tournament_players', args=(self.INVALID_T_PK,)))
        self.assertEqual(response.status_code, 404)

    def test_index(self):
        response = self.client.get(reverse('tournament_players', args=(self.t1.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_index_editable_prefs(self):
        # A tournament that can be edited, that uses preferences for power assignment
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        response = self.client.get(reverse('tournament_players', args=(self.t2.pk,)))
        self.assertEqual(response.status_code, 200)
        # Verify that the page includes buttons to send preferences emails out
        self.assertIn(b'Register Players', response.content)
        self.assertIn(b'prefs_', response.content)

    def test_index_editable_no_prefs(self):
        # A tournament that can be edited, that doesn't use preferences for power assignment
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_players', args=(self.t3.pk,)))
        self.assertEqual(response.status_code, 200)
        # Verify that the page doesn't include buttons to send preferences emails out
        self.assertIn(b'Register Players', response.content)
        self.assertNotIn(b'prefs_', response.content)

    def test_index_archived(self):
        # A tournament that the user could edit, except that it's been set to not editable
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        response = self.client.get(reverse('tournament_players', args=(self.t4.pk,)))
        self.assertEqual(response.status_code, 200)
        # Verify that we get the read-only version of the page
        self.assertNotIn(b'Register Players', response.content)

    def test_index_unregister_from_editable(self):
        # A tournament that can be edited
        # Add a TournamentPlayer and RoundPlayer just for this test
        self.assertFalse(self.t2.tournamentplayer_set.filter(player=self.p2).exists())
        tp = TournamentPlayer.objects.create(player=self.p2,
                                             tournament=self.t2)
        self.assertTrue(self.t2.tournamentplayer_set.filter(player=self.p2).exists())
        RoundPlayer.objects.create(player=self.p2,
                                   the_round=self.t2.round_numbered(1))
        self.assertTrue(self.t2.round_numbered(1).roundplayer_set.filter(player=self.p2).exists())
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        url = reverse('tournament_players', args=(self.t2.pk,))
        data = urlencode({'unregister_%d' % tp.pk: 'Unregister player',
                          'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the TournamentPlayer and RoundPlayer should no longer exist
        self.assertFalse(self.t2.tournamentplayer_set.filter(player=self.p2).exists())
        self.assertFalse(self.t2.round_numbered(1).roundplayer_set.filter(player=self.p2).exists())

    def test_index_unregister_from_archived(self):
        # A tournament that the user could edit, except that it's been set to not editable
        # Use an existing TournamentPlayer
        tp = self.t4.tournamentplayer_set.get(player=self.p1)
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        url = reverse('tournament_players', args=(self.t4.pk,))
        data = urlencode({'unregister_%d' % tp.pk: 'Unregister player',
                          'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # We shouldn't be allowed to change an uneditable Tournament
        self.assertEqual(response.status_code, 200)
        # Verify that we get the read-only version of the page
        self.assertNotIn(b'Register Players', response.content)
        # ... and the TournamentPlayer should still exist
        self.assertTrue(self.t4.tournamentplayer_set.filter(player=self.p1).exists())

    def test_index_unregister_from_finished(self):
        # TODO: Why does this not behave the same as when it's not editable?
        # A tournament that the user could edit, except that it is finished
        self.assertFalse(self.t4.editable)
        self.t4.editable = True
        self.t4.save()
        # Use an existing TournamentPlayer
        tp = self.t4.tournamentplayer_set.get(player=self.p1)
        self.client.login(username=self.USERNAME2, password=self.PWORD2)
        url = reverse('tournament_players', args=(self.t4.pk,))
        data = urlencode({'unregister_%d' % tp.pk: 'Unregister player',
                          'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # We shouldn't be allowed to change an uneditable Tournament
        self.assertEqual(response.status_code, 404)
        # the TournamentPlayer should still exist
        self.assertTrue(self.t4.tournamentplayer_set.filter(player=self.p1).exists())
        # Clean-up
        self.t4.editable = False
        self.t4.save()

    def test_index_register_player(self):
        # Use the form to register a Player
        self.assertFalse(self.t2.tournamentplayer_set.filter(player=self.p2).exists())
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        url = reverse('tournament_players', args=(self.t2.pk,))
        data = urlencode({'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0,
                          'form-1-player': str(self.p2.pk)})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the TournamentPlayer should have been added
        tp_qs = self.t2.tournamentplayer_set.filter(player=self.p2)
        self.assertTrue(tp_qs.exists())
        # new TournamentPlayer should not be unranked
        tp = tp_qs.get()
        self.assertFalse(tp.unranked)
        # Clean up
        tp_qs.delete()

    def test_index_register_registered_player(self):
        # Use the form to register a Player who is already registered
        self.assertTrue(self.t2.tournamentplayer_set.filter(player=self.p1).exists())
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        url = reverse('tournament_players', args=(self.t2.pk,))
        data = urlencode({'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0,
                          'form-1-player': str(self.p1.pk)})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)

    def test_index_resend_prefs_email(self):
        # Use the form to re-send the preferences email to a Player
        tp = self.t2.tournamentplayer_set.get(player=self.p1)
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        url = reverse('tournament_players', args=(self.t2.pk,))
        data = urlencode({'prefs_%d' % tp.pk: 'Send prefs email',
                          'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the email should be sent
        self.assertEqual(len(mail.outbox), 1)

    def test_index_flag_as_unranked(self):
        # Adding a manager as a TournamentPlayer should flag them as unranked
        self.assertFalse(self.t2.tournamentplayer_set.filter(player=self.p11).exists())
        self.client.login(username=self.USERNAME3, password=self.PWORD3)
        url = reverse('tournament_players', args=(self.t2.pk,))
        data = urlencode({'form-TOTAL_FORMS': '4',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': 0,
                          'form-1-player': str(self.p11.pk)})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, url)
        # ... and the TournamentPlayer should have been added
        tp_qs = self.t2.tournamentplayer_set.filter(player=self.p11)
        self.assertTrue(tp_qs.exists())
        # new TournamentPlayer should be unranked
        tp = tp_qs.get()
        self.assertTrue(tp.unranked)
        # Clean up
        tp_qs.delete()

    def test_details_invalid_tournament(self):
        self.assertFalse(Tournament.objects.filter(pk=self.INVALID_T_PK).exists())
        response = self.client.get(reverse('tournament_player_detail', args=(self.INVALID_T_PK,
                                                                             self.tp11.pk)))
        self.assertEqual(response.status_code, 404)

    def test_details_invalid_player(self):
        self.assertFalse(self.t1.tournamentplayer_set.filter(pk=self.INVALID_TP_PK).exists())
        response = self.client.get(reverse('tournament_player_detail', args=(self.t1.pk,
                                                                             self.INVALID_TP_PK)))
        self.assertEqual(response.status_code, 404)

    def test_details_player_not_in_tourney(self):
        response = self.client.get(reverse('tournament_player_detail', args=(self.t1.pk,
                                                                             self.tp51.pk)))
        self.assertEqual(response.status_code, 404)

    def test_details_valid(self):
        response = self.client.get(reverse('tournament_player_detail', args=(self.t1.pk,
                                                                             self.tp11.pk)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs(self):
        response = self.client.get(reverse('player_prefs', args=(self.t1.pk, self.tp11.uuid_str)))
        self.assertEqual(response.status_code, 200)

    def test_player_prefs_invalid_uuid(self):
        # Should get a 404 error if the UUID doesn't correspond to a TournamentPlayer
        response = self.client.get(reverse('player_prefs', args=(self.t1.pk, uuid.uuid4())))
        self.assertEqual(response.status_code, 404)

    def test_player_prefs_archived(self):
        # Should get a 404 error if the Tournament has been achived
        response = self.client.get(reverse('player_prefs', args=(self.t4.pk, self.tp41.uuid_str)))
        self.assertEqual(response.status_code, 404)

    def test_player_prefs_too_late(self):
        # Should get a 404 error if the final round has started
        response = self.client.get(reverse('player_prefs', args=(self.t5.pk, self.tp51.uuid_str)))
        self.assertEqual(response.status_code, 404)

    def test_player_prefs_post(self):
        self.assertFalse(self.tp11.preference_set.exists())
        url = reverse('player_prefs', args=(self.t1.pk, self.tp11.uuid_str))
        data = urlencode({'form-TOTAL_FORMS': '1',
                          'form-MAX_NUM_FORMS': '1000',
                          'form-INITIAL_FORMS': '1',
                          'prefs': 'FART'})
        response = self.client.post(url,
                                    data,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect
        self.assertEqual(response.status_code, 302)
        # ... and the preferences should have been set
        self.assertEqual(self.tp11.prefs_string(), 'FART')
        # Clean up
        self.tp11.preference_set.all().delete()
