# Generated by Django 4.2.6 on 2024-07-10 13:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_remove_profissionalsaude_sigla_conselho_registro_especialista_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='atendimento',
            name='termo_assinado_especialista',
        ),
        migrations.RemoveField(
            model_name='atendimento',
            name='termo_assinado_paciente',
        ),
        migrations.RemoveField(
            model_name='atendimento',
            name='termo_assinado_profissional',
        ),
        migrations.RemoveField(
            model_name='profissionalsaude',
            name='vidaas_token',
        ),
    ]
