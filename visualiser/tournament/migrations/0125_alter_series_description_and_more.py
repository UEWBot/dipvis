# Generated by Django 4.2.16 on 2024-11-23 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0124_gameimage_phase_season_combo_valid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='series',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tournament',
            name='discord_url',
            field=models.URLField(blank=True, default='', help_text='Board calls will be posted here', verbose_name='Discord webhook URL'),
            preserve_default=False,
        ),
    ]
