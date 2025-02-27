
from slth import ENDPOINTS
from .utils import build_url
from django.conf import settings
from django.apps import apps

APPLICATION_CLASS = None


class Style():
    def __init__(self, color="black", background="inherite", border="none"):
        self.update(color=color, background=background, border=border)

    def update(self, color=None, background=None, border=None):
        if color:
            self.color = color
        if background:
            self.background = background
        if border:
            self.border = border


class Theme():
    def __init__(self):
        self.primary:Style = Style("#1351b4")
        self.secondary:Style = Style("#071e41")
        self.auxiliary:Style = Style("#2670e8")
        self.highlight:Style = Style("#0c326f")

        self.info:Style = Style("#1351b4", "#d4e5ff")
        self.success:Style = Style("#1351b4")
        self.warning:Style = Style("#fff5c2")
        self.danger:Style = Style("#e52207")


class Groups(dict):
    def add(self, **kwargs):
        self.update(**kwargs)

class Menu(dict):
    def add(self, arg):
        self.update(arg)

    def process(self, request):
        items = []

        def get_item(k, v):
            print(k, v)
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
                    endpoint = cls().instantiate(request, None)
                    if endpoint.check_permission() and endpoint.contribute("menu"):
                        icon, label = k.split(":") if ":" in k else (None, k)
                        url = build_url(request, cls.get_api_url())
                        return dict(dict(label=label, url=url, icon=icon))

        for k, v in self.items():
            item = get_item(k, v)
            if item:
                items.append(item)
        
        return items

class Oauth(list):
    def add(self, name, client_id, client_secret, redirect_uri, authorize_url, access_token_url, user_data_url, user_logout_url, user_scope, user_create, user_username, user_email):
        super().append(dict(name=name, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, authorize_url=authorize_url, access_token_url=access_token_url, user_data_url=user_data_url, user_logout_url=user_logout_url, user_scope=user_scope, user_create=user_create, user_username=user_username, user_email=user_email))

    def serialize(self):
        data = []
        for provider in self:
            redirect_uri = "{}{}".format(settings.SITE_URL, provider['redirect_uri'])
            authorize_url = '{}?response_type=code&client_id={}&redirect_uri={}'.format(
                provider['authorize_url'], provider['client_id'], redirect_uri
            )
            if provider.get('scope'):
                authorize_url = '{}&scope={}'.format(authorize_url, provider.get('scope'))
            data.append(dict(label=f'Entrar com {provider["name"]}', url=authorize_url))
        return data

class List(list):

    def add(self, *names):
        super().extend(names)


class Dashboard():
    def __init__(self):
        self.actions:List = List()
        self.toolbar:List = List()
        self.top:List = List()
        self.center:List = List()
        self.boxes:List = List()
        self.search:List = List()
        self.usermenu:List = List()
        self.adder:List = List()
        self.tools:List = List()
        self.settings:List = List()
        self.index = "dashboard"


class ApplicationMetaclass(type):
    
    def __new__(mcs, name, bases, attrs):
        global APPLICATION_CLASS
        cls = super().__new__(mcs, name, bases, attrs)
        APPLICATION_CLASS = cls
        return cls


class Application(metaclass=ApplicationMetaclass):
    
    def __init__(self):
        self.lang = "pt-br"
        self.title = "Sloth"
        self.subtitle = "Take your time!"
        self.icon = "/static/images/logo.png"
        self.logo = "/static/images/logo.png"
        self.version =  "0.0.1"
        self.oauth:Oauth = Oauth()
        self.groups:Groups = Groups()
        self.menu:Menu = Menu()
        self.dashboard = Dashboard()
        self.theme:Theme = Theme()

    def load(self):
        pass

    def serialize(self, request):
        icon = build_url(request, self.icon)
        logo = build_url(request, self.logo)
        if request.user.is_authenticated:
            user = request.user.username.split()[0].split("@")[0]
            profile = apps.get_model("slth", "profile").objects.filter(user=request.user).first()
            photo = profile and profile.photo and build_url(request, profile.photo.url) or None
        else:
            user = profile = photo = None
        endpoints = {"actions": [], "usermenu": [], "adder": [], "settings": [], "tools": [], "toolbar": []}
        for entrypoint in endpoints:
            for endpoint_name in getattr(self.dashboard, entrypoint):
                cls = ENDPOINTS[endpoint_name]
                endpoint = cls().instantiate(request, None)
                if endpoint.check_permission() and endpoint.contribute(entrypoint):
                    name = endpoint.get_verbose_name()
                    url = build_url(request, cls.get_api_url())
                    modal = cls.get_metadata("modal", False)
                    icon = cls.get_metadata("icon", None)
                    endpoints[entrypoint].append(dict(name=name, url=url, modal=modal, icon=icon))
        return dict(
            type="application",
            icon=icon,
            navbar=dict(
                type="navbar", title=self.title, subtitle=self.subtitle, logo=logo, user=user, **endpoints
            ),
            menu=dict(
                type="menu", items=self.menu.process(request), user=user, image=photo
            ),
            footer=dict(
                type="footer", version=self.version
            ),
            oauth=self.oauth.serialize(),
            sponsors=[]
        )
    
    @staticmethod
    def get_instance():
        instance = APPLICATION_CLASS()
        instance.load()
        return instance

