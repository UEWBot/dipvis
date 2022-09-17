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

from tournament.diplomacy.models.game_set import GameSet
from tournament.diplomacy.models.great_power import GreatPower
from tournament.diplomacy.models.set_power import SetPower
from tournament.diplomacy.models.supply_centre import SupplyCentre
from tournament.models import Tournament, Round, Game, TournamentPlayer, GamePlayer
from tournament.models import CentreCount, DrawProposal, GameImage, SupplyCentreOwnership
from tournament.models import PowerBid, RoundPlayer
from tournament.models import SeederBias
from tournament.players import Player, PlayerTournamentRanking, PlayerGameResult
from tournament.players import PlayerAward, PlayerRanking

class SetPowerInline(admin.TabularInline):
    model = SetPower

    def get_extra(self, request, obj=None, **kwargs):
        if obj is not None:
            # Most likely we have the set we need
            return 0
        # We're going to want 7 set powers
        return 7

class GameSetAdmin(admin.ModelAdmin):
    """Include SetPower as part of GameSet"""
    inlines = [SetPowerInline]

class RoundAdmin(admin.ModelAdmin):
    list_filter = ('tournament',)
    ordering = ['tournament__name', 'start']

class RoundInline(admin.StackedInline):
    model = Round
    extra = 4
    fieldsets = (
        (None, {
            'fields': ('start', 'scoring_system', 'dias')
        }),
        ('Round end options', {
            'classes': ('collapse',),
            'fields': ('final_year', 'earliest_end_time', 'latest_end_time')
        }),
    )

class TournamentAdmin(admin.ModelAdmin):
    """Include Round as part of Tournament"""
    inlines = [RoundInline]
    fields = (('name', 'format', 'location'),
              ('start_date', 'end_date'),
              ('tournament_scoring_system', 'round_scoring_system'),
              ('seed_games', 'power_assignment'),
              ('draw_secrecy', 'best_country_criterion'),
              ('managers', 'is_published', 'editable'),
              'no_email',
              'wdd_tournament_id')

class TournamentPlayerAdmin(admin.ModelAdmin):
    list_filter = ('tournament', 'player', 'location', 'unranked')

class RoundPlayerAdmin(admin.ModelAdmin):
    list_filter = ('the_round__tournament', 'the_round', 'player', 'game_count')

class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    fieldsets = (
        (None, {
            'fields': ('player', 'power', 'score')
        }),
    )
    def get_extra(self, request, obj=None, **kwargs):
        # We're going to want 7 players
        return 7

class GamePlayerAdmin(admin.ModelAdmin):
    list_filter = ('game__the_round__tournament', 'power', 'game', 'player')

class CentreCountAdmin(admin.ModelAdmin):
    list_filter = ('game__the_round__tournament', 'power', 'game', 'year')

class DrawProposalAdmin(admin.ModelAdmin):
    list_filter = ('game__the_round__tournament', 'passed', 'game', 'year')
    fieldsets = (
        (None, {
            'fields': ('game', 'season', 'year', 'proposer', 'passed', 'votes_in_favour')
        }),
        ('Powers', {
            'fields': ('power_1', 'power_2', 'power_3', 'power_4', 'power_5', 'power_6', 'power_7')
        })
    )

class SCOwnershipAdmin(admin.ModelAdmin):
    list_filter = ('game__the_round__tournament', 'game', 'owner', 'year')

class GameAdmin(admin.ModelAdmin):
    """Include GamePlayer, CentreCount, DrawProposal, and SCOwnership with Game"""
    fields = ['the_round', 'name', 'notes', 'is_top_board', 'started_at', 'is_finished']
    inlines = [GamePlayerInline]
    list_filter = ('the_round__tournament', 'name', 'is_finished')

class GameImageAdmin(admin.ModelAdmin):
    list_filter = ('game__the_round__tournament', 'game', 'year', 'season', 'phase')

class PlayerAdmin(admin.ModelAdmin):
    exclude = ('_wdd_name',)
    list_filter = ('first_name', 'last_name')

class PowerBidAdmin(admin.ModelAdmin):
    list_filter = ('player__tournament', 'the_round', 'player__player')

class SeederBiasAdmin(admin.ModelAdmin):
    list_filter = ('player1__tournament', )

class PlayerTournamentRankingAdmin(admin.ModelAdmin):
    list_filter = ('player', 'tournament', 'position', 'year', 'title')

class PlayerGameResultAdmin(admin.ModelAdmin):
    list_filter = ('player', 'tournament_name', 'power', 'position', 'result')

class PlayerAwardAdmin(admin.ModelAdmin):
    list_filter = ('player', 'tournament', 'name', 'power')

class PlayerRankingAdmin(admin.ModelAdmin):
    list_filter = ('system', 'player')

# Register models
admin.site.register(GameImage, GameImageAdmin)
admin.site.register(GreatPower)
admin.site.register(SupplyCentre)
admin.site.register(GameSet, GameSetAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(DrawProposal, DrawProposalAdmin)
admin.site.register(CentreCount, CentreCountAdmin)
admin.site.register(SupplyCentreOwnership, SCOwnershipAdmin)
admin.site.register(TournamentPlayer, TournamentPlayerAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(PlayerTournamentRanking, PlayerTournamentRankingAdmin)
admin.site.register(PlayerGameResult, PlayerGameResultAdmin)
admin.site.register(PlayerAward, PlayerAwardAdmin)
admin.site.register(PlayerRanking, PlayerRankingAdmin)
admin.site.register(PowerBid, PowerBidAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(RoundPlayer, RoundPlayerAdmin)
admin.site.register(GamePlayer, GamePlayerAdmin)
admin.site.register(SeederBias, SeederBiasAdmin)
