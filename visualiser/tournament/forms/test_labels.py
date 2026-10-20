# Diplomacy Tournament Visualiser
# Copyright (C) 2026 Chris Brand
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
Form label translation Tests for the Diplomacy Tournament Visualiser.
"""
import inspect

from django import forms
from django.test import SimpleTestCase
from django.utils.functional import Promise

import tournament.forms


class FormLabelTests(SimpleTestCase):
    def test_class_level_labels_are_lazy(self):
        """
        Labels set when a form class is defined must be translated lazily.

        Otherwise they're translated once, in whatever language is active at import time.
        Labels that ModelForms take from model fields aren't checked here.
        """
        form_classes = [cls for _name, cls in inspect.getmembers(tournament.forms, inspect.isclass)
                        if issubclass(cls, forms.BaseForm)]
        self.assertTrue(form_classes)
        for cls in form_classes:
            for name, field in cls.declared_fields.items():
                with self.subTest(form=cls.__name__, field=name):
                    if field.label is not None:
                        self.assertIsInstance(field.label, Promise)
            meta = getattr(cls, '_meta', None)
            for name, label in (getattr(meta, 'labels', None) or {}).items():
                with self.subTest(form=cls.__name__, meta_label=name):
                    self.assertIsInstance(label, Promise)
