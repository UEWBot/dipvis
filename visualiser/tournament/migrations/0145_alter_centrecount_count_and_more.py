# Generated by Django 4.2.20 on 2025-04-19 18:03

import django.core.validators
from django.db import migrations, models
import tournament.diplomacy.tasks.validate_max_greatpowers
import tournament.diplomacy.tasks.validate_max_supplycentres


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0144_alter_centrecount_count_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='centrecount',
            name='count',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(tournament.diplomacy.tasks.validate_max_supplycentres.num_supplycentres)]),
        ),
        migrations.AlterField(
            model_name='drawproposal',
            name='votes_in_favour',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(tournament.diplomacy.tasks.validate_max_greatpowers.num_greatpowers)]),
        ),
        migrations.AlterField(
            model_name='playergameresult',
            name='final_sc_count',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(tournament.diplomacy.tasks.validate_max_supplycentres.num_supplycentres)]),
        ),
        migrations.AlterField(
            model_name='preference',
            name='ranking',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(tournament.diplomacy.tasks.validate_max_greatpowers.num_greatpowers)]),
        ),
    ]
