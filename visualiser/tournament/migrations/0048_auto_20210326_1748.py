# Generated by Django 2.2.16 on 2021-03-27 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0047_auto_20210211_1958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='round',
            name='scoring_system',
            field=models.CharField(choices=[('CDiplo 100', 'CDiplo 100'), ('CDiplo 80', 'CDiplo 80'), ('Carnage with dead equal', 'Carnage with dead equal'), ('Carnage with elimination order', 'Carnage with elimination order'), ('Center-count Carnage', 'Center-count Carnage'), ('Draw size', 'Draw size'), ('Janus', 'Janus'), ('ManorCon', 'ManorCon'), ('Solo or bust', 'Solo or bust'), ('Sum of Squares', 'Sum of Squares'), ('Tribute', 'Tribute'), ('Whipping', 'Whipping'), ('World Classic', 'World Classic')], help_text='How to calculate a score for one game', max_length=40, verbose_name='Game scoring system'),
        ),
    ]
