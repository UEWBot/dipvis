# Generated by Django 2.2 on 2021-02-06 02:46

from django.db import migrations, models
import django.db.models.deletion
import tournament.models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0041_tournament_no_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='power_assignment',
            field=models.CharField(choices=[('A', 'Minimising playing the same power'), ('M', 'Manually by TD or at the board'), ('P', 'Using player preferences and ranking'), ('B', 'Blind auction')], default='M', max_length=1, verbose_name='How powers are assigned'),
        ),
        migrations.CreateModel(
            name='PowerBid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bid', models.PositiveSmallIntegerField(validators=[tournament.models.validate_bid])),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.TournamentPlayer')),
                ('power', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.GreatPower')),
            ],
            options={
                'ordering': ['-bid'],
                'unique_together': {('player', 'power')},
            },
        ),
    ]
