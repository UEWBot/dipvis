# Generated by Django 2.2.16 on 2021-02-12 03:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0046_auto_20210209_1937'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='powerbid',
            unique_together={('player', 'power', 'the_round')},
        ),
    ]
