# Generated by Django 2.2 on 2022-03-29 02:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0060_auto_20220328_1904'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seederbias',
            name='weight',
        ),
    ]
