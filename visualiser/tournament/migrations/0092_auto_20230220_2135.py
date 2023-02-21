# Generated by Django 3.2.18 on 2023-02-21 05:35

from django.db import migrations, models
import tournament.diplomacy.tasks.validate_sc_count


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0091_auto_20230217_1405'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dbncoverage',
            options={'verbose_name_plural': 'DBN coverages'},
        ),
        migrations.AlterField(
            model_name='playergameresult',
            name='final_sc_count',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[tournament.diplomacy.tasks.validate_sc_count.validate_sc_count]),
        ),
    ]
