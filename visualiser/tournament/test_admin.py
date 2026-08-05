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

from datetime import date, datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.forms import modelform_factory
from django.test import RequestFactory, TestCase

from tournament.admin import (GamePlayerAdmin, RoundAdmin, RoundPlayerAdmin,
                              TeamAdmin, TournamentAdmin,
                              TournamentPlayerAdmin)
from tournament.diplomacy import GameSet, GreatPower
from tournament.game_scoring import G_SCORING_SYSTEMS
from tournament.models import (NO_SCORING_SYSTEM_STR, R_SCORING_SYSTEMS, Award,
                               BestCountryCriteria, DrawSecrecy, Formats, Game,
                               GamePlayer, PowerAssignMethods, Round,
                               RoundPlayer, Team, Tournament, TournamentPlayer)
from tournament.players import Player

HOURS_24 = timedelta(hours=24)


class TournamentAdminTests(TestCase):
    fixtures = ['game_sets.json', 'players.json']

    def test_tournament_admin_form_incompatible_valid_scoring_systems(self):
        today = date.today()
        manager = User.objects.create_user(username='admin-form-manager')
        award = Award.objects.create(name='Admin Form Award',
                                     description='Used by admin form test')
        admin_form_cls = TournamentAdmin(Tournament, AdminSite()).get_form(request=None)
        form = admin_form_cls(data={'name': 'Incompatible scoring systems admin',
                                    'start_date': today,
                                    'end_date': today,
                                    'team_size': '',
                                    'num_games_in_team_score': '',
                                    'seed_games': 'on',
                                    'power_assignment': PowerAssignMethods.AUTO,
                                    'tournament_scoring_system': 'Sum all round scores',
                                    'handicaps': '',
                                    'round_scoring_system': NO_SCORING_SYSTEM_STR,
                                    'non_player_round_score': '0.0',
                                    'non_player_round_score_once': '',
                                    'show_current_scores': 'on',
                                    'draw_secrecy': DrawSecrecy.SECRET,
                                    'best_country_criterion': BestCountryCriteria.SCORE,
                                    'discord_url': '',
                                    'is_published': '',
                                    'delay_game_url_publication': '',
                                    'managers': [str(manager.pk)],
                                    'editable': 'on',
                                    'no_email': '',
                                    'wdd_tournament_id': '',
                                    'wdr_tournament_id': '',
                                    'awards': [str(award.pk)],
                                    'format': Formats.FTF,
                                    'location': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('round_scoring_system', form.errors)
        self.assertIn('tournament_scoring_system', form.errors)

    def test_tournament_admin_manager_can_change_uneditable_tournament_only(self):
        today = date.today()
        manager = User.objects.create_user(username='manage-admin-manager',
                                           is_staff=True)
        change_tournament_perm = Permission.objects.get(codename='change_tournament')
        change_round_perm = Permission.objects.get(codename='change_round')
        manager.user_permissions.add(change_tournament_perm)
        manager.user_permissions.add(change_round_perm)
        tournament = Tournament.objects.create(name='Manage admin permission test',
                                               start_date=today,
                                               end_date=today + HOURS_24,
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system='Sum all round scores',
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               editable=False)
        round_obj = Round.objects.create(tournament=tournament,
                                         scoring_system=G_SCORING_SYSTEMS[0].name,
                                         dias=True,
                                         start=datetime.combine(tournament.start_date,
                                                                time(hour=8, tzinfo=datetime_timezone.utc)))
        try:
            tournament.managers.add(manager)
            request = RequestFactory().get('/admin/tournament/tournament/')
            request.user = manager

            tournament_admin = TournamentAdmin(Tournament, AdminSite())
            round_admin = RoundAdmin(Round, AdminSite())

            self.assertTrue(tournament_admin.has_change_permission(request, tournament))
            self.assertFalse(round_admin.has_change_permission(request, round_obj))
        finally:
            tournament.delete()
            manager.delete()

    def test_tournament_admin_superuser_can_change_uneditable_tournament_only(self):
        today = date.today()
        superuser = User.objects.create_user(username='manage-admin-superuser',
                                             is_staff=True,
                                             is_superuser=True)
        tournament = Tournament.objects.create(name='Manage admin superuser permission test',
                                               start_date=today,
                                               end_date=today + HOURS_24,
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system='Sum all round scores',
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               editable=False)
        round_obj = Round.objects.create(tournament=tournament,
                                         scoring_system=G_SCORING_SYSTEMS[0].name,
                                         dias=True,
                                         start=datetime.combine(tournament.start_date,
                                                                time(hour=8, tzinfo=datetime_timezone.utc)))
        try:
            request = RequestFactory().get('/admin/tournament/tournament/')
            request.user = superuser

            tournament_admin = TournamentAdmin(Tournament, AdminSite())
            round_admin = RoundAdmin(Round, AdminSite())

            self.assertTrue(tournament_admin.has_change_permission(request, tournament))
            self.assertFalse(round_admin.has_change_permission(request, round_obj))
        finally:
            tournament.delete()
            superuser.delete()

    def test_tournament_admin_has_view_permission_published_for_non_manager(self):
        today = date.today()
        user = User.objects.create_user(username='admin-view-user',
                                        is_staff=True)
        view_perm = Permission.objects.get(codename='view_tournament')
        user.user_permissions.add(view_perm)
        tournament = Tournament.objects.create(name='Admin published visibility test',
                                               start_date=today,
                                               end_date=today + HOURS_24,
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system='Sum all round scores',
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               is_published=True)
        try:
            request = RequestFactory().get('/admin/tournament/tournament/')
            request.user = user
            admin_instance = TournamentAdmin(Tournament, AdminSite())
            self.assertTrue(admin_instance.has_view_permission(request, tournament))
        finally:
            tournament.delete()
            user.delete()

    def test_tournament_admin_has_view_permission_unpublished_is_limited(self):
        today = date.today()
        manager = User.objects.create_user(username='admin-view-manager',
                                           is_staff=True)
        other_user = User.objects.create_user(username='admin-view-non-manager',
                                              is_staff=True)
        superuser = User.objects.create_user(username='admin-view-superuser',
                                             is_staff=True,
                                             is_superuser=True)
        view_perm = Permission.objects.get(codename='view_tournament')
        manager.user_permissions.add(view_perm)
        other_user.user_permissions.add(view_perm)
        tournament = Tournament.objects.create(name='Admin unpublished visibility test',
                                               start_date=today,
                                               end_date=today + HOURS_24,
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system='Sum all round scores',
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               is_published=False)
        try:
            tournament.managers.add(manager)
            admin_instance = TournamentAdmin(Tournament, AdminSite())

            manager_request = RequestFactory().get('/admin/tournament/tournament/')
            manager_request.user = manager
            self.assertTrue(admin_instance.has_view_permission(manager_request, tournament))

            other_request = RequestFactory().get('/admin/tournament/tournament/')
            other_request.user = other_user
            self.assertFalse(admin_instance.has_view_permission(other_request, tournament))

            superuser_request = RequestFactory().get('/admin/tournament/tournament/')
            superuser_request.user = superuser
            self.assertTrue(admin_instance.has_view_permission(superuser_request, tournament))
        finally:
            tournament.delete()
            manager.delete()
            other_user.delete()
            superuser.delete()

    def test_score_model_admin_view_hidden_scores_limited_to_managers(self):
        today = date.today()
        manager = User.objects.create_user(username='score-view-manager',
                                           is_staff=True)
        other_user = User.objects.create_user(username='score-view-non-manager',
                                              is_staff=True)
        superuser = User.objects.create_user(username='score-view-superuser',
                                             is_staff=True,
                                             is_superuser=True)

        tournament = Tournament.objects.create(name='Hidden score visibility test',
                                               start_date=today,
                                               end_date=today + HOURS_24,
                                               round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                               tournament_scoring_system='Sum all round scores',
                                               draw_secrecy=DrawSecrecy.SECRET,
                                               is_published=True,
                                               show_current_scores=False,
                                               team_size=2)

        player = Player.objects.create(first_name='Score',
                                       last_name='Viewer')
        tp = TournamentPlayer.objects.create(tournament=tournament,
                                             player=player)
        round_obj = Round.objects.create(tournament=tournament,
                                         scoring_system=G_SCORING_SYSTEMS[0].name,
                                         dias=True,
                                         start=datetime.combine(tournament.start_date,
                                                                time(hour=8, tzinfo=datetime_timezone.utc)))
        rp = RoundPlayer.objects.create(the_round=round_obj,
                                        player=player)
        game = Game.objects.create(name='ScoreVisibilityGame',
                                   started_at=round_obj.start,
                                   the_round=round_obj,
                                   the_set=GameSet.objects.first())
        gp = GamePlayer.objects.create(game=game,
                                       player=player,
                                       power=GreatPower.objects.get(abbreviation='A'))
        team = Team.objects.create(tournament=tournament,
                                   name='Team Visibility')

        view_tp_perm = Permission.objects.get(codename='view_tournamentplayer')
        view_rp_perm = Permission.objects.get(codename='view_roundplayer')
        view_gp_perm = Permission.objects.get(codename='view_gameplayer')
        view_team_perm = Permission.objects.get(codename='view_team')
        manager.user_permissions.add(view_tp_perm, view_rp_perm, view_gp_perm, view_team_perm)
        other_user.user_permissions.add(view_tp_perm, view_rp_perm, view_gp_perm, view_team_perm)

        try:
            tournament.managers.add(manager)

            checks = [
                ('tournament player', TournamentPlayerAdmin(TournamentPlayer, AdminSite()), tp),
                ('round player', RoundPlayerAdmin(RoundPlayer, AdminSite()), rp),
                ('game player', GamePlayerAdmin(GamePlayer, AdminSite()), gp),
                ('team', TeamAdmin(Team, AdminSite()), team),
            ]

            manager_request = RequestFactory().get('/admin/tournament/')
            manager_request.user = manager
            other_request = RequestFactory().get('/admin/tournament/')
            other_request.user = other_user
            superuser_request = RequestFactory().get('/admin/tournament/')
            superuser_request.user = superuser

            for label, admin_instance, obj in checks:
                with self.subTest(model=label, user='manager'):
                    self.assertTrue(admin_instance.has_view_permission(manager_request, obj))
                with self.subTest(model=label, user='non-manager'):
                    self.assertFalse(admin_instance.has_view_permission(other_request, obj))
                with self.subTest(model=label, user='superuser'):
                    self.assertTrue(admin_instance.has_view_permission(superuser_request, obj))
        finally:
            team.delete()
            gp.delete()
            game.delete()
            rp.delete()
            round_obj.delete()
            tp.delete()
            player.delete()
            tournament.delete()
            manager.delete()
            other_user.delete()
            superuser.delete()

    def test_score_model_admin_queryset_hides_hidden_scores_for_non_managers(self):
        today = date.today()
        manager = User.objects.create_user(username='score-list-manager',
                                           is_staff=True)
        other_user = User.objects.create_user(username='score-list-non-manager',
                                              is_staff=True)
        superuser = User.objects.create_user(username='score-list-superuser',
                                             is_staff=True,
                                             is_superuser=True)

        hidden_tournament = Tournament.objects.create(name='Hidden score list test',
                                                      start_date=today,
                                                      end_date=today + HOURS_24,
                                                      round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                      tournament_scoring_system='Sum all round scores',
                                                      draw_secrecy=DrawSecrecy.SECRET,
                                                      is_published=True,
                                                      show_current_scores=False,
                                                      team_size=2)
        visible_tournament = Tournament.objects.create(name='Visible score list test',
                                                       start_date=today,
                                                       end_date=today + HOURS_24,
                                                       round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                       tournament_scoring_system='Sum all round scores',
                                                       draw_secrecy=DrawSecrecy.SECRET,
                                                       is_published=True,
                                                       show_current_scores=True,
                                                       team_size=2)

        hidden_player = Player.objects.create(first_name='Hidden',
                                              last_name='Player')
        visible_player = Player.objects.create(first_name='Visible',
                                               last_name='Player')

        hidden_tp = TournamentPlayer.objects.create(tournament=hidden_tournament,
                                                    player=hidden_player)
        visible_tp = TournamentPlayer.objects.create(tournament=visible_tournament,
                                                     player=visible_player)

        hidden_round = Round.objects.create(tournament=hidden_tournament,
                                            scoring_system=G_SCORING_SYSTEMS[0].name,
                                            dias=True,
                                            start=datetime.combine(hidden_tournament.start_date,
                                                                   time(hour=8, tzinfo=datetime_timezone.utc)))
        visible_round = Round.objects.create(tournament=visible_tournament,
                                             scoring_system=G_SCORING_SYSTEMS[0].name,
                                             dias=True,
                                             start=datetime.combine(visible_tournament.start_date,
                                                                    time(hour=9, tzinfo=datetime_timezone.utc)))

        hidden_rp = RoundPlayer.objects.create(the_round=hidden_round,
                                               player=hidden_player)
        visible_rp = RoundPlayer.objects.create(the_round=visible_round,
                                                player=visible_player)

        hidden_game = Game.objects.create(name='HiddenScoreGame',
                                          started_at=hidden_round.start,
                                          the_round=hidden_round,
                                          the_set=GameSet.objects.first())
        visible_game = Game.objects.create(name='VisibleScoreGame',
                                           started_at=visible_round.start,
                                           the_round=visible_round,
                                           the_set=GameSet.objects.first())

        hidden_gp = GamePlayer.objects.create(game=hidden_game,
                                              player=hidden_player,
                                              power=GreatPower.objects.get(abbreviation='A'))
        visible_gp = GamePlayer.objects.create(game=visible_game,
                                               player=visible_player,
                                               power=GreatPower.objects.get(abbreviation='E'))

        hidden_team = Team.objects.create(tournament=hidden_tournament,
                                          name='Hidden Team')
        visible_team = Team.objects.create(tournament=visible_tournament,
                                           name='Visible Team')

        view_tp_perm = Permission.objects.get(codename='view_tournamentplayer')
        view_rp_perm = Permission.objects.get(codename='view_roundplayer')
        view_gp_perm = Permission.objects.get(codename='view_gameplayer')
        view_team_perm = Permission.objects.get(codename='view_team')
        manager.user_permissions.add(view_tp_perm, view_rp_perm, view_gp_perm, view_team_perm)
        other_user.user_permissions.add(view_tp_perm, view_rp_perm, view_gp_perm, view_team_perm)

        try:
            hidden_tournament.managers.add(manager)

            checks = [
                ('tournament player', TournamentPlayerAdmin(TournamentPlayer, AdminSite()), hidden_tp, visible_tp),
                ('round player', RoundPlayerAdmin(RoundPlayer, AdminSite()), hidden_rp, visible_rp),
                ('game player', GamePlayerAdmin(GamePlayer, AdminSite()), hidden_gp, visible_gp),
                ('team', TeamAdmin(Team, AdminSite()), hidden_team, visible_team),
            ]

            manager_request = RequestFactory().get('/admin/tournament/')
            manager_request.user = manager
            other_request = RequestFactory().get('/admin/tournament/')
            other_request.user = other_user
            superuser_request = RequestFactory().get('/admin/tournament/')
            superuser_request.user = superuser

            for label, admin_instance, hidden_obj, visible_obj in checks:
                with self.subTest(model=label, user='manager'):
                    q = admin_instance.get_queryset(manager_request)
                    self.assertIn(hidden_obj.pk, list(q.values_list('pk', flat=True)))
                    self.assertIn(visible_obj.pk, list(q.values_list('pk', flat=True)))

                with self.subTest(model=label, user='non-manager'):
                    q = admin_instance.get_queryset(other_request)
                    self.assertNotIn(hidden_obj.pk, list(q.values_list('pk', flat=True)))
                    self.assertIn(visible_obj.pk, list(q.values_list('pk', flat=True)))

                with self.subTest(model=label, user='superuser'):
                    q = admin_instance.get_queryset(superuser_request)
                    self.assertIn(hidden_obj.pk, list(q.values_list('pk', flat=True)))
                    self.assertIn(visible_obj.pk, list(q.values_list('pk', flat=True)))
        finally:
            hidden_tournament.delete()
            visible_tournament.delete()
            hidden_player.delete()
            visible_player.delete()
            manager.delete()
            other_user.delete()
            superuser.delete()

    def test_round_admin_queryset_hides_unpublished_for_non_managers(self):
        today = date.today()
        manager = User.objects.create_user(username='round-list-manager',
                                           is_staff=True)
        other_user = User.objects.create_user(username='round-list-non-manager',
                                              is_staff=True)
        superuser = User.objects.create_user(username='round-list-superuser',
                                             is_staff=True,
                                             is_superuser=True)

        published_tournament = Tournament.objects.create(name='Published round list test',
                                                         start_date=today,
                                                         end_date=today + HOURS_24,
                                                         round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                         tournament_scoring_system='Sum all round scores',
                                                         draw_secrecy=DrawSecrecy.SECRET,
                                                         is_published=True)
        unpublished_tournament = Tournament.objects.create(name='Unpublished round list test',
                                                           start_date=today,
                                                           end_date=today + HOURS_24,
                                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                           tournament_scoring_system='Sum all round scores',
                                                           draw_secrecy=DrawSecrecy.SECRET,
                                                           is_published=False)

        published_round = Round.objects.create(tournament=published_tournament,
                                               scoring_system=G_SCORING_SYSTEMS[0].name,
                                               dias=True,
                                               start=datetime.combine(published_tournament.start_date,
                                                                      time(hour=8, tzinfo=datetime_timezone.utc)))
        unpublished_round = Round.objects.create(tournament=unpublished_tournament,
                                                 scoring_system=G_SCORING_SYSTEMS[0].name,
                                                 dias=True,
                                                 start=datetime.combine(unpublished_tournament.start_date,
                                                                        time(hour=9, tzinfo=datetime_timezone.utc)))

        view_round_perm = Permission.objects.get(codename='view_round')
        manager.user_permissions.add(view_round_perm)
        other_user.user_permissions.add(view_round_perm)

        try:
            unpublished_tournament.managers.add(manager)
            admin_instance = RoundAdmin(Round, AdminSite())

            manager_request = RequestFactory().get('/admin/tournament/round/')
            manager_request.user = manager
            other_request = RequestFactory().get('/admin/tournament/round/')
            other_request.user = other_user
            superuser_request = RequestFactory().get('/admin/tournament/round/')
            superuser_request.user = superuser

            manager_ids = list(admin_instance.get_queryset(manager_request).values_list('pk', flat=True))
            self.assertIn(published_round.pk, manager_ids)
            self.assertIn(unpublished_round.pk, manager_ids)

            other_ids = list(admin_instance.get_queryset(other_request).values_list('pk', flat=True))
            self.assertIn(published_round.pk, other_ids)
            self.assertNotIn(unpublished_round.pk, other_ids)

            superuser_ids = list(admin_instance.get_queryset(superuser_request).values_list('pk', flat=True))
            self.assertIn(published_round.pk, superuser_ids)
            self.assertIn(unpublished_round.pk, superuser_ids)
        finally:
            unpublished_tournament.delete()
            published_tournament.delete()
            manager.delete()
            other_user.delete()
            superuser.delete()

    def test_tournament_admin_queryset_hides_unpublished_for_non_managers(self):
        today = date.today()
        manager = User.objects.create_user(username='tournament-list-manager',
                                           is_staff=True)
        other_user = User.objects.create_user(username='tournament-list-non-manager',
                                              is_staff=True)
        superuser = User.objects.create_user(username='tournament-list-superuser',
                                             is_staff=True,
                                             is_superuser=True)

        published_tournament = Tournament.objects.create(name='Published tournament list test',
                                                         start_date=today,
                                                         end_date=today + HOURS_24,
                                                         round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                         tournament_scoring_system='Sum all round scores',
                                                         draw_secrecy=DrawSecrecy.SECRET,
                                                         is_published=True)
        unpublished_tournament = Tournament.objects.create(name='Unpublished tournament list test',
                                                           start_date=today,
                                                           end_date=today + HOURS_24,
                                                           round_scoring_system=R_SCORING_SYSTEMS[0].name,
                                                           tournament_scoring_system='Sum all round scores',
                                                           draw_secrecy=DrawSecrecy.SECRET,
                                                           is_published=False)

        try:
            unpublished_tournament.managers.add(manager)
            admin_instance = TournamentAdmin(Tournament, AdminSite())

            manager_request = RequestFactory().get('/admin/tournament/tournament/')
            manager_request.user = manager
            other_request = RequestFactory().get('/admin/tournament/tournament/')
            other_request.user = other_user
            superuser_request = RequestFactory().get('/admin/tournament/tournament/')
            superuser_request.user = superuser

            manager_ids = list(admin_instance.get_queryset(manager_request).values_list('pk', flat=True))
            self.assertIn(published_tournament.pk, manager_ids)
            self.assertIn(unpublished_tournament.pk, manager_ids)

            other_ids = list(admin_instance.get_queryset(other_request).values_list('pk', flat=True))
            self.assertIn(published_tournament.pk, other_ids)
            self.assertNotIn(unpublished_tournament.pk, other_ids)

            superuser_ids = list(admin_instance.get_queryset(superuser_request).values_list('pk', flat=True))
            self.assertIn(published_tournament.pk, superuser_ids)
            self.assertIn(unpublished_tournament.pk, superuser_ids)
        finally:
            published_tournament.delete()
            unpublished_tournament.delete()
            manager.delete()
            other_user.delete()
            superuser.delete()
