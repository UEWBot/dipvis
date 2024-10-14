# Generated by Django 4.2.16 on 2024-10-14 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0117_alter_tournament_round_scoring_system'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='round',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('earliest_end_time__isnull', True), ('latest_end_time__isnull', True)), ('latest_end_time__gte', models.F('earliest_end_time')), _connector='OR'), name='round_end_times_valid'),
        ),
    ]
