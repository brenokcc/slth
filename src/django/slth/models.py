import os
import json
import pytz
import binascii
from uuid import uuid1
import traceback
from . import timezone
from .db import models, meta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction
from django.apps import apps
from datetime import datetime
from django.core.cache import cache
from django.utils.html import strip_tags
from django.core import serializers
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .notifications import send_push_web_notification, send_whatsapp_notification
from .components import HtmlContent
from slth.application import Application as ApplicationConfig
from django.contrib.auth.models import BaseUserManager


class UserQuerySet(BaseUserManager):

    def all(self):
        return (
            self.
            search("username", "email")
            .filters("is_superuser", "is_active")
            .fields("username", "email", "get_roles")
            .actions(
                "user.add",
                "user.view",
                "user.edit",
                "user.delete",
                "user.sendpushnotification",
                "user.changepassword",
                "auth.loginas",
            )
        )


class User(User):
    
    class Meta:
        icon = 'users'
        proxy = True
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    objects = UserQuerySet()

    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', (('first_name', 'last_name'), 'email'))
            .fieldset('Dados de Acesso', ('username', ('is_superuser', 'is_active'),))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', (('first_name', 'last_name'), 'email'))
            .fieldset('Dados de Acesso', (('username', 'get_timezone'), ('is_superuser', 'is_active'),))
            .queryset('get_push_subscriptions')
            .queryset('get_roles')
        )
    
    @meta('Inscrições de Notificação')
    def get_push_subscriptions(self):
        return self.pushsubscription_set.fields('device')
    
    def send_push_notification(self, title, message, url=None):
        send_push_web_notification(self, title, message, url=url)
    
    @meta('Papéis')
    def get_roles(self):
        return Role.objects.filter(username=self.username).fields('get_description')
    
    @meta('Fuso Horário')
    def get_timezone(self):
        user_timezone = self.usertimezone_set.first()
        return user_timezone.timezone.name if user_timezone else None



class RoleFilter(models.Filter):
    def __init__(self, username_field):
        self.username_field = username_field

    def get_label(self):
        return 'Papel'

    def choices(self, queryset, term=None):
        application = ApplicationConfig.get_instance()
        return [(k, v) for k, v in application.groups.items()]
     
    def filter(self, queryset, value):
        if value:
            usernames = Role.objects.filter(name=value).values_list('username', flat=True)
            queryset = queryset.filter(**{f'{self.username_field}__in': usernames})
        return queryset


class RoleUserFilter(models.Filter):
    def get_label(self):
        return 'Usuário'
    
    def choices(self, queryset, term=None):
        if term:
            queryset = queryset.filter(username__icontains=term)
        usernames = queryset.values_list('username', flat=True).distinct()
        return User.objects.filter(username__in=usernames)
     
    def filter(self, queryset, value):
        if value:
            queryset = queryset.filter(username=User.objects.get(pk=value).username)
        return queryset

class RoleQuerySet(models.QuerySet):

    def all(self):
        return self.fields('username', 'get_verbose_name', 'get_scope_value').filters(user=RoleUserFilter())

    def contains(self, *names):
        _names = getattr(self, '_names', None)
        if _names is None:
            _names = set(self.filter(name__in=names, active=True).values_list('name', flat=True))
            setattr(self, '_names', _names)
        for name in names:
            if name in _names:
                return True
        return False

    def active(self):
        return self.filter(active=True)

    def inactive(self):
        return self.filter(active=False)
    
    def debug(self):
        print('------- ROLES -----------')
        print('USERNAME\tNAME\tSCOPE')
        for role in self:
            print('{}\t{}\t{}'.format(role.username, role.name, role.get_scope_value()))
        print('-------------------------')

class Role(models.Model):
    username = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=50, db_index=True)
    scope = models.CharField(max_length=50, db_index=True, null=True)
    model = models.CharField(max_length=50, db_index=True, null=True)
    value = models.IntegerField('Value', db_index=True, null=True)
    active = models.BooleanField('Active', default=True, null=True)

    objects = RoleQuerySet()

    class Meta:
        verbose_name = 'Papel'
        verbose_name_plural = 'Papéis'

    def __str__(self):
        return self.get_description()

    def get_verbose_name(self):
        application = ApplicationConfig.get_instance()
        return application.groups.get(self.name, self.name)

    def get_scope_value(self):
        return apps.get_model(self.model).objects.filter(pk=self.value).first() if self.model else None

    @meta('Descrição')
    def get_description(self):
        scope_value = self.get_scope_value()
        return '{} - {}'.format(self.get_verbose_name(), scope_value) if scope_value else self.get_verbose_name()


class PushSubscription(models.Model):
    user = models.ForeignKey('auth.user', verbose_name='Usuário', on_delete=models.CASCADE)
    device = models.CharField(verbose_name='Dispositivo')
    data = models.JSONField(verbose_name='Dados da Inscrição')

    class Meta:
        icon = "mail-bulk"
        verbose_name = 'Inscrição de Notificação'
        verbose_name_plural = 'Inscrições de Notificação'

    def notify(self, text):
        import os
        from pywebpush import webpush
        specification = API.instance()
        response = webpush(
            subscription_info=self.data, data='{}>>>{}'.format(specification.title, text),
            vapid_private_key=os.environ.get('VAPID_PRIVATE_KEY'),
            vapid_claims={"sub": "mailto:admin@admin.com"}
        )
        return response.status_code == 201


class ErrorManager(models.Manager):
    pass


class Error(models.Model):
    user = models.OneToOneField('auth.user', verbose_name='Usuário', on_delete=models.CASCADE, null=True)
    date = models.DateTimeField('Data/Hora')
    traceback = models.TextField('Rastreamento')

    objects = ErrorManager()

    class Meta:
        verbose_name = 'Erro'
        verbose_name_plural = 'Erros'


class JobManager(models.Manager):
    def all(self):
        return self.order_by('-id').rows()
    
    def create(self, task, name=None, start=None):
        task_runner = super().create(name=name or uuid1().hex, task=task, start=start)
        return task_runner
    
    def execute(self, preview=False):
        qs = self.filter(finish__isnull=True, attempt__lte=3, canceled=False)
        qs = qs.filter(start__isnull=True) | qs.filter(start__lt=datetime.now())
        for obj in qs:
            try:
                obj.task.job = obj
                print(f'Executing job {obj.id}...')
                if not preview:
                    obj.start = datetime.now()
                    obj.attempt += 1
                    obj.task.run()
                    obj.finish = datetime.now()
                    print(f'Job {obj.id} completed with success.')
            except Exception as e:
                traceback.print_exc()
                obj.error = str(e)
                if obj.attempt < 3:
                    print(f'Job {obj.id} failed ({obj.error}) during attempt {obj.attempt}.')
                else:
                    obj.finish = datetime.now()
                    print(f'Job {obj.id} completed with error ({obj.error}).')
            finally:
                if not preview:
                    obj.save()


class Job(models.Model):
    name = models.CharField("Nome", max_length=255, db_index=True)
    user = models.ForeignKey(User, verbose_name='Usuário', null=True)
    start = models.DateTimeField("Início", null=True)
    finish = models.DateTimeField("Fim", null=True)
    canceled = models.BooleanField(verbose_name='Cancelada', default=False)
    attempt = models.IntegerField("Tentativa", default=0)
    
    task = models.TaskFied(verbose_name='Tarefa')
    total = models.IntegerField(verbose_name='Total', default=0)
    partial = models.IntegerField(verbose_name='Parcial', default=0)
    
    success = models.BooleanField(verbose_name='Successo', null=True)
    error = models.TextField(verbose_name='Erro', null=True)

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        
    objects = JobManager()

    def run(self):
        raise NotImplementedError()
    
    def __str__(self):
        return self.name
    
    def get_progress(self):
        key = f'task-{self.name}'
        return cache.get(key, {})


class PushNotificationQuerySet(models.QuerySet):
    def all(self):
        return self.fields('title', 'to', 'message', 'send_at', 'sent_at').search('title', 'message', 'to').filters('send_at__gte', 'send_at__lte', 'sent_at__gte', 'sent_at__lte').rows().order_by('-id')

    def create(self, to, title, message, send_at=None, action=None, url=None, key=None):
        if key:
            self.filter(key=key, sent_at__isnull=False).delete()
        notification = super().create(
            to=to, title=title, message=message, send_at=send_at, url=url, key=key
        )
        if send_at and send_at <= datetime.now():
            notification.send()
        return notification
    
    def send(self, preview=False):
        qs = self.filter(attempt__lte=3, sent_at__isnull=True)
        qs = qs.filter(send_at__isnull=True) | qs.filter(send_at__lte=datetime.now())
        for obj in qs:
            obj.send(preview=preview)


class PushNotification(models.Model):
    to = models.ForeignKey(User, verbose_name='To', on_delete=models.CASCADE)
    title = models.CharField("Subject")
    message = models.TextField("Content")
    url = models.CharField("URL", null=True)
    
    send_at = models.DateTimeField("Send at", null=True)
    sent_at = models.DateTimeField("Sent at", null=True)
    attempt = models.IntegerField("Attempt", default=0)

    error = models.TextField("Error", null=True)
    key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Push Notification'
        verbose_name_plural = 'Push Notifications'

    objects = PushNotificationQuerySet()

    def __str__(self):
        return f'Push Notification {self.title} to {self.to}'

    def send(self, preview=False):
        self.attempt = self.attempt + 1
        try:
            print(f'Sending notification "{self.title}" to "{self.to}"...')
            if not preview:
                send_push_web_notification(self.to, self.title, self.message, url=self.url)
                self.sent_at = datetime.now()
                print(f'Notification "{self.title}" to "{self.to}" sent with success.')
        except Exception as e:
            self.error = str(e)
            print(f'Notification "{self.title}" to "{self.to}" failed during attempt {self.attempt}.')
            traceback.print_exc()
        finally:
            if not preview:
                super().save()


class WhatsappNotificationQuerySet(models.QuerySet):
    def all(self):
        return self.fields('title', 'to', 'message', 'send_at', 'sent_at').search('title', 'message', 'to').filters('send_at__gte', 'send_at__lte', 'sent_at__gte', 'sent_at__lte').rows().order_by('-id')

    @meta('Enviadas')
    def sent(self):
        return self.filter(send_at__isnull=False)
    
    @meta('Não-Enviadas')
    def unsent(self):
        return self.filter(send_at__isnull=True)

    def create(self, to, title, message, send_at=None, url=None, key=None):
        if key:
            self.filter(key=key, sent_at__isnull=False).delete()
        notification = super().create(
            to=to, title=title, message=message, send_at=send_at, url=url, key=key
        )
        if send_at and send_at <= datetime.now():
            notification.send()
        return notification
    
    def send(self, preview=False):
        qs = self.filter(attempt__lte=3, sent_at__isnull=True)
        qs = qs.filter(send_at__isnull=True) | qs.filter(send_at__lte=datetime.now())
        for obj in qs:
            obj.send(preview=preview)


class WhatsappNotification(models.Model):
    to = models.CharField(verbose_name='To')
    title = models.CharField("Subject")
    message = models.TextField("Content")
    url = models.CharField("URL", null=True, blank=True)
    
    send_at = models.DateTimeField("Send at", null=True, blank=True)
    sent_at = models.DateTimeField("Sent at", null=True, blank=True)
    attempt = models.IntegerField("Attempt", default=0, blank=True)

    error = models.TextField("Error", null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Whatsapp Notification'
        verbose_name_plural = 'Whatsapp Notifications'

    objects = WhatsappNotificationQuerySet()

    def __str__(self):
        return f'Whatsapp Notification {self.title} to {self.to}'

    def send(self, preview=False):
        self.attempt = self.attempt + 1
        try:
            print(f'Sending notification "{self.title}" to "{self.to}"...')
            if not preview:
                send_whatsapp_notification(self.to, self.title, self.message, url=self.url)
                self.sent_at = datetime.now()
                print(f'Notification "{self.title}" to "{self.to}" sent with success.')
        except Exception as e:
            self.error = str(e)
            print(f'Notification "{self.title}" to "{self.to}" failed during attempt {self.attempt}.')
            traceback.print_exc()
        finally:
            if not preview:
                super().save()

    def serializer(self):
        return super().serializer().fieldset("Dados Gerais", ('subject', 'to', 'content', 'url', 'send_at'))


class EmailManager(models.Manager):
    def all(self):
        return self.fields('subject', 'to', 'content', 'send_at', 'sent_at').search('subject', 'content', 'to').filters('send_at__gte', 'send_at__lte', 'sent_at__gte', 'sent_at__lte').rows().order_by('-id')

    def create(self, to, subject, content, send_at=None, action=None, url=None, key=None):
        to = [to] if isinstance(to, str) else list(to)
        if key:
            self.filter(key=key, sent_at__isnull=False).delete()
        email = super().create(
            to=" ".join(to), subject=subject, content=content, send_at=send_at, action=action, url=url, key=key
        )
        if send_at and send_at <= datetime.now():
            email.send()
        return email
    
    def send(self, preview=False):
        qs = self.filter(attempt__lte=3, sent_at__isnull=True)
        qs = qs.filter(send_at__isnull=True) | qs.filter(send_at__lte=datetime.now())
        for obj in qs:
            obj.send(preview=preview)


class Email(models.Model):
    to = models.TextField("To", help_text="Separated by space")
    subject = models.CharField("Subject")
    content = models.TextField("Content")
    send_at = models.DateTimeField("Send at", null=True)
    sent_at = models.DateTimeField("Sent at", null=True)
    attempt = models.IntegerField("Attempt", default=0)

    action = models.CharField("Action", null=True)
    url = models.CharField("URL", null=True)

    error = models.TextField("Error", null=True)
    key = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    objects = EmailManager()

    class Meta:
        verbose_name = "E-mail"
        verbose_name_plural = "E-mails"

    def __str__(self):
        return self.subject

    def send(self, preview=False):
        application = ApplicationConfig.get_instance()
        to = [email.strip() for email in self.to.split()]
        msg = EmailMultiAlternatives(self.subject, strip_tags(self.content), settings.DEFAULT_FROM_EMAIL, to)
        html = render_to_string('email.html', dict(email=self, title=application.title))
        msg.attach_alternative(html, "text/html")
        self.attempt = self.attempt + 1
        try:
            print(f'Sending e-mail "{self.subject}" to "{self.to}"...')
            if not preview:
                msg.send(fail_silently=False)
                self.sent_at = datetime.now()
                print(f'E-mail "{self.subject}" to "{self.to}" sent with success.')
        except Exception as e:
            self.error = str(e)
            print(f'Email "{self.subject}" to "{self.to}" failed during attempt {self.attempt}.')
            traceback.print_exc()
        finally:
            if not preview:
                super().save()

    def formfactory(self):
        return super().formfactory().fieldset(
            'Dados Gerais', ('subject', 'to', 'content', 'send_at')
        ).fieldset(
            'Botão', ('action', 'url')
        )
    
    def serializer(self):
        return super().serializer().fieldset(
            'Dados Gerais', ('subject', 'to', 'get_content', ('send_at', 'sent_at'))
        ).fieldset(
            'Botão', ('action', 'url')
        )
    
    def get_content(self):
        return HtmlContent(self.content)


class Profile(models.Model):
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(verbose_name=_("Foto"), upload_to='profile', width=500, blank=True, null=True, extensions=['png', 'jpg', 'jpeg'])

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profile")


class Token(models.Model):
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = binascii.hexlify(os.urandom(20)).decode()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.key


class LogQuerySet(models.QuerySet):
    def all(self):
        return self.search('username').fields(('username', 'endpoint', 'datetime'), 'data').order_by('-id')


class Log(models.Model):
    username = models.CharField(max_length=50, db_index=True, null=True)
    endpoint = models.CharField(verbose_name='Nome do Endpoint', db_index=True, null=True)
    instance = models.CharField(verbose_name='Instância', max_length=50, db_index=True, null=True)
    action = models.CharField(verbose_name='Ação', db_index=True, null=True)
    datetime = models.DateTimeField(verbose_name='Data/Hora', null=True)
    url = models.CharField(verbose_name='URL', null=True)
    data = models.TextField(verbose_name='Dados')

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'

    objects = LogQuerySet()

    def __str__(self):
        return f'Log #{self.id}'


class DeletionQuerySet(models.QuerySet):
    def all(self):
        return self.fields(('username', 'datetime', 'instance'), 'backup').search('username', 'instance').filters('datetime', 'restored').actions('deletion.restore').order_by('-id')



class Deletion(models.Model):
    username = models.CharField(max_length=50, db_index=True, null=True)
    datetime = models.DateTimeField(verbose_name='Data/Hora', null=True)
    instance = models.CharField(verbose_name='Instância', max_length=50, db_index=True, null=True)
    restored = models.BooleanField(verbose_name='Restaurado', default=False)
    backup = models.TextField(verbose_name='Backup')

    class Meta:
        verbose_name = 'Exclusão'
        verbose_name_plural = 'Exclusões'

    objects = DeletionQuerySet()

    def __str__(self):
        return f'Exclusão #{self.id} - f{self.instance}'
    
    def restore(self):
        backup = json.loads(self.backup)
        data = {}
        objects = []
        for name in backup['order']:
            data[name] = []

        for obj in serializers.deserialize("python", backup['objects']):
            if backup['order']:
                if obj.object.__class__.__name__ in data:
                    data[obj.object.__class__.__name__].append(obj.object)
                    if obj.object.__class__ not in objects:
                        objects.append(obj.object.__class__)
            else:
                if not obj.object.__class__.__name__ in data:
                    data[obj.object.__class__.__name__] = []
                data[obj.object.__class__.__name__].append(obj.object)
                if obj.object.__class__ not in objects:
                    objects.append(obj.object.__class__)

        with transaction.atomic():
            for key in data:
                print((key, len(data[key])))
                for obj in data[key]:
                    obj.save()
            self.restored = True
            self.save()


class TimeZone(models.Model):
    name = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Fuso Horário'
        verbose_name_plural = 'Fusos Horários'

    def __str__(self):
        return self.name
    
    def localtime(self, value):
        return timezone.get_timezone(self.name).localize(value).astimezone(timezone.get_default_timezone()).replace(tzinfo=None) if value else None


class UserTimeZone(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Usuário', on_delete=models.CASCADE)
    timezone = models.ForeignKey(TimeZone, verbose_name='Fuso Horário', on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = 'Fuso Horário do Usuário'
        verbose_name_plural = 'Fusos Horários do Usuário'

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.key)


class SettingsQuerySet(models.QuerySet):
    def all(self):
        return self


class Settings(models.Model):
    key = models.CharField(verbose_name='Chave')
    value = models.CharField(verbose_name='Value')

    class Meta:
        icon = 'gears'
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

    objects = SettingsQuerySet()

    def __str__(self):
        return f'Configuração {self.id}'



# class Task(models.Model):
#     total = models.IntegerField(verbose_name='Total', default=0)
#     partial = models.IntegerField(verbose_name='Parcial', default=0)
#     progress = models.IntegerField(verbose_name='Progresso', default=0)
#     error = models.TextField(verbose_name='Erro', null=True)
#     file = models.CharField(verbose_name='Arquivo')
#     key = models.CharField(verbose_name='UUID')

