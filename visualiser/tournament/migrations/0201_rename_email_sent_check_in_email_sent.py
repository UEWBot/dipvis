from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0200_round_seed_generation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='round',
            old_name='email_sent',
            new_name='check_in_email_sent',
        ),
        migrations.AlterField(
            model_name='round',
            name='check_in_email_sent',
            field=models.BooleanField(default=False, verbose_name='check-in email sent'),
        ),
    ]
