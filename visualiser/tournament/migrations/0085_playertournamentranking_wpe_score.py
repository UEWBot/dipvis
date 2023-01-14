# Generated by Django 3.2.16 on 2023-02-09 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0084_dbncoverage'),
    ]

    operations = [
        migrations.AddField(
            model_name='playertournamentranking',
            name='wpe_score',
            field=models.FloatField(blank=True, help_text='World Performance Evaluation score', null=True),
        ),
    ]
