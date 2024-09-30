# Generated by Django 5.1.1 on 2024-09-29 22:32

import django.db.models.deletion
import slth
import slth.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slth', '0009_remove_email_from_email_email_action_email_attempt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='key',
            field=slth.db.models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='action',
            field=slth.db.models.CharField(max_length=255, null=True, verbose_name='Action'),
        ),
        migrations.AlterField(
            model_name='email',
            name='attempt',
            field=slth.db.models.IntegerField(default=0, verbose_name='Attempt'),
        ),
        migrations.AlterField(
            model_name='email',
            name='content',
            field=slth.db.models.TextField(verbose_name='Content'),
        ),
        migrations.AlterField(
            model_name='email',
            name='error',
            field=slth.db.models.TextField(null=True, verbose_name='Error'),
        ),
        migrations.AlterField(
            model_name='email',
            name='send_at',
            field=slth.db.models.DateTimeField(null=True, verbose_name='Send at'),
        ),
        migrations.AlterField(
            model_name='email',
            name='sent_at',
            field=slth.db.models.DateTimeField(null=True, verbose_name='Sent at'),
        ),
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=slth.db.models.CharField(max_length=255, verbose_name='Subject'),
        ),
        migrations.AlterField(
            model_name='email',
            name='to',
            field=slth.db.models.TextField(help_text='Separated by space', verbose_name='To'),
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', slth.db.models.CharField(db_index=True, max_length=255, verbose_name='Nome')),
                ('start', slth.db.models.DateTimeField(null=True, verbose_name='Início')),
                ('finish', slth.db.models.DateTimeField(null=True, verbose_name='Fim')),
                ('canceled', models.BooleanField(default=False, verbose_name='Cancelada')),
                ('attempt', slth.db.models.IntegerField(default=0, verbose_name='Tentativa')),
                ('task', slth.db.models.TaskFied(verbose_name='Tarefa')),
                ('total', slth.db.models.IntegerField(default=0, verbose_name='Total')),
                ('partial', slth.db.models.IntegerField(default=0, verbose_name='Parcial')),
                ('success', models.BooleanField(null=True, verbose_name='Successo')),
                ('error', slth.db.models.TextField(null=True, verbose_name='Erro')),
                ('user', slth.db.models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='slth.user', verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Tarefa',
                'verbose_name_plural': 'Tarefas',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
        migrations.CreateModel(
            name='PushNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', slth.db.models.CharField(max_length=255, verbose_name='Subject')),
                ('message', slth.db.models.TextField(verbose_name='Content')),
                ('url', slth.db.models.CharField(max_length=255, null=True, verbose_name='URL')),
                ('send_at', slth.db.models.DateTimeField(null=True, verbose_name='Send at')),
                ('sent_at', slth.db.models.DateTimeField(null=True, verbose_name='Sent at')),
                ('attempt', slth.db.models.IntegerField(default=0, verbose_name='Attempt')),
                ('error', slth.db.models.TextField(null=True, verbose_name='Error')),
                ('key', slth.db.models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('to', slth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slth.user', verbose_name='To')),
            ],
            options={
                'verbose_name': 'Push Notification',
                'verbose_name_plural': 'Push Notifications',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
    ]
