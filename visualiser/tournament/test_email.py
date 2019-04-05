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

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from tournament.diplomacy import GreatPower, GameSet
from tournament.email import send_board_call, send_prefs_email
from tournament.models import Tournament, TournamentPlayer
from tournament.models import Round, RoundPlayer
from tournament.models import Game, GamePlayer
from tournament.models import G_SCORING_SYSTEMS, R_SCORING_SYSTEMS
from tournament.models import T_SCORING_SYSTEMS, SECRET, PREFERENCES
from tournament.players import Player

class EmailTests(TestCase):
    fixtures = ['game_sets.json']

    @classmethod
    def setUpTestData(cls):
        settings.HOSTNAME = 'example.com'
        # Use the memory email backend
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        # Email comes from the TD
        cls.td_email = 'td@example.com'
        settings.EMAIL_HOST_USER = cls.td_email

        # Easy access to all the GreatPowers
        cls.austria = GreatPower.objects.get(abbreviation='A')
        cls.england = GreatPower.objects.get(abbreviation='E')
        cls.france = GreatPower.objects.get(abbreviation='F')
        cls.germany = GreatPower.objects.get(abbreviation='G')
        cls.italy = GreatPower.objects.get(abbreviation='I')
        cls.russia = GreatPower.objects.get(abbreviation='R')
        cls.turkey = GreatPower.objects.get(abbreviation='T')

        # We need a Round in a Tournament, with 3 Games

        s = GameSet.objects.get(name='Avalon Hill')

        now = timezone.now()

        cls.t1 = Tournament.objects.create(name='t1',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=SECRET)

        r = Round.objects.create(tournament=cls.t1,
                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                 dias=True,
                                 start=cls.t1.start_date)

        g1 = Game.objects.create(name='g1',
                                 started_at=r.start,
                                 the_round=r,
                                 the_set=s)
        g2 = Game.objects.create(name='g2',
                                 started_at=r.start,
                                 the_round=r,
                                 the_set=s)
        g3 = Game.objects.create(name='g3',
                                 started_at=r.start,
                                 the_round=r,
                                 the_set=s)

        # A whole lot of players
        cls.p1 = Player.objects.create(first_name='Abbey',
                                       last_name='Brown',
                                       email = 'a.brown@example.com')
        TournamentPlayer.objects.create(player=cls.p1, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p1, the_round=r)
        GamePlayer.objects.create(player=cls.p1, game=g1, power=cls.austria)

        cls.p2 = Player.objects.create(first_name='Charles',
                                       last_name='Dog',
                                       email = 'c.dog@example.com')
        TournamentPlayer.objects.create(player=cls.p2, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p2, the_round=r)
        GamePlayer.objects.create(player=cls.p2, game=g1, power=cls.england)

        cls.p3 = Player.objects.create(first_name='Ethel',
                                       last_name='Frankenstein',
                                       email = 'e.frankenstein@example.com')
        TournamentPlayer.objects.create(player=cls.p3, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p3, the_round=r)
        GamePlayer.objects.create(player=cls.p3, game=g1, power=cls.france)

        cls.p4 = Player.objects.create(first_name='George',
                                       last_name='Hotel',
                                       email = 'g.hotel@example.com')
        TournamentPlayer.objects.create(player=cls.p4, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p4, the_round=r)
        GamePlayer.objects.create(player=cls.p4, game=g1, power=cls.germany)

        cls.p5 = Player.objects.create(first_name='Iris',
                                       last_name='Jackson',
                                       email = 'i.jackson@example.com')
        TournamentPlayer.objects.create(player=cls.p5, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p5, the_round=r)
        GamePlayer.objects.create(player=cls.p5, game=g1, power=cls.italy)

        # This one in Game 1 has no email address
        cls.p6 = Player.objects.create(first_name='Kevin',
                                       last_name='Lame')
        TournamentPlayer.objects.create(player=cls.p6, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p6, the_round=r)
        GamePlayer.objects.create(player=cls.p6, game=g1, power=cls.russia)

        cls.p7 = Player.objects.create(first_name='Michelle',
                                       last_name='Nobody',
                                       email = 'm.nobody@example.com')
        TournamentPlayer.objects.create(player=cls.p7, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p7, the_round=r)
        GamePlayer.objects.create(player=cls.p7, game=g2, power=cls.turkey)

        cls.p8 = Player.objects.create(first_name='Owen',
                                       last_name='Pennies',
                                       email = 'o.pennies@example.com')
        TournamentPlayer.objects.create(player=cls.p8, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p8, the_round=r)
        GamePlayer.objects.create(player=cls.p8, game=g2, power=cls.russia)

        cls.p9 = Player.objects.create(first_name='Queenie',
                                       last_name='Radiation',
                                       email = 'q.radiation@example.com')
        TournamentPlayer.objects.create(player=cls.p9, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p9, the_round=r)
        GamePlayer.objects.create(player=cls.p9, game=g2, power=cls.italy)

        cls.p10 = Player.objects.create(first_name='Sebastian',
                                        last_name='Twinkie',
                                        email = 's.twinkie@example.com')
        TournamentPlayer.objects.create(player=cls.p10, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p10, the_round=r)
        GamePlayer.objects.create(player=cls.p10, game=g2, power=cls.germany)

        cls.p11 = Player.objects.create(first_name='Ursula',
                                        last_name='Valentine',
                                        email = 'u.valentine@example.com')
        TournamentPlayer.objects.create(player=cls.p11, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p11, the_round=r)
        GamePlayer.objects.create(player=cls.p11, game=g2, power=cls.france)

        # This one is in the Tournament and the Round, but not any Games
        cls.p12 = Player.objects.create(first_name='Wallace',
                                        last_name='Xavier',
                                        email = 'w.xavier@example.com')
        TournamentPlayer.objects.create(player=cls.p12, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p12, the_round=r)

        # This one is playing in two Games and has an email address
        cls.p13 = Player.objects.create(first_name='Yugo',
                                        last_name='Zombie',
                                        email = 'y.zombie@example.com')
        TournamentPlayer.objects.create(player=cls.p13, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p13, the_round=r)
        GamePlayer.objects.create(player=cls.p13, game=g1, power=cls.turkey)
        GamePlayer.objects.create(player=cls.p13, game=g2, power=cls.austria)

        # This one in Game 2 and Game 3 has no email address
        cls.p14 = Player.objects.create(first_name='Arthur',
                                        last_name='Bottom')
        TournamentPlayer.objects.create(player=cls.p14, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p14, the_round=r)
        GamePlayer.objects.create(player=cls.p14, game=g2, power=cls.england)
        GamePlayer.objects.create(player=cls.p14, game=g3, power=cls.austria)

        # This one has an email address, is in the Tournament, but not this Round
        cls.p15 = Player.objects.create(first_name='Charlotte',
                                        last_name='Dromedary',
                                        email = 'c.dromedary@example.com')
        TournamentPlayer.objects.create(player=cls.p15, tournament=cls.t1)

        # This one has an email address but is not in the Tournament
        cls.p16 = Player.objects.create(first_name='Edward',
                                        last_name='Fancypants',
                                        email = 'e.fancypant@example.com')

        # Game 3 has no players with email addresses at all
        cls.p17 = Player.objects.create(first_name='Geraldine',
                                        last_name='Hogwash')
        TournamentPlayer.objects.create(player=cls.p17, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p17, the_round=r)
        GamePlayer.objects.create(player=cls.p17, game=g3, power=cls.austria)

        cls.p18 = Player.objects.create(first_name='Idiot',
                                        last_name='Jalopy')
        TournamentPlayer.objects.create(player=cls.p18, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p18, the_round=r)
        GamePlayer.objects.create(player=cls.p18, game=g3, power=cls.austria)

        cls.p19 = Player.objects.create(first_name='Keith',
                                        last_name='Llama')
        TournamentPlayer.objects.create(player=cls.p19, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p19, the_round=r)
        GamePlayer.objects.create(player=cls.p19, game=g3, power=cls.austria)

        cls.p20 = Player.objects.create(first_name='Markus',
                                        last_name='Nucleotide')
        TournamentPlayer.objects.create(player=cls.p20, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p20, the_round=r)
        GamePlayer.objects.create(player=cls.p20, game=g3, power=cls.austria)

        cls.p21 = Player.objects.create(first_name='Olivia',
                                        last_name='Petticoat')
        TournamentPlayer.objects.create(player=cls.p21, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p21, the_round=r)
        GamePlayer.objects.create(player=cls.p21, game=g3, power=cls.austria)

        cls.p22 = Player.objects.create(first_name='Quentin',
                                        last_name='Radish')
        TournamentPlayer.objects.create(player=cls.p22, tournament=cls.t1)
        RoundPlayer.objects.create(player=cls.p22, the_round=r)
        GamePlayer.objects.create(player=cls.p22, game=g3, power=cls.austria)

        # Tournament with preferences
        # All t2 Players have email addresses
        cls.t2 = Tournament.objects.create(name='t2',
                                           start_date=now,
                                           end_date=now,
                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                           tournament_scoring_system=T_SCORING_SYSTEMS[0].name,
                                           draw_secrecy=SECRET,
                                           power_assignment=PREFERENCES)

        # One TournamentPlayer in t2
        cls.p23 = Player.objects.create(first_name='Shirley',
                                        last_name='Turkey',
                                        email='s.turkey@example.com')
        tp = TournamentPlayer.objects.create(player=cls.p23, tournament=cls.t2)
        # Explicitly call save() to generate UUID
        tp.save()

        # One unused Player
        cls.p24 = Player.objects.create(first_name='Ulysses',
                                        last_name='Vitamin',
                                        email='u.vitamin@example.com')

    # send_board_call()
    def test_send_board_call(self):
        r = Round.objects.first()
        send_board_call(r)
        # 3 Games, but one where no players has an email address, so we expect to send 2 emails
        self.assertEqual(len(mail.outbox), 2)
        for m in mail.outbox:
            # Both should be "from" the TD
            self.assertEqual(m.from_email, self.td_email)
            # Both should have just the TD in "To:"
            self.assertEqual(len(m.to), 1)
            self.assertEqual(m.to[0], self.td_email)
            # Both should have nobody in "CC:"
            self.assertEqual(len(m.cc), 0)
            # Player emails should be in "BCC:"
            self.assertEqual(len(m.bcc), 6)
            # p13 should get both emails (playing both games)
            self.assertIn(self.p13.email, m.bcc)
            # p16 shouldn't get any email (not in Tournament)
            self.assertNotIn(self.p16.email, m.bcc)
            # p15 shouldn't get any email (not in Round)
            self.assertNotIn(self.p15.email, m.bcc)
            # p12 shouldn't get any email (not in any Game in the Round)
            self.assertNotIn(self.p12.email, m.bcc)

    # send_prefs_email()
    def test_send_prefs_email_no_prefs_done(self):
        # We need a TournamentPlayer from t1 and a Player with an email address
        tp = self.t1.tournamentplayer_set.get(player=self.p15)
        send_prefs_email(tp)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_prefs_email_no_prefs_new(self):
        tp = TournamentPlayer.objects.create(player=self.p24,
                                             tournament=self.t1)
        tp.save()
        self.assertEqual(len(mail.outbox), 0)

    def test_send_prefs_email_no_prefs_force(self):
        tp = self.t1.tournamentplayer_set.get(player=self.p15)
        send_prefs_email(tp, force=True)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_prefs_email_prefs_done(self):
        tp = self.t2.tournamentplayer_set.first()
        send_prefs_email(tp)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_prefs_email_prefs_new(self):
        tp = TournamentPlayer.objects.create(player=self.p24,
                                             tournament=self.t2)
        tp.save()
        self.assertEqual(len(mail.outbox), 1)
        tp.delete()

    def test_send_prefs_email_prefs_force(self):
        tp = self.t2.tournamentplayer_set.first()
        send_prefs_email(tp, force=True)
        self.assertEqual(len(mail.outbox), 1)
