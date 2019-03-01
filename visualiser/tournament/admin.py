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

from tournament.diplomacy import GreatPower, GameSet, SetPower, SupplyCentre
from tournament.models import Tournament, Round, Game, TournamentPlayer, GamePlayer
from tournament.models import CentreCount, DrawProposal, GameImage, SupplyCentreOwnership
from tournament.models import RoundPlayer
from tournament.models import SeederBias
from tournament.players import Player, PlayerTournamentRanking, PlayerGameResult
from tournament.players import PlayerAward, PlayerRanking

class SetPowerInline(admin.TabularInline):
    model = SetPower

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            # Most likely we have the set we need
            return 0
        # We're going to want 7 set powers
        return 7

class GameSetAdmin(admin.ModelAdmin):
    """Include SetPower as part of GameSet"""
    inlines = [SetPowerInline]

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

class TournamentPlayerInline(admin.TabularInline):
    model = TournamentPlayer
    extra = 7

class TournamentAdmin(admin.ModelAdmin):
    """Include Round and TournamentPlayer as part of Tournament"""
    inlines = [RoundInline, TournamentPlayerInline]
    fields = ('name',
              ('start_date', 'end_date'),
              ('tournament_scoring_system', 'round_scoring_system'),
              ('seed_games', 'power_assignment'),
              'draw_secrecy',
              ('managers', 'is_published', 'editable'))

class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    fieldsets = (
        (None, {
            'fields': ('player', 'power', 'score')
        }),
        ('Replacement player options', {
            'classes': ('collapse',),
            'fields': ('first_season', 'first_year')
        }),
        ('Replaced player options', {
            'classes': ('collapse',),
            'fields': ('last_season', 'last_year')
        }),
    )
    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            # Replacement players are pretty rare
            # Let them click the button if needed
            return 0
        # We're going to want 7 players
        return 7

class CentreCountInline(admin.TabularInline):
    model = CentreCount
    extra = 7

class DrawProposalInline(admin.StackedInline):
    model = DrawProposal
    extra = 1
    fieldsets = (
        (None, {
            'fields': ('season', 'year', 'proposer', 'passed', 'votes_in_favour')
        }),
        ('Powers', {
            'fields': ('power_1', 'power_2', 'power_3', 'power_4', 'power_5', 'power_6', 'power_7')
        })
    )

class SCOwnershipInline(admin.TabularInline):
    model = SupplyCentreOwnership
    extra = 34

class GameAdmin(admin.ModelAdmin):
    """Include GamePlayer, CentreCount, DrawProposal, and SCOwnership with Game"""
    fields = ['the_round', 'name', 'is_top_board', 'started_at', 'is_finished']
    inlines = [GamePlayerInline, CentreCountInline, DrawProposalInline, SCOwnershipInline]

# Register models
admin.site.register(GameImage)
admin.site.register(GreatPower)
admin.site.register(SupplyCentre)
admin.site.register(GameSet, GameSetAdmin)
admin.site.register(Player)
admin.site.register(DrawProposal)
admin.site.register(CentreCount)
admin.site.register(TournamentPlayer)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(PlayerTournamentRanking)
admin.site.register(PlayerGameResult)
admin.site.register(PlayerAward)
admin.site.register(PlayerRanking)
admin.site.register(RoundPlayer)
admin.site.register(GamePlayer)
admin.site.register(SeederBias)
