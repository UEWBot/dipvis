# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-11 05:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0006_auto_20171116_2135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playeraward',
            name='tournament',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='playergameresult',
            name='tournament_name',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='playertournamentranking',
            name='tournament',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='name',
            field=models.CharField(max_length=60),
        ),
    ]
