# Generated by Django 5.1.3 on 2024-12-03 15:42

import django.db.models.deletion
import slth
import slth.db.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slth', '0010_email_key_alter_email_action_alter_email_attempt_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTimeZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', slth.db.models.CharField(max_length=255, verbose_name='Fuso Horário')),
                ('user', slth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Fuso Horário do Usuário',
                'verbose_name_plural': 'Fusos Horários do Usuário',
            },
            bases=(models.Model, slth.ModelMixin),
        ),
    ]
