# Generated by Django 3.2.24 on 2024-06-15 21:40

from django.db import migrations
import tournament.players
import tournament.wdd


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0108_auto_20240310_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='wdd_player_id',
            field=tournament.players.WDDPlayerIdField(blank=True, null=True, unique=True, validators=[tournament.wdd.validate_wdd_player_id], verbose_name='WDD player id'),
        ),
    ]
