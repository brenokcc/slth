import json
import types
import inspect
from .models import Token
from django.apps import apps
from typing import TypeVar, Generic
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .factory import FormFactory
from django.core.exceptions import ValidationError
from slth import forms
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
)
from .exceptions import JsonResponseException
from .utils import build_url, append_url
from .models import PushSubscription, Profile, User
from slth.queryset import QuerySet
from .notifications import send_push_web_notification
from slth import APPLICATON, ENDPOINTS
from . import oauth


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
                ("Cadastrar", AddEndpoint[model], "plus"),
                ("Editar", EditEndpoint[model], "pen"),
                ("Visualizar", ViewEndpoint[model], "eye"),
                ("Excluir", DeleteEndpoint[model], "trash"),
            )
            for prefix, base, icon in items:
                endpoint = types.new_class(f"{prefix}{model.__name__}", (base,), {})
                endpoint.check_permission = lambda self: (
                    cls().instantiate(self.request, self).check_permission()
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
        return {}

    def post(self):
        return Response(message="Ação realizada com sucesso")

    def check_permission(self):
        return self.request.user.is_superuser

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
        return serialize(self.process())

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
            pattern = "{}{}/".format(pattern, "<int:{}>".format(arg))
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
        actions = [
            f"{prefix}{self.model.__name__.lower()}"
            for prefix in ("cadastrar", "visualizar", "editar", "excluir")
        ]
        return self.model.objects.all().actions(*actions)


class ListEndpoint(Generic[T], ModelEndpoint):
    def get(self) -> QuerySet:
        return self.model.objects.contextualize(self.request)


class AddEndpoint(Generic[T], ModelEndpoint):
    def __init__(self):
        super().__init__()
        self.instance = self.model()

    def get(self) -> FormFactory:
        return self.model().formfactory()

    def get_instance(self):
        return self.instance


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
        self.get_instance().delete()
        return super().post()


class ChildEndpoint(Endpoint):

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
    username = forms.CharField(label="Username")
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
                redirect="/api/dashboard/",
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
        verbose_name = "Icons"

    def get(self):
        return IconSet()

    def check_permission(self):
        return settings.DEBUG


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
        if self.request.user.is_authenticated:
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
        else:
            self.redirect("/api/login/")

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
        )
        for entrypoint in ["actions", "usermenu", "adder", "settings", "tools", "toolbar"]:
            if APPLICATON["dashboard"][entrypoint]:
                for endpoint in APPLICATON["dashboard"][entrypoint]:
                    cls = ENDPOINTS[endpoint]
                    if cls().instantiate(self.request, self).check_permission():
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
                        if cls().instantiate(self.request, self).check_permission():
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
                        "src": build_url(self.request, APPLICATON["logo"]),
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
        return self.formfactory().fields("title", "message", "url").initial(
            title='Mais uma notificação', message='Corpo da notificação', url='http://localhost:8000/app/dashboard/'
        )

    def post(self):
        send_push_web_notification(self.instance, self.cleaned_data["title"], self.cleaned_data["message"], url=self.cleaned_data["url"])
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
