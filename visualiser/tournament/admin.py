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

from django.contrib import admin
from django.db.models import Q

from tournament.circuits import Circuit, CircuitPlayer, CircuitSeries
from tournament.diplomacy import GameSet, GreatPower, SetPower, SupplyCentre
from tournament.forms import CircuitPlayerAdminForm
from tournament.models import (Award, AwardRecipient, CentreCount,
                               DBNCoverage, DrawProposal, Game, GameImage,
                               GamePlayer, Pool, Round, RoundPlayer,
                               SeederBias, Series, SupplyCentreOwnership,
                               Team, Tournament, TournamentAward,
                               TournamentPlayer)
from tournament.players import (Player, PlayerAward, PlayerEventRanking,
                                PlayerGameResult, PlayerRanking, PlayerTitle,
                                WDDPlayer)


class TournamentPermissionAdminMixin:
    """Shared object-level permission checks for tournament-scoped models."""

    # How do we find the Tournament corresponding to obj?
    tournament_attr = 'tournament'

    def get_tournament_for_permission(self, obj):
        """Return the Tournament associated with obj."""
        tournament = obj
        for attr in self.tournament_attr.split('.'):
            tournament = getattr(tournament, attr)
        return tournament

    def has_tournament_change_permission(self, request, obj, tournament):
        """Hook for model-specific object-level change checks."""
        return tournament.can_be_changed_by(request.user)

    def has_tournament_view_permission(self, request, obj, tournament):
        """Hook for model-specific object-level view checks."""
        return tournament.can_be_viewed_by(request.user)

    def has_view_permission(self, request, obj=None):
        """Check admin permission plus Tournament-level visibility constraints."""
        # Generic permissions for unspecified obj
        if not super().has_view_permission(request, None):
            return False
        if obj is None:
            return True

        # Specific permissions for objects in a given tournament
        tournament = self.get_tournament_for_permission(obj)
        return self.has_tournament_view_permission(request, obj, tournament)

    def has_change_permission(self, request, obj=None):
        """Check admin permission plus Tournament-level constraints for action."""
        # Generic permissions for unspecified obj
        if not super().has_change_permission(request, None):
            return False
        if obj is None:
            return True

        # Specific permissions for objects in a given tournament
        tournament = self.get_tournament_for_permission(obj)
        return self.has_tournament_change_permission(request, obj, tournament)

    def has_delete_permission(self, request, obj=None):
        """Check admin permission plus Tournament-level constraints for action."""
        # Generic permissions for unspecified obj
        if not super().has_delete_permission(request, None):
            return False
        if obj is None:
            return True

        # Specific permissions for objects in a given tournament
        tournament = self.get_tournament_for_permission(obj)
        return tournament.can_be_deleted_by(request.user)

    def get_queryset(self, request):
        """Limit changelist rows to tournaments visible to the request user."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        t_attr = self.tournament_attr.replace('.', '__')
        return qs.filter(
            Q(**{f'{t_attr}__managers': request.user}) |
            Q(**{f'{t_attr}__is_published': True})
        ).distinct()


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_filter = ['power']
    ordering = ['name']


@admin.register(AwardRecipient)
class AwardRecipientAdmin(admin.ModelAdmin):
    list_filter = ['tournament_award__tournament', 'tournament_award__award']
    ordering = ['tournament_award']


class TournamentAwardInline(admin.TabularInline):
    model = TournamentAward
    extra = 0


@admin.register(CentreCount)
class CentreCountAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'year']
    tournament_attr = 'game.the_round.tournament'
    ordering = ['game', 'year']


@admin.register(CircuitPlayer)
class CircuitPlayerAdmin(admin.ModelAdmin):
    form = CircuitPlayerAdminForm
    list_filter = ['circuit', 'player']
    ordering = ['circuit', 'player']


@admin.register(CircuitSeries)
class CircuitSeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    ordering = ['name']


@admin.register(DBNCoverage)
class DBNCoverageAdmin(admin.ModelAdmin):
    list_filter = ['tournament']


@admin.register(DrawProposal)
class DrawProposalAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'passed', 'game', 'year']
    tournament_attr = 'game.the_round.tournament'
    ordering = ['game']


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 7
    fieldsets = [
        (None, {
            'fields': ['player', 'power', 'tie_break_rank', 'score']
        }),
    ]


class ScoreVisibilityAdminMixin(TournamentPermissionAdminMixin):
    """Restrict score visibility for non-managers when current scores are hidden."""

    def has_tournament_view_permission(self, request, obj, tournament):
        if (not tournament.show_current_scores) and (not tournament.can_be_managed_by(request.user)):
            return False
        return super().has_tournament_view_permission(request, obj, tournament)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        t_attr = self.tournament_attr.replace('.', '__')
        return qs.filter(
            Q(**{f'{t_attr}__managers': request.user}) |
            Q(**{f'{t_attr}__show_current_scores': True})
        ).distinct()


@admin.register(Game)
class GameAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    """Include GamePlayer, CentreCount, DrawProposal, and SCOwnership with Game"""
    fields = ['name', 'started_at', 'is_finished', 'is_top_board', 'the_round', 'the_set', 'external_url', 'notes']
    inlines = [GamePlayerInline]
    list_filter = ['the_round__tournament', 'name', 'is_finished']
    tournament_attr = 'the_round.tournament'
    ordering = ['the_round__tournament', 'name']


@admin.register(GameImage)
class GameImageAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'year', 'season', 'phase']
    tournament_attr = 'game.the_round.tournament'
    ordering = ['game', 'year', '-season', 'phase']


@admin.register(GamePlayer)
class GamePlayerAdmin(ScoreVisibilityAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'player']
    tournament_attr = 'game.the_round.tournament'
    ordering = ['game', 'power']


class SetPowerInline(admin.TabularInline):
    model = SetPower

    def get_extra(self, request, obj=None, **kwargs):
        if obj is not None:
            # Most likely we have the set we need
            return 0
        # We're going to want 7 set powers
        return 7


@admin.register(GameSet)
class GameSetAdmin(admin.ModelAdmin):
    """Include SetPower as part of GameSet"""
    inlines = [SetPowerInline]
    ordering = ['name']


class WDDPlayerInline(admin.TabularInline):
    model = WDDPlayer

    def get_extra(self, request, obj=None, **kwargs):
        """Returns the number of extra inline forms to display"""
        # The vast majority of Players only have one entry in the WDD
        if obj and obj.wddplayer_set.exists():
            return 0
        return 1


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    exclude = ['_wdd_firstname', '_wdd_lastname']
    list_filter = ['first_name', 'last_name']
    inlines = [WDDPlayerInline]
    ordering = ['last_name', 'first_name']


@admin.register(PlayerAward)
class PlayerAwardAdmin(admin.ModelAdmin):
    list_filter = ['player', 'event_ranking', 'name', 'power']
    ordering = ['event_ranking__event_name', 'player']


@admin.register(PlayerGameResult)
class PlayerGameResultAdmin(admin.ModelAdmin):
    list_filter = ['player', 'event_ranking', 'power', 'position', 'result']
    ordering = ['event_ranking__event_name', 'player']


@admin.register(PlayerRanking)
class PlayerRankingAdmin(admin.ModelAdmin):
    list_filter = ['system', 'player']
    ordering = ['player', 'system']


@admin.register(PlayerTitle)
class PlayerTitleAdmin(admin.ModelAdmin):
    list_filter = ['player', 'title', 'year']
    ordering = ['player', 'year']


@admin.register(PlayerEventRanking)
class PlayerEventRanking(admin.ModelAdmin):
    list_filter = ['player', 'event_name', 'position']
    ordering = ['event_name', 'player']


@admin.register(Pool)
class PoolAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['the_round__tournament']
    prepopulated_fields = {"slug": ["name"]}
    tournament_attr = 'the_round.tournament'
    ordering = ['-board_count']


@admin.register(Round)
class RoundAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament']
    tournament_attr = 'tournament'
    ordering = ['start']


@admin.register(RoundPlayer)
class RoundPlayerAdmin(ScoreVisibilityAdminMixin, admin.ModelAdmin):
    list_filter = ['the_round__tournament', 'the_round', 'player', 'game_count']
    tournament_attr = 'the_round.tournament'
    ordering = ['player', 'the_round__start']


@admin.register(SupplyCentreOwnership)
class SCOwnershipAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'owner', 'year']
    tournament_attr = 'game.the_round.tournament'
    ordering = ['game', 'year']


@admin.register(SeederBias)
class SeederBiasAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['player1__tournament']
    tournament_attr = 'player1.tournament'


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}
    ordering = ['name']


class RoundInline(admin.StackedInline):
    model = Round
    fieldsets = [
        (None, {
            'fields': ['start', 'scoring_system', 'dias', 'is_team_round']
        }),
        ('Round end options', {
            'classes': ['collapse'],
            'fields': ['final_year', 'earliest_end_time', 'latest_end_time']
        }),
    ]

    def get_extra(self, request, obj=None, **kwargs):
        if obj is not None:
            # "Add another Round" will be there anyway
            return 0
        return 3


@admin.register(Team)
class TeamAdmin(ScoreVisibilityAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament']
    tournament_attr = 'tournament'
    ordering = ['name']


@admin.register(Tournament)
class TournamentAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    """Include Round as part of Tournament"""
    inlines = [RoundInline, TournamentAwardInline]
    fields = (('name', 'format', 'location'),
              ('start_date', 'end_date'),
              ('team_size', 'num_games_in_team_score'),
              ('seed_games', 'default_game_set', 'power_assignment'),
              ('tournament_scoring_system', 'handicaps', 'round_scoring_system',
               'non_player_round_score', 'non_player_round_score_once'),
              ('show_current_scores', 'draw_secrecy', 'best_country_criterion'),
              ('discord_url', 'is_published', 'delay_game_url_publication'),
              ('managers', 'editable', 'no_email'),
              ('wdd_tournament_id', 'wdr_tournament_id'))
    ordering = ['-start_date']

    def get_tournament_for_permission(self, obj):
        return obj

    def get_queryset(self, request):
        """Tournament IS the tournament — filter directly on its own fields."""
        qs = admin.ModelAdmin.get_queryset(self, request)
        if request.user.is_superuser:
            return qs
        return qs.filter(
            Q(managers=request.user) | Q(is_published=True)
        ).distinct()

    def has_tournament_change_permission(self, request, obj, tournament):
        # Tournament managers may always edit the Tournament object itself,
        # including toggling editable.
        return tournament.can_be_managed_by(request.user)


@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(ScoreVisibilityAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament', 'player', 'location', 'unranked']
    tournament_attr = 'tournament'
    ordering = ['player']


@admin.register(WDDPlayer)
class WDDPlayerAdmin(admin.ModelAdmin):
    list_filter = ['player']
    ordering = ['player']


# Register models
admin.site.register(Circuit)
admin.site.register(GreatPower)
admin.site.register(SupplyCentre)
