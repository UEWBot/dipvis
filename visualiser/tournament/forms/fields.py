# Diplomacy Tournament Visualiser
# Copyright (C) 2014, 2016-2026 Chris Brand
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

"""
Fields for the Diplomacy Tournament Visualiser.
"""

from django import forms


class PlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a Player"""
    def label_from_instance(self, obj):
        return obj.sortable_str()


class RoundPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a RoundPlayer"""
    def __init__(self, *args, **kwargs):
        self.flag_sandboxers = kwargs.pop('flag_sandboxers', False)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        # optionally flag if they are willing to sandbox
        suffix = ''
        if self.flag_sandboxers and obj.sandboxer:
            suffix = '*'
        return obj.player.sortable_str() + suffix


class TournamentPlayerChoiceField(forms.ModelChoiceField):
    """Field to pick a TournamentPlayer"""
    def label_from_instance(self, obj):
        return obj.player.sortable_str()


class TournamentPlayerMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Field to pick TournamentPlayers"""
    def label_from_instance(self, obj):
        return obj.player.sortable_str()
