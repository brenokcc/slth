# Generated by Django 4.2.7 on 2024-04-17 09:04

from django.db import migrations
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_escolaridade_esfera_nivelensino_orgao_poder_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='municipio',
            name='latitude',
            field=slth.db.models.CharField(blank=True, max_length=255, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='municipio',
            name='longitude',
            field=slth.db.models.CharField(blank=True, max_length=255, null=True, verbose_name='Longitude'),
        ),
    ]
