# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-17 05:35
from __future__ import unicode_literals

from django.db import migrations, models
import tournament.diplomacy
import tournament.models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0005_auto_20171101_1049'),
    ]

    operations = [
        migrations.AddField(
            model_name='drawproposal',
            name='votes_in_favour',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[tournament.models.validate_vote_count]),
        ),
        migrations.AddField(
            model_name='tournament',
            name='draw_secrecy',
            field=models.CharField(choices=[('S', 'Pass/Fail'), ('C', 'Numbers for and against')], default='S', max_length=1, verbose_name='What players are told about failed draw votes'),
        ),
        migrations.AlterField(
            model_name='drawproposal',
            name='passed',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='gameset',
            name='initial_image',
            field=models.ImageField(upload_to=tournament.diplomacy.utils.game_image_location),
        ),
        migrations.AlterField(
            model_name='round',
            name='scoring_system',
            field=models.CharField(choices=[('CDiplo 100', 'CDiplo 100'), ('CDiplo 80', 'CDiplo 80'), ('Carnage with dead equal', 'Carnage with dead equal'), ('Draw size', 'Draw size'), ('Solo or bust', 'Solo or bust'), ('Sum of Squares', 'Sum of Squares')], help_text='How to calculate a score for one game', max_length=40, verbose_name='Game scoring system'),
        ),
    ]
