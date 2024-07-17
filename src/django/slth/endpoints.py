import io
import json
import types
import inspect
import requests
from weasyprint import HTML
from .models import Token, Role, Log, Deletion
from django.apps import apps
from typing import TypeVar, Generic
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .factory import FormFactory
from django.core.exceptions import ValidationError
from slth import forms
from django.db.models import Model
from datetime import datetime
from django.template.loader import render_to_string
from django.contrib.auth import authenticate
from .forms import ModelForm, Form
from .serializer import serialize, Serializer
from .components import (
    Application as Application_,
    Navbar,
    Menu,
    Footer,
    Response,
    Boxes,
    IconSet,
    TemplateContent,
)
from .exceptions import JsonResponseException, ReadyResponseException
from .utils import build_url, append_url
from .models import PushSubscription, Profile, User, Log
from slth.queryset import QuerySet
from slth import APPLICATON, ENDPOINTS
from . import oauth
from .tasks import Task, TaskRunner
from .threadlocal import tl


T = TypeVar("T")


class ApiResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "*"
        self["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH"
        self["Access-Control-Max-Age"] = "600"


class EnpointMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        bases_names = [cls.__name__ for cls in bases]
        if (
            name not in ("Endpoint", "ChildEndpoint")
            and "_ChildEndpoint" not in bases_names
        ):
            ENDPOINTS[cls.__name__.lower()] = cls
        if "AdminEndpoint" in bases_names[0:1]:
            model = cls.__orig_bases__[0].__args__[0]
            items = (
                ("Cadastrar", AddEndpoint[model], "plus", "add"),
                ("Editar", EditEndpoint[model], "pen", "edit"),
                ("Visualizar", ViewEndpoint[model], "eye", "view"),
                ("Excluir", DeleteEndpoint[model], "trash", "delete"),
            )
            for prefix, base, icon, action in items:
                endpoint = types.new_class(f"{prefix}{model.__name__}", (base,), {})
                endpoint.__admin__ = cls
                endpoint.__action__ = action
                endpoint.check_permission = lambda self: (
                    getattr(self.__admin__.instantiate(self.request, self), f'check_{self.__action__}_permission')()
                )
                endpoint.Meta = type(
                    "Meta",
                    (),
                    dict(
                        icon=icon,
                        modal=prefix != "Visualizar",
                        verbose_name=f"{prefix} {model._meta.verbose_name}",
                    ),
                )
            if "Meta" not in attrs:
                cls.Meta = type(
                    "Meta",
                    (),
                    dict(
                        icon=getattr(model._meta, "icon", None),
                        modal=False,
                        verbose_name=f"{model._meta.verbose_name_plural}",
                    ),
                )
        return cls


class Endpoint(metaclass=EnpointMetaclass):
    cache = cache

    def __init__(self):
        self.request = None
        self.source = None
        self.instantiator = None
        self.cleaned_data = {}
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
        fields = []
        for name in dir(self):
            if isinstance(getattr(self, name), forms.Field):
                fields.append(name)
        return self.formfactory().fields(*fields) if fields else {}

    def post(self):
        return Response(message="Ação realizada com sucesso")

    def check_permission(self):
        return self.request.user.is_superuser
    
    def contribute(self, entrypoint):
        return True

    def check_role(self, *names, superuser=True):
        if self.request.user.is_superuser and superuser:
            return True
        for name in names:
            if (
                self.objects("slth.role")
                .filter(username=self.request.user.username, name=name)
                .exists()
            ):
                return True
        return False

    def redirect(self, url):
        raise JsonResponseException(dict(type="redirect", url=url))
    
    def render(self, data, template=None, pdf=False, autoreload=None):
        base_url=settings.SITE_URL
        data.update(base_url=base_url)
        if template is None:
            template = '{}.html'.format(template or self.__class__.__name__.lower())
        if pdf:
            buffer = io.BytesIO()
            if isinstance(template, str):
                templates = template,
            else:
                templates = template
            pages = []
            for template in templates:
                html = render_to_string(template, data)
                if pdf:
                    doc = HTML(string=html).render()
                    pages.extend(doc.pages)
            new_doc = doc.copy(pages=pages)
            new_doc.write_pdf(buffer, base_url=base_url, stylesheets=[])
            buffer.seek(0)
            raise ReadyResponseException(HttpResponse(buffer, content_type='application/pdf'))
        return TemplateContent(template, data, autoreload=autoreload)

    def getform(self, form):
        return form

    def process(self):
        data = self.get()
        title = self.get_verbose_name()
        if isinstance(data, models.QuerySet):
            data = data.contextualize(self.request).settitle(title).apply_lookups(self.request.user)
        elif isinstance(data, Serializer):
            data = data.contextualize(self.request).settitle(title)
        elif isinstance(data, FormFactory):
            form = self.getform(data.settitle(title).form(self))
            if self.request.method == "POST" or self.request.GET.get("form") == title:
                try:
                    self.cleaned_data = form.submit()
                    if form._message or form._redirect or form._dispose:
                        return Response(form._message, form._redirect, dispose=form._dispose)
                    else:
                        return self.post()
                except ValidationError as e:
                    raise JsonResponseException(
                        dict(type="error", text="\n".join(e.messages), errors={})
                    )
            else:
                data = form
        elif isinstance(data, Form) or isinstance(data, ModelForm):
            data = data.settitle(title)
        elif self.request.method == "POST" and not data:
            return self.post()
        return data

    def serialize(self):
        output = self.process()
        if isinstance(output, Task):
            TaskRunner(output).start()
            output = Response(f'Tarefa {output.key} iniciada.', task=output.key)
        return serialize(output)

    def to_response(self):
        return ApiResponse(self.serialize(), safe=False)

    def formfactory(self, instance=None, method="POST") -> FormFactory:
        return FormFactory(instance, method=method)

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
            return f"/api/{cls.get_api_name()}/{arg}/"
        return f"/api/{cls.get_api_name()}/"

    @classmethod
    def get_pretty_name(cls):
        name = []
        for c in cls.__name__:
            if name and c.isupper():
                name.append(" ")
            name.append(c)
        return "".join(name)

    @classmethod
    def get_qualified_name(cls):
        return "{}.{}".format(cls.__module__, cls.__name__).lower()

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
        pattern = "{}/".format(cls.get_api_name())
        for arg in args:
            pattern = "{}{}/".format(pattern, "<str:{}>".format(arg))
        return pattern

    @classmethod
    def get_api_metadata(cls, request, base_url, pk=None):
        action_name = cls.get_metadata("verbose_name")
        icon = cls.get_metadata("icon")
        modal = cls.get_metadata("modal")
        if cls.is_child():
            url = append_url(base_url, f"action={cls.get_api_name()}")
            url = f"{url}&id={pk}" if pk else url
        else:
            url = build_url(request, f"/api/{cls.get_api_name()}/")
            url = f"{url}{pk}/" if pk else url
        return dict(
            type="action",
            title=action_name,
            name=action_name,
            url=url,
            key=cls.get_api_name(),
            icon=icon,
            modal=modal,
        )

    @classmethod
    def get_metadata(cls, key, default=None):
        value = None
        metaclass = getattr(cls, "Meta", None)
        if metaclass:
            value = getattr(metaclass, key, None)
        if value is None:
            if key == "verbose_name":
                value = cls.get_pretty_name()
            if key == "modal":
                value = (
                    issubclass(cls, EditEndpoint)
                    or issubclass(cls, DeleteEndpoint)
                    or issubclass(cls, Endpoint)
                    or issubclass(cls, ChildEndpoint)
                )
        return default if value is None else value

    def get_verbose_name(self):
        return self.get_metadata("verbose_name")
    
    def get_instance(self):
        return None
    
    def start_audit_trail(self):
        instance = self.get_instance()
        pk = instance.pk if isinstance(instance, Model) else None
        tl.context = dict(
            endpoint = self.get_api_name(), model=None, pk=pk,
            datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            user=self.request.user.username if self.request.user.is_authenticated else None,
            url=self.request.get_full_path(), logs=[]
        )

    def finish_audit_trail(self):
        if hasattr(tl, 'context') and tl.context['logs']:
            pk = tl.context['pk']
            instance = self.get_instance()
            print(tl.context)
            if pk or isinstance(instance, Model):
                model = '{}.{}'.format(instance._meta.app_label, instance._meta.model_name)
                tl.context.update(model=model, pk=pk or instance.pk)
            Log.objects.create(data=tl.context)

    def absolute_url(self, relative_url):
        return "{}://{}{}".format(self.request.META.get('X-Forwarded-Proto', self.request.scheme), self.request.get_host(), relative_url)


class PublicEndpoint(Endpoint):
    def check_permission(self):
        return True


class ReportEndpoint(Endpoint):

    def process(self):
        data = super().process()
        template = '{}.html'.format(self.__class__.__name__.lower())
        html = render_to_string(template, data)
        headers = {'Content-type': 'text/html'}
        response = requests.post('http://weasyprint.aplicativo.click/pdf', headers=headers, data=html)
        raise ReadyResponseException(HttpResponse(response.content, content_type='application/pdf'))


class ModelEndpoint(Endpoint):
    def __init__(self):
        self.model = self.__orig_bases__[0].__args__[0]
        if isinstance(self.model, str):
            self.model = self.objects(self.model).get(pk=self.pk)
        super().__init__()


class AdminEndpoint(Generic[T], ModelEndpoint):

    def get(self) -> QuerySet:
        actions = [
            f"{prefix}{self.model.__name__.lower()}"
            for prefix in ("cadastrar", "visualizar", "editar", "excluir")
        ]
        return self.model.objects.all().actions(*actions)
    
    def check_add_permission(self):
        return self.check_permission()
    
    def check_view_permission(self):
        return self.check_permission()
    
    def check_edit_permission(self):
        return self.check_permission()
    
    def check_delete_permission(self):
        return self.check_permission()


class ListEndpoint(Generic[T], ModelEndpoint):
    def get(self) -> QuerySet:
        return self.model.objects#.contextualize(self.request)


class AddEndpoint(Generic[T], ModelEndpoint):
    def __init__(self):
        super().__init__()
        self.instance = self.model()

    def get(self) -> FormFactory:
        return self.formfactory()

    def get_instance(self):
        return self.instance
    
    def formfactory(self):
        return self.instance.formfactory()


class ModelInstanceEndpoint(ModelEndpoint):
    def __init__(self, pk):
        super().__init__()
        self.instance = self.model.objects.get(pk=pk)

    def get_instance(self):
        return self.instance


class InstanceEndpoint(Generic[T], ModelInstanceEndpoint):

    def formfactory(self) -> FormFactory:
        return FormFactory(self.get_instance())

    def serializer(self) -> Serializer:
        return Serializer(self.get_instance()).contextualize(self.request)


class ViewEndpoint(Generic[T], ModelInstanceEndpoint):

    class Meta:
        icon = "eye"
        modal = False
        verbose_name = "Visualizar"

    def get(self) -> Serializer:
        return self.get_instance().serializer().contextualize(self.request)

    def get_verbose_name(self):
        return str(self.get_instance())


class EditEndpoint(Generic[T], ModelInstanceEndpoint):
    def get(self) -> FormFactory:
        return self.get_instance().formfactory()


class DeleteEndpoint(Generic[T], ModelInstanceEndpoint):
    def get(self) -> FormFactory:
        return self.formfactory(self.get_instance()).fields()

    def post(self):
        self.get_instance().safe_delete(self.request.user.username)
        return super().post()


class ChildEndpoint(Endpoint):

    @classmethod
    def is_child(cls):
        return True

    def check_permission(self):
        return True
    
class RelationEndpoint(Generic[T], ModelEndpoint):
    def __init__(self):
        super().__init__()
        self.instance = self.model()
        
    def get(self) -> FormFactory:
        return self.formfactory()

    def get_instance(self):
        return self.instance
    
    def formfactory(self):
        return super().formfactory(self.instance)
    
    @classmethod
    def is_child(cls):
        return True

    def check_permission(self):
        return True


class Add(ChildEndpoint):
    class Meta:
        icon = "plus"
        verbose_name = "Cadastrar"

    def get(self) -> FormFactory:
        return self.source.model().formfactory()


class ChildInstanceEndpoint(ChildEndpoint):
    def __init__(self, instance):
        self.instance = instance
        super().__init__()

    def get_instance(self):
        return self.instance

    def formfactory(self) -> FormFactory:
        return FormFactory(self.get_instance())

    def serializer(self) -> Serializer:
        return Serializer(self.get_instance()).contextualize(self.request)


class View(ChildInstanceEndpoint):
    class Meta:
        icon = "eye"
        modal = False
        verbose_name = "Visualizar"

    def get(self) -> Serializer:
        return self.get_instance().serializer()


class Edit(ChildInstanceEndpoint):
    class Meta:
        icon = "pen"
        verbose_name = "Editar"

    def get(self) -> FormFactory:
        return self.get_instance().formfactory()


class Delete(ChildInstanceEndpoint):
    class Meta:
        icon = "trash"
        verbose_name = "Excluir"

    def get(self):
        return self.formfactory().fields()

    def post(self):
        self.get_instance().delete()
        return super().post()


class Login(PublicEndpoint):
    username = forms.CharField(label="Username", mask=getattr(settings, 'USERNAME_MASK', None))
    password = forms.CharField(label="Senha")

    class Meta:
        modal = False
        icon = "sign-in"
        verbose_name = "Login"

    def get(self):
        code = self.request.GET.get("code")
        if code:
            user = oauth.authenticate(code)
            if user:
                token = Token.objects.create(user=user)
                return Response(
                    message="Bem-vindo!",
                    redirect="/api/dashboard/",
                    store=dict(token=token.key, application=None),
                )
        return self.formfactory().fields("username", "password")

    def post(self):
        user = authenticate(
            self.request,
            username=self.cleaned_data.get("username"),
            password=self.cleaned_data.get("password"),
        )
        if user:
            token = Token.objects.create(user=user)
            return Response(
                message="Bem-vindo!",
                redirect=self.request.GET.get("next", "/api/dashboard/"),
                store=dict(token=token.key, application=None),
            )
        else:
            raise ValidationError("Login e senha não conferem")


class Logout(Endpoint):
    class Meta:
        modal = False
        verbose_name = "Sair"

    def get(self):
        return Response(
            message="Logout realizado com sucesso.",
            redirect="/api/home/",
            store=dict(token=None, application=None),
        )

    def check_permission(self):
        return self.request.user.is_authenticated


class Icons(PublicEndpoint):
    class Meta:
        modal = True
        verbose_name = "Ícones"

    def get(self):
        return IconSet()

    def check_permission(self):
        return settings.DEBUG
    
    def contribute(self, entrypoint):
        return self.request.user.is_authenticated
    

class Roles(ListEndpoint[Role]):
    class Meta:
        modal = False
        verbose_name = 'Papéis dos Usuários'
    
    def get(self):
        return super().get().all()

class Logs(ListEndpoint[Log]):
    class Meta:
        modal = False
        verbose_name = 'Histórico de Alterações'
    
    def get(self):
        return super().get().all()
    

class Deletions(ListEndpoint[Deletion]):
    class Meta:
        modal = False
        verbose_name = 'Exclusões'
    
    def get(self):
        return super().get().all()


class RestoreDeletion(InstanceEndpoint[Deletion]):
    class Meta:
        verbose_name = 'Restaurar'

    def get(self):
        return (super().formfactory().fields())
    
    def post(self):
        self.instance.restore()
        return super().post()
    
    def check_permission(self):
        return super().check_permission() and not self.instance.restored



class Search(Endpoint):
    def get(self):
        key = "_options_"
        options = self.cache.get(key, [])
        term = self.request.GET.get("term")
        if options is None and APPLICATON["dashboard"]["search"]:
            options = []
            for endpoint in APPLICATON["dashboard"]["search"]:
                cls = ENDPOINTS[endpoint]
                url = build_url(self.request, cls.get_api_url())
                verbose_name = cls.get_metadata("verbose_name")
                options.append(dict(id=url, value=verbose_name))
            self.cache.set(key, options)
        if term:
            result = []
            for option in options:
                if slugify(term.lower()) in slugify(option["value"].lower()):
                    result.append(option)
        else:
            result = options
        return result[0:10]


class Users(ListEndpoint[User]):

    class Meta:
        modal = False
        verbose_name = "Usuários"

    def get(self):
        return (
            super()
            .get()
            .search("username", "email")
            .filters("is_superuser", "is_active")
            .fields("username", "email", "get_roles")
            .actions(
                "add",
                "viewuser",
                "edit",
                "delete",
                "sendpushnotification",
                "changepassword",
            )
        )

class ViewUser(ViewEndpoint[User]):
    class Meta:
        modal = False
        icon = 'eye'
        verbose_name = 'Visualizar '

    def get(self):
        return (
            super().get()
        )


class ChangePassword(ChildInstanceEndpoint):
    password = forms.CharField(label="Senha", required=False)

    class Meta:
        icon = "user-lock"
        verbose_name = "Alterar Senha"

    def get(self):
        return self.formfactory().fields("password")

    def post(self):
        self.instance.set_password(self.cleaned_data["password"])
        self.instance.save()
        return super().post()


class Home(PublicEndpoint):
    class Meta:
        verbose_name = ""

    def get(self):
        cls = ENDPOINTS[APPLICATON["index"]]
        self.redirect(cls.get_api_url())


class Dashboard(Endpoint):
    class Meta:
        verbose_name = ""

    def get(self):
        serializer = Serializer(request=self.request)
        if APPLICATON["dashboard"]["boxes"]:
            boxes = Boxes("Acesso Rápido")
            for endpoint in APPLICATON["dashboard"]["boxes"]:
                cls = ENDPOINTS[endpoint]
                if cls().contextualize(self.request).check_permission():
                    icon = cls.get_metadata("icon", "check")
                    label = cls.get_metadata("verbose_name")
                    url = build_url(self.request, cls.get_api_url())
                    boxes.append(icon, label, url)
            serializer.append("Acesso Rápido", boxes)
        if APPLICATON["dashboard"]["top"]:
            group = serializer.group("Top")
            for endpoint in APPLICATON["dashboard"]["top"]:
                cls = ENDPOINTS[endpoint]
                if cls.instantiate(
                    self.request, self.request.user
                ).check_permission():
                    group.endpoint(
                        cls.get_metadata("verbose_name"), cls, wrap=False
                    )
            group.parent()
        if APPLICATON["dashboard"]["center"]:
            for endpoint in APPLICATON["dashboard"]["center"]:
                cls = ENDPOINTS[endpoint]
                serializer.endpoint(
                    cls.get_metadata("verbose_name"), cls, wrap=False
                )
        return serializer

    def check_permission(self):
        return self.request.user.is_authenticated


class Application(PublicEndpoint):
    def get(self):
        user = None
        navbar = None
        menu = None
        icon = build_url(self.request, APPLICATON["logo"])
        logo = build_url(self.request, APPLICATON["logo"])
        if self.request.user.is_authenticated:
            user = self.request.user.username.split()[0].split("@")[0]
        navbar = Navbar(
            title=APPLICATON["title"],
            subtitle=APPLICATON["subtitle"],
            logo=logo,
            user=user,
            search=False,
            roles=' | '.join((str(role) for role in self.objects('slth.role').filter(username=self.request.user.username)))
        )
        for entrypoint in ["actions", "usermenu", "adder", "settings", "tools", "toolbar"]:
            if APPLICATON["dashboard"][entrypoint]:
                for endpoint_name in APPLICATON["dashboard"][entrypoint]:
                    cls = ENDPOINTS[endpoint_name]
                    endpoint = cls().instantiate(self.request, self)
                    if endpoint.check_permission() and endpoint.contribute(entrypoint):
                        label = cls.get_metadata("verbose_name")
                        url = build_url(self.request, cls.get_api_url())
                        modal = cls.get_metadata("modal", False)
                        icon = cls.get_metadata("icon", None)
                        navbar.add_action(entrypoint, label, url, modal, icon=icon)
        
        if APPLICATON["menu"]:
            items = []

            def get_item(k, v):
                if isinstance(v, dict):
                    icon, label = k.split(":") if ":" in k else (None, k)
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
                        endpoint = cls().instantiate(self.request, self)
                        if endpoint.check_permission() and endpoint.contribute("menu"):
                            icon, label = k.split(":") if ":" in k else (None, k)
                            url = build_url(self.request, cls.get_api_url())
                            return dict(dict(label=label, url=url, icon=icon))
                    else:
                        print(v)

            for k, v in APPLICATON["menu"].items():
                item = get_item(k, v)
                if item:
                    items.append(item)
            profile = (
                Profile.objects.filter(user=self.request.user).first() if user else None
            )
            photo_url = (
                profile.photo.url
                if profile and profile.photo
                else "/static/images/user.svg"
            )
            menu = Menu(items, user=user, image=build_url(self.request, photo_url))

        footer = Footer(APPLICATON["version"])
        return Application_(
            icon=icon, navbar=navbar, menu=menu, footer=footer, oauth=oauth.providers(),
            sponsors=APPLICATON.get("sponsors", ())
        )


class Manifest(PublicEndpoint):

    class Meta:
        verbose_name = "Manifest"

    def get(self):
        return dict(
            {
                "name": APPLICATON["title"],
                "short_name": APPLICATON["title"],
                "lang": "pt-BR",
                "start_url": build_url(self.request, "/app/home/"),
                "scope": build_url(self.request, "/app/"),
                "display": "standalone",
                "icons": [
                    {
                        "src": build_url(self.request, APPLICATON["icon"]),
                        "sizes": "192x192",
                        "type": "image/png",
                    }
                ],
            }
        )

    def check_permission(self):
        return True


class PushSubscribe(Endpoint):

    class Meta:
        verbose_name = "Subscrever para Notificações"

    def post(self):
        data = json.loads(self.request.POST.get("subscription"))
        device = self.request.META.get("HTTP_USER_AGENT", "")
        qs = PushSubscription.objects.filter(user=self.request.user, device=device)
        if qs.exists():
            qs.update(data=data)
        else:
            PushSubscription.objects.create(user=self.request.user, data=data, device=device)
        return Response()

    def check_permission(self):
        return True


class PushSubscriptions(ListEndpoint[PushSubscription]):
    class Meta:
        verbose_name = "Notificações"


class SendPushNotification(ChildInstanceEndpoint):
    title = forms.CharField(label='Título')
    message = forms.CharField(label="Texto", widget=forms.Textarea())
    url = forms.CharField(label='URL', required=False)

    class Meta:
        icon = "mail-bulk"
        verbose_name = "Enviar Notificação"

    def get(self):
        return self.formfactory().fields("title", "message", "url")

    def post(self):
        self.instance.send_push_notification(self.cleaned_data["title"], self.cleaned_data["message"], url=self.cleaned_data["url"])
        return Response(message="Notificação enviada com sucesso.")


class EditProfile(Endpoint):
    password = forms.CharField(label="Senha", required=False)
    password2 = forms.CharField(label="Confirmação", required=False)

    class Meta:
        verbose_name = "Editar Perfil"

    def __init__(self, *args, **kwargs):
        self.instance = None
        super().__init__(*args, **kwargs)

    def get(self):
        self.instance = Profile.objects.filter(
            user=self.request.user
        ).first() or Profile(user=self.request.user)
        return (
            self.formfactory(self.instance)
            .fieldset("Dados Gerais", ("photo",))
            .fieldset("Dados de Acesso", (("password", "password2"),))
        )

    def post(self):
        self.instance.save()
        if self.cleaned_data.get("password"):
            self.instance.user.set_password(self.cleaned_data.get("password"))
            self.instance.user.save()
        return Response(
            message="Ação realizada com sucesso.",
            redirect="/api/dashboard/",
            store=dict(application=None),
        )

    def check_permission(self):
        return self.request.user.is_authenticated


class About(PublicEndpoint):
    def get(self):
        return dict(version=APPLICATON["version"])
    
class TaskProgress(PublicEndpoint):

    def __init__(self, key):
        self.key = key
        super().__init__()

    def get(self):
        return cache.get(self.key)

