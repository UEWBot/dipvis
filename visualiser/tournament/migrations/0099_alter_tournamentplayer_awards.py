# Generated by Django 3.2.19 on 2023-10-02 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0098_alter_round_scoring_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournamentplayer',
            name='awards',
            field=models.ManyToManyField(blank=True, to='tournament.Award'),
        ),
    ]
