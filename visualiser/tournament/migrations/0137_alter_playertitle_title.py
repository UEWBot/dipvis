# Generated by Django 4.2.16 on 2025-01-22 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0136_player_wdr_player_id_playeraward_wdr_tournament_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playertitle',
            name='title',
            field=models.CharField(max_length=50),
        ),
    ]
