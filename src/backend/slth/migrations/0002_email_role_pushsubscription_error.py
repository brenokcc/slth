# Generated by Django 4.1 on 2024-03-16 23:08

from django.conf import settings
from django.db import migrations
from slth.db import models
import slth


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('slth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_email', models.EmailField(max_length=254, verbose_name='Remetente')),
                ('to', models.TextField(help_text='Separar endereços de e-mail por ",".', verbose_name='Destinatário')),
                ('subject', models.CharField(max_length=255, verbose_name='Assunto')),
                ('content', models.TextField(verbose_name='Conteúdo')),
                ('sent_at', models.DateTimeField(null=True, verbose_name='Data/Hora')),
            ],
            options={
                'verbose_name': 'E-mail',
                'verbose_name_plural': 'E-mails',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('scope', models.CharField(db_index=True, max_length=50, null=True)),
                ('model', models.CharField(db_index=True, max_length=50, null=True)),
                ('value', models.IntegerField(db_index=True, null=True, verbose_name='Value')),
                ('active', models.BooleanField(default=True, null=True, verbose_name='Active')),
            ],
            options={
                'verbose_name': 'Papel',
                'verbose_name_plural': 'Papéis',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device', models.CharField(max_length=255, verbose_name='Dispositivo')),
                ('data', models.JSONField(verbose_name='Dados da Inscrição')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Inscrição de Notificação',
                'verbose_name_plural': 'Inscrições de Notificação',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(verbose_name='Data/Hora')),
                ('traceback', models.TextField(verbose_name='Rastreamento')),
                ('user', models.OneToOneField(null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Erro',
                'verbose_name_plural': 'Erros',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
    ]
