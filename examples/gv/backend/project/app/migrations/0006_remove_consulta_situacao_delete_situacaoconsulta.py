# Generated by Django 4.2.7 on 2024-04-22 06:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_situacaoconsulta_cor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='consulta',
            name='situacao',
        ),
        migrations.DeleteModel(
            name='SituacaoConsulta',
        ),
    ]