# Generated by Django 3.2.16 on 2023-02-11 19:11

from django.db import migrations, models
import tournament.models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0086_alter_tournament_tournament_scoring_system'),
    ]

    operations = [
        migrations.AlterField(
            model_name='round',
            name='scoring_system',
            field=models.CharField(choices=[('7Eleven', '7Eleven'), ('Bangkok', 'Bangkok'), ('CDiplo 100', 'CDiplo 100'), ('CDiplo 80', 'CDiplo 80'), ('Carnage with dead equal', 'Carnage with dead equal'), ('Carnage with elimination order', 'Carnage with elimination order'), ('Center-count Carnage', 'Center-count Carnage'), ('Detour09', 'Detour09'), ('Draw size', 'Draw size'), ('ManorCon', 'ManorCon'), ('ManorCon v2', 'ManorCon v2'), ('Maxonian', 'Maxonian'), ('OMG', 'OMG'), ('OpenTribute', 'OpenTribute'), ('Original ManorCon', 'Original ManorCon'), ('Solo or bust', 'Solo or bust'), ('Sum of Squares', 'Sum of Squares'), ('Tribute', 'Tribute'), ('Whipping', 'Whipping'), ('World Classic', 'World Classic')], help_text='How to calculate a score for one game', max_length=40, validators=[tournament.models.validate_game_scoring_system], verbose_name='Game scoring system'),
        ),
    ]