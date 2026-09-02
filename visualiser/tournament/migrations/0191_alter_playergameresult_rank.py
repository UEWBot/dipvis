from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0190_circuittournamentresult'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playergameresult',
            name='rank',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]