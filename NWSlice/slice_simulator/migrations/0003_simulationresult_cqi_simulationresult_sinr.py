# Generated by Django 5.1.7 on 2025-03-15 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slice_simulator', '0002_simulationresult_jitter_simulationresult_latency_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulationresult',
            name='cqi',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='simulationresult',
            name='sinr',
            field=models.FloatField(default=0),
        ),
    ]
