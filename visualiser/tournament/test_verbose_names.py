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
Model verbose name Tests for the Diplomacy Tournament Visualiser.
"""
from django.apps import apps
from django.test import SimpleTestCase
from django.utils.functional import Promise


class VerboseNameTests(SimpleTestCase):
    """
    Names shown in the admin (and in ModelForms) should be translatable.

    Django's default verbose names, derived from the code, are never translated.
    """

    def test_models_have_lazy_verbose_names(self):
        for model in apps.get_app_config('tournament').get_models():
            for attr in ('verbose_name', 'verbose_name_plural'):
                with self.subTest(model=model.__name__, attr=attr):
                    self.assertIsInstance(model._meta.original_attrs.get(attr), Promise)

    def test_fields_have_lazy_verbose_names(self):
        for model in apps.get_app_config('tournament').get_models():
            for field in model._meta.get_fields():
                if field.auto_created or not (field.concrete or field.many_to_many):
                    continue
                kwargs = field.deconstruct()[3]
                with self.subTest(model=model.__name__, field=field.name):
                    self.assertIsInstance(kwargs.get('verbose_name'), Promise)
                    if kwargs.get('help_text'):
                        self.assertIsInstance(kwargs['help_text'], Promise)
