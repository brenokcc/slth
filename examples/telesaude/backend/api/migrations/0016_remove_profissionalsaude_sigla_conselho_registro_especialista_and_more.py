# Generated by Django 4.2.6 on 2024-07-09 18:43

from django.db import migrations, models
import django.db.models.deletion
import slth
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_alter_profissionalsaude_uf_registro_especialista_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='sigla_conselho_registro_especialista',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='sigla_conselho_registro_profissional',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='uf_registro_especialista',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='uf_registro_profissional',
        ),
        migrations.CreateModel(
            name='ConselhoClasse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sigla', slth.db.models.CharField(max_length=20, unique=True, verbose_name='Sigla')),
                ('estado', slth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.estado', verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Conselho de Classe',
                'verbose_name_plural': 'Conselhos de Classe',
                'ordering': ['sigla'],
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.AddField(
            model_name='profissionalsaude',
            name='conselho_especialista',
            field=slth.db.models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='r3', to='api.conselhoclasse', verbose_name='Conselho de Especialista'),
        ),
        migrations.AddField(
            model_name='profissionalsaude',
            name='conselho_profissional',
            field=slth.db.models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.conselhoclasse', verbose_name='Conselho Profissional'),
        ),
    ]