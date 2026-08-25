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
Forms for Awards in the Diplomacy Tournament Visualiser.
"""

from django import forms
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from tournament.models import (AwardRecipient, Game, TournamentAward,
                               TournamentPlayer)

from .fields import GameChoiceField, TournamentPlayerChoiceField


class AwardRecipientForm(forms.ModelForm):
    """Form to record one recipient of a TournamentAward, and optionally the Game it was for"""
    tournament_player = TournamentPlayerChoiceField(queryset=TournamentPlayer.objects.none())
    game = GameChoiceField(queryset=Game.objects.none(), required=False)

    class Meta:
        model = AwardRecipient
        fields = ['tournament_player', 'game']

    def __init__(self, *args, **kwargs):
        # Remove our special kwarg from the list
        self.tournament_award = kwargs.pop('tournament_award')
        super().__init__(*args, **kwargs)
        tournament = self.tournament_award.tournament
        self.fields['tournament_player'].queryset = tournament.tournamentplayer_set.filter(unranked=False)
        self.fields['game'].queryset = Game.objects.filter(the_round__tournament=tournament)


class BaseAwardRecipientFormSet(BaseInlineFormSet):
    """Inline formset of AwardRecipients for a single TournamentAward"""
    def get_form_kwargs(self, index):
        # Pass the special kwarg down to the form itself.
        # Used for both regular forms and the empty_form.
        kwargs = super().get_form_kwargs(index)
        kwargs['tournament_award'] = self.instance
        return kwargs


AwardRecipientFormSet = inlineformset_factory(TournamentAward,
                                              AwardRecipient,
                                              form=AwardRecipientForm,
                                              formset=BaseAwardRecipientFormSet,
                                              fields=['tournament_player', 'game'],
                                              extra=2,
                                              can_delete=True)

