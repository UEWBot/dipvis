# Generated by Django 3.2.18 on 2023-02-21 05:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0092_auto_20230220_2135'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='centrecount',
            constraint=models.CheckConstraint(check=models.Q(('year__gte', 1900)), name='centrecount_year_valid'),
        ),
        migrations.AddConstraint(
            model_name='centrecount',
            constraint=models.CheckConstraint(check=models.Q(('count__lte', 34)), name='centrecount_count_valid'),
        ),
        migrations.AddConstraint(
            model_name='drawproposal',
            constraint=models.CheckConstraint(check=models.Q(('year__gte', 1901)), name='drawproposal_year_valid'),
        ),
        migrations.AddConstraint(
            model_name='gameimage',
            constraint=models.CheckConstraint(check=models.Q(('year__gte', 1901)), name='gameimage_year_valid'),
        ),
        migrations.AddConstraint(
            model_name='playeraward',
            constraint=models.CheckConstraint(check=models.Q(('final_sc_count__lte', 34), ('final_sc_count__isnull', True), _connector='OR'), name='playeraward_final_sc_count_valid'),
        ),
        migrations.AddConstraint(
            model_name='playergameresult',
            constraint=models.CheckConstraint(check=models.Q(('final_sc_count__lte', 34), ('final_sc_count__isnull', True), _connector='OR'), name='playergameresult_final_sc_count_valid'),
        ),
        migrations.AddConstraint(
            model_name='playergameresult',
            constraint=models.CheckConstraint(check=models.Q(('year_eliminated__gte', 1901), ('year_eliminated__isnull', True), _connector='OR'), name='playergameresult_year_eliminated_valid'),
        ),
        migrations.AddConstraint(
            model_name='round',
            constraint=models.CheckConstraint(check=models.Q(('final_year__gte', 1901), ('final_year__isnull', True), _connector='OR'), name='round_final_year_valid'),
        ),
        migrations.AddConstraint(
            model_name='supplycentreownership',
            constraint=models.CheckConstraint(check=models.Q(('year__gte', 1900)), name='supplycentreownership_year_valid'),
        ),
    ]
