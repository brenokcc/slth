# Generated by Django 4.2.6 on 2024-07-04 07:16

from django.db import migrations, models
import slth
import slth.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_profissionalsaude_zoom_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', slth.db.models.CharField(max_length=255, verbose_name='UUID')),
                ('nome', slth.db.models.CharField(max_length=255, verbose_name='Nome')),
                ('data', models.DateTimeField(verbose_name='Data')),
                ('arquivo', slth.db.models.FileField(upload_to='documentos', verbose_name='Arquivo')),
            ],
            options={
                'verbose_name': 'Documento',
                'verbose_name_plural': 'Documentos',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.AddField(
            model_name='profissionalsaude',
            name='vidaas_token',
            field=slth.db.models.TextField(blank=True, null=True, verbose_name='Vidaas Token'),
        ),
        migrations.AlterField(
            model_name='atendimento',
            name='duracao',
            field=slth.db.models.IntegerField(choices=[(20, '20min'), (40, '40min'), (60, '1h')], default=20, null=True, verbose_name='Duração'),
        ),
    ]