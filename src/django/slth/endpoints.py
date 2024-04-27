
import json
import types
import inspect
from django.apps import apps
from typing import TypeVar, Generic
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .factory import FormFactory
from .forms import LoginForm, ModelForm, Form, SendPushNotificationForm, EditProfileForm
from .serializer import serialize, Serializer
from .components import Application as Application_, Navbar, Menu, Footer, Response, Boxes, IconSet
from .exceptions import JsonResponseException
from .utils import build_url, append_url
from .models import PushSubscription, Profile
from slth.queryset import QuerySet
from slth import APPLICATON, ENDPOINTS
from django.contrib.auth.models import User


import slth


T = TypeVar("T")

class ApiResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "*"
        self["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH";
        self["Access-Control-Max-Age"] = "600"


class EnpointMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        bases_names = [cls.__name__ for cls in bases]
        if name not in ('Endpoint', 'ChildEndpoint') and '_ChildEndpoint' not in bases_names:
            ENDPOINTS[cls.__name__.lower()] = cls
        if 'AdminEndpoint' in bases_names[0:1]:
            model = cls.__orig_bases__[0].__args__[0]
            items = (
                ('Cadastrar', AddEndpoint[model], 'plus'),
                ('Editar', EditEndpoint[model], 'pen'),
                ('Visualizar', ViewEndpoint[model], 'eye'),
                ('Excluir', DeleteEndpoint[model], 'trash')
            )
            for prefix, base, icon in items:
                endpoint = types.new_class(f'{prefix}{model.__name__}', (base,), {})
                endpoint.check_permission = lambda self: (
                    cls().instantiate(self.request, self).check_permission()
                )
                endpoint.Meta = type(
                    'Meta', (), dict(
                        icon=icon, modal=prefix != 'Visualizar',
                        verbose_name=f'{prefix} {model._meta.verbose_name}'
                    )
                )
            if 'Meta' not in attrs:
                cls.Meta = type(
                    'Meta', (), dict(
                        icon=getattr(model._meta, 'icon', None), modal=False,
                        verbose_name=f'{model._meta.verbose_name_plural}'
                    )
                )
        return cls


class Endpoint(metaclass=EnpointMetaclass):
    cache = cache

    def __init__(self):
        self.request = None
        self.source = None
        self.instantiator = None
        super().__init__()

    def configure(self, source, instantiator=None):
        self.source = source
        self.instantiator = instantiator
        return self

    def contextualize(self, request):
        self.request = request
        return self

    def objects(self, model):
        return apps.get_model(model).objects
        
    def get(self):
        return {}
    
    def post(self):
        data = self.get()
        if isinstance(data, FormFactory):
            data = data.form(self.request).post()
        if isinstance(data, Form) or isinstance(data, ModelForm):
            data = data.post()
        return data
    
    def save(self, data):
        pass
    
    def check_permission(self):
        return self.request.user.is_superuser
    
    def check_role(self, *names, superuser=True):
        if self.request.user.is_superuser and superuser:
            return True
        for name in names:
            if self.objects('slth.role').filter(username=self.request.user.username, name=name).exists():
                return True
        return False
    
    def redirect(self, url):
        raise JsonResponseException(dict(type='redirect', url=url))
    
    def getdata(self):
        if self.request.method == 'GET':
            data = self.get()
        elif self.request.method == 'POST':
            data = self.post()
        else:
            data = {}
        title = self.get_metadata('verbose_name')
        if isinstance(data, models.QuerySet):
            data = data.contextualize(self.request).settitle(title)
        elif isinstance(data, Serializer):
            data = data.contextualize(self.request).settitle(title)
        elif isinstance(data, FormFactory):
            data = data.settitle(title).form(self.request)
        elif isinstance(data, Form) or isinstance(data, ModelForm):
            data = data.settitle(title)
        return {} if data is None else data
    
    def serialize(self):
        return serialize(self.getdata())
    
    def to_response(self):
        return ApiResponse(self.serialize(), safe=False)
    
    def formfactory(self, instance, delete=False) -> FormFactory:
        return FormFactory(instance, delete=delete)
    
    def serializer(self, instance=None) -> Serializer:
        return Serializer(instance or self).contextualize(self.request)
    
    @classmethod
    def is_child(cls):
        return False
    
    @classmethod
    def get_api_name(cls):
        return cls.__name__.lower()
    
    @classmethod
    def get_api_url(cls, arg=None):
        if arg:
            return f'/api/{cls.get_api_name()}/{arg}/'  
        return f'/api/{cls.get_api_name()}/'    
    
    @classmethod
    def get_pretty_name(cls):
        name = []
        for c in cls.__name__:
            if name and c.isupper():
                name.append(' ')
            name.append(c)
        return ''.join(name)
    
    @classmethod
    def get_qualified_name(cls):
        return '{}.{}'.format(cls.__module__, cls.__name__).lower()
    
    @classmethod
    def instantiate(cls, request, source):
        args = ()
        if cls.is_child():
            args = (source,) if cls.has_args() else ()
        else:
            args = (source.pk,) if cls.has_args() else ()
        return cls(*args).configure(source).contextualize(request)
    
    @classmethod
    def has_args(cls):
        return len(inspect.getfullargspec(cls.__init__).args) > 1
    
    @classmethod
    def get_api_url_pattern(cls):
        args = inspect.getfullargspec(cls.__init__).args[1:]
        pattern = '{}/'.format(cls.get_api_name())
        for arg in args:
            pattern = '{}{}/'.format(pattern, '<int:{}>'.format(arg))
        return pattern
    
    @classmethod
    def get_api_metadata(cls, request, base_url, pk=None):
        action_name = cls.get_metadata('verbose_name')
        icon = cls.get_metadata('icon')
        modal = cls.get_metadata('modal')
        if cls.is_child():
            url = append_url(base_url, f'action={cls.get_api_name()}')
            url = f'{url}&id={pk}' if pk else url
        else:
            url = build_url(request, f'/api/{cls.get_api_name()}/')
            url = f'{url}{pk}/' if pk else url
        return dict(type='action', title=action_name, name=action_name, url=url, key=cls.get_api_name(), icon=icon, modal=modal)
    
    @classmethod
    def get_metadata(cls, key, default=None):
        value = None
        metaclass = getattr(cls, 'Meta', None)
        if metaclass:
            value = getattr(metaclass, key, None)
        if value is None:
            if key == 'verbose_name':
                value = cls.get_pretty_name()
            if key == 'modal':
                value = issubclass(cls, EditEndpoint) or issubclass(cls, DeleteEndpoint) or issubclass(cls, Endpoint) or issubclass(cls, ChildEndpoint)
        return default if value is None else value

class PublicEndpoint(Endpoint):
    def check_permission(self):
        return True

class ModelEndpoint(Endpoint):
    def __init__(self):
        self.model = self.__orig_bases__[0].__args__[0]
        if isinstance(self.model, str):
            self.model = self.objects(self.model).get(pk=self.pk)
        super().__init__()

class AdminEndpoint(Generic[T], ModelEndpoint):

    def get(self) -> QuerySet:
        actions = [f'{prefix}{self.model.__name__.lower()}' for prefix in ('cadastrar', 'visualizar', 'editar', 'excluir')]
        return self.model.objects.all().actions(*actions)
    
class ListEndpoint(Generic[T], ModelEndpoint):
    def get(self) -> QuerySet:
        return self.model.objects

class AddEndpoint(Generic[T], ModelEndpoint):
    def get(self) -> FormFactory:
        return self.model().formfactory()

class ModelInstanceEndpoint(ModelEndpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get_instance(self):
        return self.model.objects.get(pk=self.pk)

class InstanceEndpoint(Generic[T], ModelInstanceEndpoint):

    def formfactory(self, delete=False) -> FormFactory:
        return FormFactory(self.get_instance(), delete=delete)

    def serializer(self) -> Serializer:
        return Serializer(self.get_instance()).contextualize(self.request)
    

class ViewEndpoint(Generic[T], ModelInstanceEndpoint):

    class Meta:
        icon = 'eye'
        modal = False
        verbose_name = 'Visualizar'

    def get(self) -> Serializer:
        return self.get_instance().serializer().contextualize(self.request)
        
class EditEndpoint(Generic[T], ModelInstanceEndpoint):
    def get(self) -> FormFactory:
        return self.get_instance().formfactory()
    
class DeleteEndpoint(Generic[T], ModelInstanceEndpoint):
    def get(self) -> FormFactory:
        return self.formfactory(self.get_instance(), delete=True)
    

class FormEndpoint(Generic[T], Endpoint):

    def get_form_cls(self):
        return self.__orig_bases__[0].__args__[0]

    def get(self):
        return self.get_form_cls()(request=self.request)
    
class InstanceFormEndpoint(Generic[T], Endpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get_form_cls(self):
        return self.__orig_bases__[0].__args__[0]

    def get_instance(self):
        return self.get_form_cls().Meta.model.objects.get(pk=self.pk)

    def get(self):
        return self.get_form_cls()(self.get_instance(), request=self.request)
    
class ChildEndpoint(Endpoint):

    @classmethod
    def is_child(cls):
        return True
    
    def check_permission(self):
        return True

class Add(ChildEndpoint):
    class Meta:
        icon = 'plus'
        verbose_name = 'Cadastrar'

    def get(self) -> FormFactory:
        return self.source.model().formfactory()
    
class ChildInstanceEndpoint(ChildEndpoint):
    def __init__(self, instance):
        self.instance = instance
        super().__init__()

    def get_instance(self):
        return self.instance
    
    def formfactory(self, delete=False) -> FormFactory:
        return FormFactory(self.get_instance(), delete=delete)
    
    def serializer(self) -> Serializer:
        return Serializer(self.get_instance()).contextualize(self.request)
    
class ChildFormEndpoint(Generic[T], Endpoint):

    def get_form_cls(self):
        return self.__orig_bases__[0].__args__[0]

    def get(self):
        return self.get_form_cls()(request=self.request, endpoint=self)
    

class ChildInstanceFormEndpoint(Generic[T], ChildEndpoint):

    def __init__(self, source):
        self.source = source
        super().__init__()

    def get_form_cls(self):
        return self.__orig_bases__[0].__args__[0]
    
    def get_instance(self):
        return self.source

    def get(self):
        return self.get_form_cls()(instance=self.get_instance(), request=self.request, endpoint=self)

class View(ChildInstanceEndpoint):
    class Meta:
        icon = 'eye'
        modal = False
        verbose_name = 'Visualizar'
    
    def get(self) -> Serializer:
        return self.get_instance().serializer()

class Edit(ChildInstanceEndpoint):
    class Meta:
        icon = 'pen'
        verbose_name = 'Editar'
    def get(self) -> FormFactory:
        return self.get_instance().formfactory()
   
class Delete(ChildInstanceEndpoint):
    class Meta:
        icon = 'trash'
        verbose_name = 'Excluir'
    def get(self):
        return self.formfactory(delete=True)

class Login(Endpoint):
    def get(self):
        return LoginForm(request=self.request)

class Logout(PublicEndpoint):
    class Meta:
        modal = False
        verbose_name = 'Sair'
        
    def get(self):
        return Response(message='Logout realizado com sucesso.', redirect='/api/login/', store=dict(token=None, application=None))

class Icons(PublicEndpoint):
    class Meta:
        modal = True
        verbose_name = 'Icons'

    def get(self):
        return IconSet()


class Search(Endpoint):
    def get(self):
        key = '_options_'
        options = self.cache.get(key)
        term = self.request.GET.get('term')
        if options is None and APPLICATON['dashboard']['search']:
            options = []
            for endpoint in APPLICATON['dashboard']['search']:
                cls = ENDPOINTS[endpoint]
                url = build_url(self.request, cls.get_api_url())
                verbose_name = cls.get_metadata('verbose_name')
                options.append(dict(id=url, value=verbose_name))
            self.cache.set(key, options)
        if term:
            result = []
            for option in options:
                if slugify(term.lower()) in slugify(option['value'].lower()):
                    result.append(option)
        else:
            result = options
        return result[0:10]
    
class Users(ListEndpoint[User]):

    class Meta:
        modal = False
        verbose_name = 'Usuários'

    def get(self):
        return super().get().fields('username', 'email', 'is_superuser').actions('sendpushnotification')

class Dashboard(Endpoint):
    class Meta:
        verbose_name = ''
        
    def get(self):
        if self.request.user.is_authenticated:
            serializer = Serializer(request=self.request)
            if APPLICATON['dashboard']['boxes']:
                boxes = Boxes('Acesso Rápido')
                for endpoint in APPLICATON['dashboard']['boxes']:
                    cls = ENDPOINTS[endpoint]
                    if cls().contextualize(self.request).check_permission():
                        icon = cls.get_metadata('icon', 'check')
                        label = cls.get_metadata('verbose_name')
                        url = build_url(self.request, cls.get_api_url())
                        boxes.append(icon, label, url)
                serializer.append('Acesso Rápido', boxes)
            if APPLICATON['dashboard']['top']:
                group = serializer.group('Top')
                for endpoint in APPLICATON['dashboard']['top']:
                    cls = ENDPOINTS[endpoint]
                    if cls.instantiate(self.request, self.request.user).check_permission():
                        group.endpoint(cls.get_metadata('verbose_name'), cls, wrap=False)
                group.parent()
            if APPLICATON['dashboard']['center']:
                for endpoint in APPLICATON['dashboard']['center']:
                    cls = ENDPOINTS[endpoint]
                    serializer.endpoint(cls.get_metadata('verbose_name'), cls, wrap=False)
            return serializer
        else:
            self.redirect('/api/login/')

    def check_permission(self):
        return self.request.user.is_authenticated
    
class Application(PublicEndpoint):
    def get(self):
        navbar = None
        menu = None
        icon = build_url(self.request, APPLICATON['logo'])
        if self.request.user.is_authenticated:
            logo = build_url(self.request, APPLICATON['logo'])
            navbar = Navbar(
                title=APPLICATON['title'], subtitle=APPLICATON['subtitle'],
                logo=logo, user=self.request.user.username.split()[0].split('@')[0]
            )
            for entrypoint in ['usermenu', 'adder', 'settings', 'tools']:
                if APPLICATON['dashboard'][entrypoint]:
                    for endpoint in APPLICATON['dashboard'][entrypoint]:
                        cls = ENDPOINTS[endpoint]
                        if cls().instantiate(self.request, self).check_permission():
                            label = cls.get_metadata('verbose_name')
                            url = build_url(self.request, cls.get_api_url())
                            modal = cls.get_metadata('modal', False)
                            navbar.add_action(entrypoint, label, url, modal)
            items = []
            def get_item(k, v):
                if isinstance(v, dict):
                    icon, label = k.split(':') if ':' in k else (None, k)
                    subitems = []
                    for k1, v1 in v.items():
                        subitem = get_item(k1, v1)
                        if subitem:
                            subitems.append(subitem)
                    if subitems:
                        return dict(dict(icon=icon, label=label, items=subitems))
                else:
                    cls = ENDPOINTS.get(v)
                    if cls:
                        if cls().instantiate(self.request, self).check_permission():
                            icon, label = k.split(':') if ':' in k else (None, k)
                            url = build_url(self.request, cls.get_api_url())
                            return dict(dict(label=label, url=url, icon=icon))
                    else:
                        print(v)
            for k, v in APPLICATON['menu'].items():
                item = get_item(k, v)
                if item:
                    items.append(item)
            profile = Profile.objects.filter(user=self.request.user).first()
            photo_url = profile.photo.url if profile and profile.photo else '/static/images/user.png'
            menu = Menu(items, user=self.request.user.username, image=build_url(self.request, photo_url))
        footer = Footer(APPLICATON['version'])
        return Application_(icon=icon, navbar=navbar, menu=menu, footer=footer)
    
class Manifest(PublicEndpoint):

    class Meta:
        verbose_name = 'Manifest'

    def get(self):
        return dict(
            {
                "name": APPLICATON['title'],
                "short_name": APPLICATON['title'],
                "lang": 'pt-BR',
                "start_url": build_url(self.request, "/app/dashboard/"),
                "scope": build_url(self.request, "/app/"),
                "display": "standalone",
                "icons": [{
                    "src": build_url(self.request, APPLICATON['logo']),
                    "sizes": "192x192",
                    "type": "image/png"
                }]
            }
        )

    def check_permission(self):
        return True


class PushSubscribe(Endpoint):

    class Meta:
        verbose_name = 'Subscrever para Notificações'

    def post(self):
        data = json.loads(self.request.POST.get('subscription'))
        device = self.request.META.get('HTTP_USER_AGENT', '')
        qs = PushSubscription.objects.filter(user=User.objects.first(), device=device)
        qs.update(data=data) if qs.exists() else PushSubscription.objects.create(
            user=User.objects.first(), data=data, device=device
        )
        return Response()

    def check_permission(self):
        return True
    
class PushSubscriptions(ListEndpoint[PushSubscription]):
    class Meta:
        verbose_name = 'Notificações'

class SendPushNotification(ChildInstanceFormEndpoint[SendPushNotificationForm]):
    class Meta:
        icon = 'mail-bulk'
        verbose_name = 'Enviar Notificação'

class EditProfile(Endpoint):
    class Meta:
        verbose_name = 'Editar Perfil'

    def get(self):
        profile = Profile.objects.filter(user=self.request.user).first() or Profile(user=self.request.user)
        return EditProfileForm(instance=profile, request=self.request)

    def check_permission(self):
        return self.request.user.is_authenticated


