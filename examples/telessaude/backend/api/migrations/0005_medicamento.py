# Generated by Django 4.2.6 on 2024-07-15 21:29

from django.db import migrations, models
import slth
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_tipoexame_tuss_alter_tipoexame_detalhe_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Medicamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', slth.db.models.CharField(max_length=255, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Medicamento',
                'verbose_name_plural': 'Medicamentos',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
    ]