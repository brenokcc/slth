# Generated by Django 4.2.6 on 2024-06-16 12:47

from django.db import migrations
import django.db.models.deletion
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_remove_atendimento_horario_especialista_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nucleo',
            name='estados',
        ),
        migrations.RemoveField(
            model_name='nucleo',
            name='municipios',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='estados',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='informar_atuacao',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='municipios',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='pode_atualizar_agenda',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='teleconsultor',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='teleinterconsultor',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='unidades',
        ),
        migrations.AddField(
            model_name='pessoafisica',
            name='cpf_responsavel',
            field=slth.db.models.CharField(blank=True, max_length=14, null=True, verbose_name='CPF do Responsável'),
        ),
        migrations.AddField(
            model_name='pessoafisica',
            name='nome_responsavel',
            field=slth.db.models.CharField(blank=True, max_length=80, null=True, verbose_name='Nome do Responsável'),
        ),
        migrations.AlterField(
            model_name='atendimento',
            name='duracao',
            field=slth.db.models.IntegerField(choices=[(30, '30min'), (60, '1h'), (90, '1h30min')], null=True, verbose_name='Duração'),
        ),
        migrations.AlterField(
            model_name='nucleo',
            name='unidades',
            field=slth.db.models.ManyToManyField(blank=True, to='api.unidade', verbose_name='Unidades Atendidas'),
        ),
        migrations.AlterField(
            model_name='profissionalsaude',
            name='pessoa_fisica',
            field=slth.db.models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.pessoafisica', verbose_name='Pessoa Física'),
        ),
    ]