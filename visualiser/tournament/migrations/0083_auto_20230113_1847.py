# Generated by Django 3.2.16 on 2023-01-14 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0082_alter_tournament_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameplayer',
            name='score_dropped',
            field=models.BooleanField(default=False, help_text='Set if this score does not contribute towards the round score'),
        ),
        migrations.AddField(
            model_name='roundplayer',
            name='score_dropped',
            field=models.BooleanField(default=False, help_text='Set if this score does not contribute towards the tournament score'),
        ),
    ]
