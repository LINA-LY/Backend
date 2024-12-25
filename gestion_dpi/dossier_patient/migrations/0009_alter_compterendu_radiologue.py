# Generated by Django 5.1.4 on 2024-12-25 12:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dossier_patient', '0008_alter_soin_infirmier'),
        ('utilisateurs', '0010_alter_ordonnance_dpi_patient_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compterendu',
            name='radiologue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compte_rendus', to='utilisateurs.radiologue'),
        ),
    ]
