# Generated by Django 4.2.6 on 2024-05-22 04:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_atendimento_assunto_alter_atendimento_duvida_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UnidadeOrganizacional',
            new_name='Nucleo',
        ),
    ]
