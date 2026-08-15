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

from datetime import date
from urllib.parse import urlencode
from unittest.mock import patch

from django_countries import countries

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, tag
from django.urls import reverse

from tournament.circuits import Circuit, CircuitPlayer
from tournament.diplomacy import GreatPower
from tournament.models import DrawSecrecy, R_SCORING_SYSTEMS, T_SCORING_SYSTEMS, Tournament, TournamentPlayer
from tournament.players import Player, PlayerGameResult, WDDPlayer


class PlayerViewTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        # A Player
        cls.p1 = Player.objects.create(first_name='Angela',
                                       last_name='Ampersand')

        # A pk that (hopefully) doesn't correspond to a player
        cls.INVALID_P_PK = 99999

        # A Superuser
        cls.USERNAME = 'superuser'
        cls.PWORD = 'L33tPw0rd'
        u = User.objects.create_user(username=cls.USERNAME,
                                     password=cls.PWORD,
                                     is_superuser=True)
        u.save()

    def test_index(self):
        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/index.html')
        self.assertContains(response, str(self.p1))

    def test_index_shows_pagination_controls(self):
        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page 1 of 1')
        self.assertNotContains(response, 'first')
        self.assertNotContains(response, 'previous')

    def test_index_middle_page_has_previous_and_next(self):
        for i in range(60):
            Player.objects.create(first_name=f'Page{i:02d}',
                                  last_name='Nav')

        response = self.client.get(reverse('player_index') + '?page=2',
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page 2 of 3')
        self.assertContains(response, 'first')
        self.assertContains(response, 'previous')
        self.assertContains(response, 'next')
        self.assertContains(response, 'last')

    def test_index_shows_add_player_links_for_authorized_user(self):
        username = 'player-index-adder'
        password = 'L33tPassw0rd'
        user = User.objects.create_user(username=username,
                                        password=password,
                                        is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename='add_player'))
        self.client.login(username=username, password=password)

        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add a single player')
        self.assertContains(response, 'Upload CSV file of players')

    def test_index_hides_add_player_links_for_unauthorized_user(self):
        username = 'player-index-noadd'
        password = 'NoAddPassw0rd'
        user = User.objects.create_user(username=username,
                                        password=password,
                                        is_staff=True)
        self.client.login(username=username, password=password)

        response = self.client.get(reverse('player_index'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Add a single player')
        self.assertNotContains(response, 'Upload CSV file of players')

    def test_detail_invalid_player(self):
        response = self.client.get(reverse('player_detail',
                                           args=(self.INVALID_P_PK,)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_detail(self):
        """Don't have to be logged in to see a player"""
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, str(self.p1))
        self.assertContains(response, 'No tournaments in the database')
        self.assertContains(response, 'No circuits in the database')
        self.assertContains(response, 'WPE7 Scores')
        self.assertContains(response, 'Compare With Another Player')

    def test_detail_shows_circuit_participation_links(self):
        today = date.today()
        t = Tournament.objects.create(name='Circuit Participation Test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True)
        tp = TournamentPlayer.objects.create(player=self.p1,
                                             tournament=t,
                                             score=9.5)
        circuit = Circuit.objects.create(name='Player Circuit',
                                         start_date=today,
                                         end_date=today,
                                         scoring_system='Sum best 3 tournament percentiles')
        circuit.tournaments.add(t)
        cp = CircuitPlayer.objects.get(player=self.p1,
                           circuit=circuit)
        cp.tournamentplayers.add(tp)

        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, 'Player Circuit')
        self.assertContains(response, circuit.get_absolute_url())

        # Cleanup
        circuit.delete()
        t.delete()

    def test_detail_location_hidden_when_blank(self):
        self.assertEqual(self.p1.location, '')
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertNotContains(response, 'Location:')

    def test_detail_location_shown_when_set(self):
        self.p1.location = 'Cambridge'
        self.p1.save(update_fields=['location'])
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, 'Location:')
        self.assertContains(response, 'Cambridge')
        # Cleanup
        self.p1.location = ''
        self.p1.save(update_fields=['location'])

    def test_detail_picture_shown_when_set(self):
        self.p1.picture = SimpleUploadedFile('player_picture.png',
                                             b'png-bytes',
                                             content_type='image/png')
        self.p1.save(update_fields=['picture'])
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, 'style="max-width:10%;"')
        self.assertContains(response, 'alt="Angela Ampersand"')
        # Cleanup
        self.p1.picture.delete(save=False)
        self.p1.picture = None
        self.p1.save(update_fields=['picture'])

    def test_detail_shows_tournament_entry(self):
        today = date.today()
        t = Tournament.objects.create(name='Detail Test Open',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET,
                                      is_published=True)
        TournamentPlayer.objects.bulk_create([
            TournamentPlayer(player=self.p1,
                             tournament=t,
                             score=9.5)
        ])
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, str(t))
        self.assertNotContains(response, 'No tournaments in the database')
        # Cleanup
        t.delete()

    def test_detail_nationalities(self):
        self.assertEqual(len(self.p1.nationalities), 0)
        self.p1.nationalities = countries[0]
        self.p1.save(update_fields=['nationalities'])
        # Don't have to be logged in to see a player
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        self.assertContains(response, 'style="width:32px;"')
        # Cleanup
        self.p1.nationalities = []
        self.p1.save(update_fields=['nationalities'])

    def test_detail_wddplayers(self):
        """Test a Player with multiple WDDPlayers"""
        self.assertFalse(self.p1.wddplayer_set.exists())
        WDDPlayer.objects.create(wdd_player_id=912,
                                 player=self.p1)
        WDDPlayer.objects.create(wdd_player_id=15045,
                                 player=self.p1)
        # Don't have to be logged in to see a player
        response = self.client.get(reverse('player_detail',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/detail.html')
        # Cleanup
        self.p1.wddplayer_set.all().delete()

    def test_detail_refresh_wdd(self):
        """Test the 'Update background' button"""
        self.client.login(username=self.USERNAME, password=self.PWORD)
        player_url = reverse('player_detail', args=(self.p1.pk,))
        data = urlencode({'update_bg': 'Update background'})
        response = self.client.post(player_url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect back to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, player_url)

    def test_detail_versus(self):
        """Test the 'Versus' button"""
        p = Player.objects.create(first_name='Barry',
                                  last_name='Bandersnatch')
        self.client.login(username=self.USERNAME, password=self.PWORD)
        player_url = reverse('player_detail', args=(self.p1.pk,))
        data = urlencode({'versus': 'Submit',
                          'player': str(p.pk)})
        response = self.client.post(player_url,
                                    data,
                                    secure=True,
                                    content_type='application/x-www-form-urlencoded')
        # It should redirect to the versus page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('player_versus',
                                               args=(self.p1.pk, p.pk)))
        # Cleanup
        p.delete()

    def test_versus_invalid_player1(self):
        response = self.client.get(reverse('player_versus',
                                           args=(self.INVALID_P_PK, self.p1.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_versus_invalid_player2(self):
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, self.INVALID_P_PK)),
                                   secure=True)
        self.assertEqual(response.status_code, 404)

    def test_versus_no_prev(self):
        p2 = Player.objects.create(first_name='Bernard',
                                   last_name='Belligerent')
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/versus.html')
        self.assertContains(response, 'No records of any games with both these players')
        p2.delete()

    def test_versus_prev(self):
        england = GreatPower.objects.get(abbreviation='E')
        germany = GreatPower.objects.get(abbreviation='G')
        p2 = Player.objects.create(first_name='Bernard',
                                   last_name='Belligerent')
        # Add a shared game
        # Add in another result for a non-shared game
        today = date.today()
        pgr1 = PlayerGameResult.objects.create(event_name='Galaxy Championship',
                                               round_number=2,
                                               game_number=1,
                                               date=today,
                                               player=self.p1,
                                               power=germany,
                                               position=2)
        # One with lots of blanks
        pgr2 = PlayerGameResult.objects.create(event_name='Galaxy Championship',
                                               round_number=3,
                                               game_number=2,
                                               date=today,
                                               player=self.p1,
                                               power=england,
                                               position=3)
        # One with lots of detail
        PlayerGameResult.objects.create(event_name=pgr1.event_name,
                                        round_number=pgr1.round_number,
                                        game_number=pgr1.game_number,
                                        date=pgr1.date,
                                        player=p2,
                                        power=germany,
                                        position=6,
                                        position_equals=2,
                                        score=3.4,
                                        final_sc_count=1,
                                        result='D7')
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/versus.html')
        self.assertContains(response, 'Tournament')
        self.assertContains(response, 'Power')
        self.assertContains(response, 'Galaxy Championship')
        self.assertContains(response, '2nd')
        self.assertContains(response, '6th')
        self.assertContains(response, '3.40')
        self.assertContains(response, 'background-color:LightGreen;')
        pgr1.delete()
        pgr2.delete()
        p2.delete()

    def test_versus_prev_wdr_link(self):
        france = GreatPower.objects.get(abbreviation='F')
        turkey = GreatPower.objects.get(abbreviation='T')
        p2 = Player.objects.create(first_name='Wendy',
                                   last_name='West')
        today = date.today()
        pgr1 = PlayerGameResult.objects.create(event_name='Nebula Classic',
                                               round_number=4,
                                               game_number=5,
                                               date=today,
                                               player=self.p1,
                                               power=france,
                                               position=1,
                                               wdr_tournament_id=4173)
        PlayerGameResult.objects.create(event_name=pgr1.event_name,
                                        round_number=pgr1.round_number,
                                        game_number=pgr1.game_number,
                                        date=pgr1.date,
                                        player=p2,
                                        power=turkey,
                                        position=7,
                                        wdr_tournament_id=4173)
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/versus.html')
        self.assertContains(response,
                            'href="https://www.world-diplomacy-reference.com/tournaments/4173/boards"')
        self.assertContains(response, 'R 4 B 5')
        # Cleanup
        pgr1.delete()
        p2.delete()

    def test_versus_prev_wdd_link_fallback(self):
        austria = GreatPower.objects.get(abbreviation='A')
        russia = GreatPower.objects.get(abbreviation='R')
        p2 = Player.objects.create(first_name='Waldo',
                                   last_name='White')
        today = date.today()
        pgr1 = PlayerGameResult.objects.create(event_name='Comet Open',
                                               round_number=1,
                                               game_number=3,
                                               date=today,
                                               player=self.p1,
                                               power=austria,
                                               position=4,
                                               wdd_tournament_id=9001)
        PlayerGameResult.objects.create(event_name=pgr1.event_name,
                                        round_number=pgr1.round_number,
                                        game_number=pgr1.game_number,
                                        date=pgr1.date,
                                        player=p2,
                                        power=russia,
                                        position=5,
                                        wdd_tournament_id=9001)
        response = self.client.get(reverse('player_versus',
                                           args=(self.p1.pk, p2.pk)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/versus.html')
        self.assertContains(response,
                            'href="https://world-diplomacy-database.com/php/results/tournament_board.php?id_tournament=9001&amp;id_round=1&amp;id_board=3"')
        self.assertContains(response, 'R 1 B 3')
        # Cleanup
        pgr1.delete()
        p2.delete()

    def test_wpe(self):
        """Test WPE page"""
        response = self.client.get(reverse('wep7',
                                           args=(self.p1.pk,)),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/wpe.html')
        self.assertContains(response, 'Start date:')
        self.assertContains(response, 'WPE Score')

    def test_upload_players_requires_login(self):
        response = self.client.get(reverse('upload_players'),
                                   secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_upload_players_get(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        response = self.client.get(reverse('upload_players'),
                                   secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'players/upload_players.html')
        self.assertContains(response, 'Mandatory columns:')
        self.assertContains(response, 'First Name')
        self.assertContains(response, 'Last Name')
        self.assertContains(response, 'Optional columns:')
        self.assertContains(response, 'Backstabbr Username')
        self.assertContains(response, 'WDR URL')
        self.assertContains(response, 'WDR Id')
        self.assertContains(response, 'WDD URL')
        self.assertContains(response, 'WDD Id')
        self.assertContains(response, 'Upload')

    def test_upload_players_post_missing_first_name(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = 'Last Name\nAmpersand\n'
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))

    def test_upload_players_post_missing_last_name(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = 'First Name\nAngela\n'
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))

    def test_upload_players_post_missing_email_column(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,Backstabbr Username\n'
            'Eddie,Emailless,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Eddie', last_name='Emailless')
        self.assertEqual(p.email, '')
        # Cleanup
        p.delete()

    def test_upload_players_post_missing_backstabbr_column(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,Email Address\n'
            'Bella,NoBackstabbr,bella@example.com\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Bella', last_name='NoBackstabbr')
        self.assertEqual(p.email, 'bella@example.com')
        self.assertEqual(p.backstabbr_username, '')
        # Cleanup
        p.delete()

    def test_upload_players_post_large_file(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name\n'
            'Lara,Large\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('django.core.files.uploadedfile.InMemoryUploadedFile.multiple_chunks',
                   return_value=True):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))

    def test_upload_players_post_invalid_wdd_id_non_integer(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDD Id,Backstabbr Username\n'
            'Will,WrongId,abc,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Will', last_name='WrongId')
        self.assertFalse(WDDPlayer.objects.filter(player=p).exists())
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdr_id_non_integer(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR Id,Backstabbr Username\n'
            'Wren,WrongWdr,abc,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Wren', last_name='WrongWdr')
        self.assertIsNone(p.wdr_player_id)
        # Cleanup
        p.delete()

    def test_upload_players_post_valid_wdr_id(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR Id,Backstabbr Username\n'
            'Ria,RightWdr,4173,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdr_player_id',
                   return_value=None):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Ria', last_name='RightWdr')
        self.assertEqual(p.wdr_player_id, 4173)
        # Cleanup
        p.delete()

    def test_upload_players_post_valid_wdr_url(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR URL,Backstabbr Username\n'
            'Ruth,UrlWdr,https://www.world-diplomacy-reference.com/players/4173,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdr_player_id',
                   return_value=None):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Ruth', last_name='UrlWdr')
        self.assertEqual(p.wdr_player_id, 4173)
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdr_url_non_integer(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR URL,Backstabbr Username\n'
            'Uma,UrlBadWdr,https://www.world-diplomacy-reference.com/players/not-a-number,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Uma', last_name='UrlBadWdr')
        self.assertIsNone(p.wdr_player_id)
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdr_id_validation(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR Id,Backstabbr Username\n'
            'Wes,ValidateWdr,123,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdr_player_id',
                   side_effect=ValidationError('bad id')):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Wes', last_name='ValidateWdr')
        self.assertIsNone(p.wdr_player_id)
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdr_url_validation(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDR URL,Backstabbr Username\n'
            'Wendy,UrlValidateWdr,https://www.world-diplomacy-reference.com/players/4173,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdr_player_id',
                   side_effect=ValidationError('bad url id')):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Wendy', last_name='UrlValidateWdr')
        self.assertIsNone(p.wdr_player_id)
        # Cleanup
        p.delete()

    def test_upload_players_post_existing_player_different_wdr_id(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        p = Player.objects.create(first_name='Dana',
                                  last_name='DiffWdr',
                                  wdr_player_id=1001)
        csv_data = (
            'First Name,Last Name,WDR Id,Backstabbr Username\n'
            'Dana,DiffWdr,2002,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdr_player_id',
                   return_value=None):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p.refresh_from_db()
        self.assertEqual(p.wdr_player_id, 1001)
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdd_id_validation(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDD Id,Backstabbr Username\n'
            'Vera,Validate,123,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdd_player_id',
                   side_effect=ValidationError('bad id')):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Vera', last_name='Validate')
        self.assertFalse(WDDPlayer.objects.filter(player=p).exists())
        # Cleanup
        p.delete()

    def test_upload_players_post_invalid_wdd_url_validation(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDD URL,Backstabbr Username\n'
            'Ula,Urlbad,https://world-diplomacy-database.com/php/results/player_fiche.php?id_player=456,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdd_player_id',
                   side_effect=ValidationError('bad url id')):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Ula', last_name='Urlbad')
        self.assertFalse(WDDPlayer.objects.filter(player=p).exists())
        # Cleanup
        p.delete()

    def test_upload_players_post_valid_wdd_id_calls_wdd_create(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,WDD Id,Backstabbr Username\n'
            'Willa,WithWdd,789,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.validate_wdd_player_id',
                   return_value=None):
            with patch('tournament.player_views.WDDPlayer.get_or_create',
                       create=True) as mocked_get_or_create:
                response = self.client.post(reverse('upload_players'),
                                            {'csv_file': csv_file},
                                            secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Willa', last_name='WithWdd')
        mocked_get_or_create.assert_called_once_with(wdd_player_id=789,
                                                     player=p)
        # Cleanup
        p.delete()
    def test_upload_players_post_invalid_email_ignored(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,Email Address,Backstabbr Username\n'
            'Iris,Invalid,not-an-email,\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Iris', last_name='Invalid')
        self.assertEqual(p.email, '')
        # Cleanup
        p.delete()

    def test_upload_players_post_adds_player_trims_fields(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        csv_data = (
            'First Name,Last Name,Email Address,Backstabbr Username\n'
            '  Una  ,  Update  ,  una@example.com  ,  una_bs  \n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p = Player.objects.get(first_name='Una', last_name='Update')
        self.assertEqual(p.email, 'una@example.com')
        self.assertEqual(p.backstabbr_username, 'una_bs')
        # Cleanup
        p.delete()

    def test_upload_players_post_updates_existing_missing_fields(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        p = Player.objects.create(first_name='Nadia',
                                  last_name='Needsinfo')
        self.assertEqual(p.email, '')
        self.assertEqual(p.backstabbr_username, '')
        csv_data = (
            'First Name,Last Name,Email Address,Backstabbr Username\n'
            'Nadia,Needsinfo,nadia@example.com,nadia_bs\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        response = self.client.post(reverse('upload_players'),
                                    {'csv_file': csv_file},
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p.refresh_from_db()
        self.assertEqual(p.email, 'nadia@example.com')
        self.assertEqual(p.backstabbr_username, 'nadia_bs')
        # Cleanup
        p.delete()

    def test_upload_players_post_existing_player_mismatch_fields(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        p = Player.objects.create(first_name='Mira',
                                  last_name='Mismatch',
                                  email='old@example.com',
                                  backstabbr_username='old_bs')
        csv_data = (
            'First Name,Last Name,Email Address,Backstabbr Username\n'
            'Mira,Mismatch,new@example.com,new_bs\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.Player.objects.update_or_create',
                   return_value=(p, False)):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p.refresh_from_db()
        self.assertEqual(p.email, 'old@example.com')
        self.assertEqual(p.backstabbr_username, 'old_bs')
        # Cleanup
        p.delete()

    def test_upload_players_post_existing_player_adds_missing_info_branch(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        p = Player.objects.create(first_name='Alma',
                                  last_name='Addinfo')
        csv_data = (
            'First Name,Last Name,Email Address,Backstabbr Username\n'
            'Alma,Addinfo,alma@example.com,alma_bs\n'
        )
        csv_file = SimpleUploadedFile('players.csv',
                                      csv_data.encode('utf-8'),
                                      content_type='text/csv')
        with patch('tournament.player_views.Player.objects.update_or_create',
                   return_value=(p, False)):
            response = self.client.post(reverse('upload_players'),
                                        {'csv_file': csv_file},
                                        secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
        p.refresh_from_db()
        self.assertEqual(p.email, 'alma@example.com')
        self.assertEqual(p.backstabbr_username, 'alma_bs')
        # Cleanup
        p.delete()

    def test_upload_players_post_missing_file(self):
        self.client.login(username=self.USERNAME, password=self.PWORD)
        response = self.client.post(reverse('upload_players'),
                                    secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('upload_players'))
