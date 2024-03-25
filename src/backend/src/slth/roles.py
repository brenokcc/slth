from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Model, QuerySet
from django.db.models.fields import related_descriptors
from django.db.models.signals import m2m_changed, post_save, post_delete

ROLES = {}

def related_model(model, relation_name):
 attr = getattr(model, relation_name, None)
 if attr is None or relation_name.startswith('get_'):
  if relation_name.startswith('get_'):
      attr = getattr(model, relation_name)
  else:
      attr = getattr(model, f'get_{relation_name}')
  value = attr(model(id=0))
  if isinstance(value, QuerySet):
    return value.model
  elif isinstance(value,Model):
    return type(value)
 if isinstance(attr, related_descriptors.ForwardManyToOneDescriptor):
    return attr.field.related_model
 elif isinstance(attr, related_descriptors.ManyToManyDescriptor):
    return attr.field.related_model
 elif isinstance(attr, related_descriptors.ReverseManyToOneDescriptor):
    return attr.rel.related_model


def post_save_func(sender, **kwargs):
    from .models import Role
    pk = kwargs['instance'].pk
    model = '{}.{}'.format(sender._meta.app_label, sender._meta.model_name)
    existing = set(Role.objects.filter(model=model, value=pk).values_list('pk', flat=True))
    creating = set()
    for name, role in sender.__roles__.items():
        scopes = role.get('scopes')
        values = [role[k] for k in ('username', 'email', 'inactive', 'active') if k in role and role[k]]
        for item in sender.objects.filter(pk=pk).values(*values):
            username = item[role['username']]
            email = item[role['email']] if 'email' in role and role['email'] else ''
            active = item[role['active']] if 'active' in role and role['active'] else True
            inactive = item[role['inactive']] if 'inactive' in role and role['inactive'] else False
            if username is None or (inactive or not active):
                if scopes:
                    for scope in scopes.keys():
                        Role.objects.filter(username=username, name=name, scope=scope, model=model, value=pk).delete()
                else:
                    Role.objects.filter(username=username, name=name).delete()
            else:
                user = User.objects.filter(username=username).first()
                if user is None:
                    user = User.objects.create(username=username)
                    user.email = email
                    if hasattr(settings, 'DEFAULT_PASSWORD'):
                        user.set_password(settings.DEFAULT_PASSWORD(user))
                    else:
                        user.set_password('123')
                    user.save()
                else:
                    if email and not user.email:
                        user.email = email
                        user.save()
                if scopes:
                    for scope, lookup in scopes.items():
                        scope_model = sender if lookup in ('id', 'pk') else related_model(sender, lookup)
                        model = '{}.{}'.format(scope_model._meta.app_label, scope_model._meta.model_name)
                        for value in sender.objects.filter(pk=pk).values_list(lookup, flat=True):
                            creating.add(Role.objects.get_or_create(
                                username=username, name=name, model=model, scope=scope, value=value
                            )[0].id)
                else:
                    creating.add(Role.objects.get_or_create(
                        username=username, name=name, model=None, scope=None, value=None
                    )[0].id)
    Role.objects.filter(pk__in=existing-creating).delete()


def m2m_save_func(sender, **kwargs):
    if kwargs['action'].startswith('post_'):
        post_save_func(type(kwargs['instance']), instance=kwargs['instance'])


def post_delete_func(sender, **kwargs):
    from .models import Role
    pk = kwargs['instance'].pk
    model = '{}.{}'.format(sender._meta.app_label, sender._meta.model_name)
    Role.objects.filter(model=model, value=pk).delete()


def role(name, username, email=None, active=None, inactive=None, **scopes):
    def decorate(cls):
        if not hasattr(cls, '__roles__'):
            cls.__roles__ = {}
        metadata = dict(username=username, email=email, active=active, inactive=inactive, scopes=scopes)
        ROLES[name] = (cls, metadata)
        cls.__roles__[name] = metadata
        post_save.connect(post_save_func, cls)
        post_delete.connect(post_delete_func, cls)
        for field in cls._meta.many_to_many:
            m2m_changed.connect(m2m_save_func, sender=getattr(cls, field.name).through)

        return cls
    return decorate
