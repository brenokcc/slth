import os
import json
import binascii
from .db import models, meta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction
from django.apps import apps
from datetime import datetime
from django.utils.html import strip_tags
from django.core import serializers
from django.core.mail import EmailMultiAlternatives
from .notifications import send_push_web_notification
from slth import APPLICATON


class RoleFilter(models.Filter):
    def __init__(self, username_field):
        self.username_field = username_field

    def get_label(self):
        return 'Papel'

    def choices(self, queryset, term=None):
        return [(k, v) for k, v in APPLICATON['groups'].items()]
     
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
        return APPLICATON['groups'].get(self.name, self.name)

    def get_scope_value(self):
        return apps.get_model(self.model).objects.filter(pk=self.value).first() if self.model else None

    @meta('Descrição')
    def get_description(self):
        scope_value = self.get_scope_value()
        return '{} - {}'.format(self.get_verbose_name(), scope_value) if scope_value else self.get_verbose_name()


class EmailManager(models.Manager):
    def all(self):
        return self.order_by('-id')

    def send(self, to, subject, content, from_email=None):
        to = [to] if isinstance(to, str) else list(to)
        return self.create(from_email=from_email or 'no-replay@mail.com', to=', '.join(to), subject=subject, content=content)


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


class Error(models.Model):
    user = models.OneToOneField('auth.user', verbose_name='Usuário', on_delete=models.CASCADE, null=True)
    date = models.DateTimeField('Data/Hora')
    traceback = models.TextField('Rastreamento')

    class Meta:
        verbose_name = 'Erro'
        verbose_name_plural = 'Erros'


class Email(models.Model):
    from_email = models.EmailField('Remetente')
    to = models.TextField('Destinatário', help_text='Separar endereços de e-mail por ",".')
    subject = models.CharField('Assunto')
    content = models.TextField('Conteúdo', formatted=True)
    sent_at = models.DateTimeField('Data/Hora', null=True)

    objects = EmailManager()

    class Meta:
        verbose_name = 'E-mail'
        verbose_name_plural = 'E-mails'

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        to = [email.strip() for email in self.to.split(',')]
        msg = EmailMultiAlternatives(self.subject, strip_tags(self.content), self.from_email, to)
        msg.attach_alternative(self.content, "text/html")
        if self.sent_at is None:
            msg.send(fail_silently=True)
            self.sent_at = datetime.now()
        super().save(*args, **kwargs)


class Profile(models.Model):
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(verbose_name=_("Foto"), width=500, blank=True, null=True, extensions=['png', 'jpg', 'jpeg'])

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
    
class User(User):
    class Meta:
        icon = 'users'
        proxy = True
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

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
            .fieldset('Dados de Acesso', ('username', ('is_superuser', 'is_active'),))
            .queryset('Notificação', 'get_push_subscriptions')
            .queryset('Papéis', 'get_roles')
        )
    
    @meta('Inscrições de Notificação')
    def get_push_subscriptions(self):
        return self.pushsubscription_set.fields('device')
    
    def send_push_notification(self, title, message, url=None):
        send_push_web_notification(self, title, message, url=url)
    
    @meta('Papéis')
    def get_roles(self):
        return Role.objects.filter(username=self.username).fields('get_description').actions('delete')


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
        return self.fields(('username', 'datetime', 'instance'), 'backup').search('username', 'instance').filters('datetime', 'restored').actions('restoredeletion').order_by('-id')



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



# class Task(models.Model):
#     total = models.IntegerField(verbose_name='Total', default=0)
#     partial = models.IntegerField(verbose_name='Parcial', default=0)
#     progress = models.IntegerField(verbose_name='Progresso', default=0)
#     error = models.TextField(verbose_name='Erro', null=True)
#     file = models.CharField(verbose_name='Arquivo')
#     key = models.CharField(verbose_name='UUID')

