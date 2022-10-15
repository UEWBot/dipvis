# Generated by Django 2.2 on 2022-10-12 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0070_game_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=2000, null=True)),
                ('slug', models.SlugField(unique=True)),
                ('tournaments', models.ManyToManyField(to='tournament.Tournament')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]