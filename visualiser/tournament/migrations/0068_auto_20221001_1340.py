# Generated by Django 2.2 on 2022-10-01 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0067_tournament_delay_game_url_publication'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='notes',
            new_name='external_url',
        ),
        migrations.AlterField(
            model_name='tournament',
            name='delay_game_url_publication',
            field=models.BooleanField(default=False, help_text='Check to keep game URL secret until after the tournament completes', verbose_name='Delay publishing game URL'),
        ),
    ]