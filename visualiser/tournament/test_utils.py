# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand <chris.carter.brand@gmail.com>
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
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone as django_timezone

from tournament.models import (R_SCORING_SYSTEMS, T_SCORING_SYSTEMS,
                               DrawSecrecy, Round, Tournament, TournamentPlayer)
from tournament.players import Player
from tournament.utils import (map_to_backstabbr_power, nuke_invalid_email,
                              player_emails, upcoming_rounds)


class UtilsTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def test_map_to_backstabbr_power(self):
        from tournament.diplomacy import GreatPower

        gp = GreatPower.objects.get(abbreviation='A')
        power = map_to_backstabbr_power(gp)
        self.assertEqual(power[0], 'A')

    def test_map_to_backstabbr_power_invalid(self):
        fake_power = SimpleNamespace(abbreviation='Z')
        self.assertRaises(ValueError, map_to_backstabbr_power, fake_power)

    def test_player_emails(self):
        today = django_timezone.now().date()
        t = Tournament.objects.create(name='util-email-test',
                                      start_date=today,
                                      end_date=today,
                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                      tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                      draw_secrecy=DrawSecrecy.SECRET)
        p1 = Player.objects.create(first_name='Uma',
                                   last_name='UtilsOne',
                                   email='uma1@example.com')
        p2 = Player.objects.create(first_name='Uri',
                                   last_name='UtilsTwo',
                                   email='uri2@example.com')
        TournamentPlayer.objects.create(player=p1, tournament=t)
        TournamentPlayer.objects.create(player=p2, tournament=t)

        emails = player_emails(t)
        self.assertCountEqual(emails, ['uma1@example.com', 'uri2@example.com'])
        # Cleanup
        t.delete()
        p1.delete()
        p2.delete()

    def test_nuke_invalid_email(self):
        p = Player.objects.create(first_name='Nina',
                                  last_name='Nuked',
                                  email='bad@example.com')
        nuke_invalid_email('bad@example.com')
        p.refresh_from_db()
        self.assertEqual(p.email, '')
        # Cleanup
        p.delete()

    def test_upcoming_rounds_published_only(self):
        now = django_timezone.now()
        t_pub = Tournament.objects.create(name='util-round-pub',
                                          start_date=now.date(),
                                          end_date=now.date(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          is_published=True)
        t_unpub = Tournament.objects.create(name='util-round-unpub',
                                            start_date=now.date(),
                                            end_date=now.date(),
                                            round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                            draw_secrecy=DrawSecrecy.SECRET,
                                            is_published=False)
        Round.objects.create(tournament=t_pub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))
        Round.objects.create(tournament=t_unpub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))

        with patch('builtins.print') as mock_print:
            upcoming_rounds(num_days=2, include_unpublished=False)
        self.assertEqual(mock_print.call_count, 1)
        # Cleanup
        t_pub.delete()
        t_unpub.delete()

    def test_upcoming_rounds_include_unpublished(self):
        now = django_timezone.now()
        t_pub = Tournament.objects.create(name='util-round-pub-all',
                                          start_date=now.date(),
                                          end_date=now.date(),
                                          round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                          tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                          draw_secrecy=DrawSecrecy.SECRET,
                                          is_published=True)
        t_unpub = Tournament.objects.create(name='util-round-unpub-all',
                                            start_date=now.date(),
                                            end_date=now.date(),
                                            round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                            tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                            draw_secrecy=DrawSecrecy.SECRET,
                                            is_published=False)
        Round.objects.create(tournament=t_pub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))
        Round.objects.create(tournament=t_unpub,
                             scoring_system=R_SCORING_SYSTEMS[0].name,
                             dias=True,
                             is_finished=False,
                             start=now + timedelta(days=1))

        with patch('builtins.print') as mock_print:
            upcoming_rounds(num_days=2, include_unpublished=True)
        self.assertEqual(mock_print.call_count, 2)
        # Cleanup
        t_pub.delete()
        t_unpub.delete()