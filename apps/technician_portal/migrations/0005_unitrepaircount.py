# Generated by Django 5.1.1 on 2024-09-19 21:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('technician_portal', '0004_alter_repair_description_alter_repair_repair_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitRepairCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_number', models.CharField(max_length=50)),
                ('repair_count', models.IntegerField(default=0)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='technician_portal.customer')),
            ],
            options={
                'unique_together': {('customer', 'unit_number')},
            },
        ),
    ]
