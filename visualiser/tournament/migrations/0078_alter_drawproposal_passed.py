# Generated by Django 3.2.16 on 2023-01-01 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0077_auto_20221124_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drawproposal',
            name='passed',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
