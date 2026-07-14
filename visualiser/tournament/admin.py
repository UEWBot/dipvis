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
from django.db import transaction

from tournament.diplomacy import GameSet, GreatPower, SetPower, SupplyCentre
from tournament.models import (Award, CentreCount, DBNCoverage, DrawProposal,
                               Game, GameImage, GamePlayer, Pool, Round,
                               RoundPlayer, SeederBias, Series,
                               SupplyCentreOwnership, Team, Tournament,
                               TournamentPlayer)
from tournament.players import (Player, PlayerAward, PlayerGameResult,
                                PlayerRanking, PlayerTitle,
                                PlayerTournamentRanking, WDDPlayer)


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

    def has_view_permission(self, request, obj=None):
        """Check admin permission plus Tournament-level visibility constraints."""
        # Generic permissions for unspecified obj
        if not super().has_view_permission(request, None):
            return False
        if obj is None:
            return True

        # Specific permissions for objects in a given tournament
        tournament = self.get_tournament_for_permission(obj)
        return tournament.can_be_viewed_by(request.user)

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


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_filter = ['power']


@admin.register(CentreCount)
class CentreCountAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'year']
    tournament_attr = 'game.the_round.tournament'


@admin.register(DBNCoverage)
class DBNCoverageAdmin(admin.ModelAdmin):
    list_filter = ['tournament']


@admin.register(DrawProposal)
class DrawProposalAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'passed', 'game', 'year']
    tournament_attr = 'game.the_round.tournament'


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 7
    fieldsets = [
        (None, {
            'fields': ['player', 'power', 'tie_break_rank', 'score']
        }),
    ]


@admin.register(Game)
class GameAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    """Include GamePlayer, CentreCount, DrawProposal, and SCOwnership with Game"""
    fields = ['name', 'started_at', 'is_finished', 'is_top_board', 'the_round', 'the_set', 'external_url', 'notes']
    inlines = [GamePlayerInline]
    list_filter = ['the_round__tournament', 'name', 'is_finished']
    tournament_attr = 'the_round.tournament'


@admin.register(GameImage)
class GameImageAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'year', 'season', 'phase']
    tournament_attr = 'game.the_round.tournament'


@admin.register(GamePlayer)
class GamePlayerAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'player']
    tournament_attr = 'game.the_round.tournament'


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


@admin.register(PlayerAward)
class PlayerAwardAdmin(admin.ModelAdmin):
    list_filter = ['player', 'tournament', 'name', 'power']


@admin.register(PlayerGameResult)
class PlayerGameResultAdmin(admin.ModelAdmin):
    list_filter = ['player', 'tournament_name', 'power', 'position', 'result']


@admin.register(PlayerRanking)
class PlayerRankingAdmin(admin.ModelAdmin):
    list_filter = ['system', 'player']


@admin.register(PlayerTitle)
class PlayerTitleAdmin(admin.ModelAdmin):
    list_filter = ['player', 'title', 'year']


@admin.register(PlayerTournamentRanking)
class PlayerTournamentRankingAdmin(admin.ModelAdmin):
    list_filter = ['player', 'tournament', 'position', 'year']


@admin.register(Pool)
class PoolAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['the_round__tournament']
    prepopulated_fields = {"slug": ["name"]}
    tournament_attr = 'the_round.tournament'


@admin.register(Round)
class RoundAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament']
    ordering = ['tournament__name', 'start']
    tournament_attr = 'tournament'


@admin.register(RoundPlayer)
class RoundPlayerAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['the_round__tournament', 'the_round', 'player', 'game_count']
    tournament_attr = 'the_round.tournament'

    # RoundPlayer.delete() needs to be called for each object
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()

@admin.register(SupplyCentreOwnership)
class SCOwnershipAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'owner', 'year']
    tournament_attr = 'game.the_round.tournament'


@admin.register(SeederBias)
class SeederBiasAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['player1__tournament']
    tournament_attr = 'player1.tournament'


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}


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
class TeamAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament']
    tournament_attr = 'tournament'


@admin.register(Tournament)
class TournamentAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    """Include Round as part of Tournament"""
    inlines = [RoundInline]
    fields = (('name', 'format', 'location'),
              ('start_date', 'end_date'),
              ('team_size', 'num_games_in_team_score'),
              ('seed_games', 'power_assignment'),
              ('tournament_scoring_system', 'handicaps', 'round_scoring_system',
               'non_player_round_score', 'non_player_round_score_once'),
              ('show_current_scores', 'draw_secrecy', 'best_country_criterion'),
              ('discord_url', 'is_published', 'delay_game_url_publication'),
              ('managers', 'editable', 'no_email'),
              ('wdd_tournament_id', 'wdr_tournament_id'),
              'awards')

    def get_tournament_for_permission(self, obj):
        return obj

    def has_tournament_change_permission(self, request, obj, tournament):
        # Tournament managers may always edit the Tournament object itself,
        # including toggling editable.
        return tournament.can_be_managed_by(request.user)


@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(TournamentPermissionAdminMixin, admin.ModelAdmin):
    list_filter = ['tournament', 'player', 'location', 'unranked']
    tournament_attr = 'tournament'


@admin.register(WDDPlayer)
class WDDPlayerAdmin(admin.ModelAdmin):
    list_filter = ['player']


# Register models
admin.site.register(GreatPower)
admin.site.register(SupplyCentre)
