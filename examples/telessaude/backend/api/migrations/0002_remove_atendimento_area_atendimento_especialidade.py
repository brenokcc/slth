# Generated by Django 4.2.6 on 2024-07-14 21:55

from django.db import migrations
import django.db.models.deletion
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='atendimento',
            name='area',
        ),
        migrations.AddField(
            model_name='atendimento',
            name='especialidade',
            field=slth.db.models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='api.especialidade', verbose_name='Especialidade'),
            preserve_default=False,
        ),
    ]
