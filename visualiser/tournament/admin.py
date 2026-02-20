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

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.set_power import SetPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.models import (Award, CentreCount, DBNCoverage, DrawProposal,
                               Game, GameImage, GamePlayer, Pool, Round,
                               RoundPlayer, SeederBias, Series,
                               SupplyCentreOwnership, Team, Tournament,
                               TournamentPlayer)
from tournament.players import (Player, PlayerAward, PlayerGameResult,
                                PlayerRanking, PlayerTitle,
                                PlayerTournamentRanking, WDDPlayer)


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_filter = ['power']


@admin.register(CentreCount)
class CentreCountAdmin(admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'year']


@admin.register(DBNCoverage)
class DBNCoverageAdmin(admin.ModelAdmin):
    list_filter = ['tournament']


@admin.register(DrawProposal)
class DrawProposalAdmin(admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'passed', 'game', 'year']


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 7
    fieldsets = [
        (None, {
            'fields': ['player', 'power', 'score']
        }),
    ]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Include GamePlayer, CentreCount, DrawProposal, and SCOwnership with Game"""
    fields = ['name', 'started_at', 'is_finished', 'is_top_board', 'the_round', 'the_set', 'external_url', 'notes']
    inlines = [GamePlayerInline]
    list_filter = ['the_round__tournament', 'name', 'is_finished']


@admin.register(GameImage)
class GameImageAdmin(admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'year', 'season', 'phase']


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'power', 'game', 'player']


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


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    exclude = ['_wdd_firstname', '_wdd_lastname']
    list_filter = ['first_name', 'last_name']


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
class PoolAdmin(admin.ModelAdmin):
    list_filter = ['the_round__tournament']
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_filter = ['tournament']
    ordering = ['tournament__name', 'start']


@admin.register(RoundPlayer)
class RoundPlayerAdmin(admin.ModelAdmin):
    list_filter = ['the_round__tournament', 'the_round', 'player', 'game_count']

    # RoundPlayer.delete() needs to be called for each object
    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.delete()


@admin.register(SupplyCentreOwnership)
class SCOwnershipAdmin(admin.ModelAdmin):
    list_filter = ['game__the_round__tournament', 'game', 'owner', 'year']


@admin.register(SeederBias)
class SeederBiasAdmin(admin.ModelAdmin):
    list_filter = ['player1__tournament']


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
class TeamAdmin(admin.ModelAdmin):
    list_filter = ['tournament']


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """Include Round as part of Tournament"""
    inlines = [RoundInline]
    fields = (('name', 'format', 'location', 'team_size'),
              ('start_date', 'end_date'),
              ('seed_games', 'power_assignment'),
              ('tournament_scoring_system', 'handicaps', 'round_scoring_system',
               'non_player_round_score', 'non_player_round_score_once'),
              ('show_current_scores', 'draw_secrecy', 'best_country_criterion'),
              ('discord_url', 'is_published', 'delay_game_url_publication'),
              ('managers', 'editable', 'no_email'),
              ('wdd_tournament_id', 'wdr_tournament_id'),
              'awards')


@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(admin.ModelAdmin):
    list_filter = ['tournament', 'player', 'location', 'unranked']


@admin.register(WDDPlayer)
class WDDPlayerAdmin(admin.ModelAdmin):
    list_filter = ['player']


# Register models
admin.site.register(GreatPower)
admin.site.register(SupplyCentre)
