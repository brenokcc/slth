
from slth import ENDPOINTS
from .utils import build_url
from django.conf import settings
from django.apps import apps

APPLICATION_CLASS = None


class Style():
    def __init__(self, name, color="black", background="inherite", border="none"):
        self.name = name
        self.update(color=color, background=background, border=border)

    def update(self, color=None, background=None, border=None):
        if color:
            self.color = color
        if background:
            self.background = background
        if border:
            self.border = border

    def to_css(self):
        return f"""
            --{self.name}-color: { self.color };
            --{self.name}-border: { self.border };
            --{self.name}-background: { self.background };
        """

class ColorSchema:
    def to_css(self):
        css = []
        css.append("<style>")
        css.append(":root{")
        css.append(f"--border-radius: {self.border_radius}px;")
        css.append(self.default.to_css())
        css.append(self.header.to_css())
        css.append(self.footer.to_css())
        css.append(self.fieldset.to_css())
        css.append(self.input.to_css())
        css.append(self.primary.to_css())
        css.append(self.secondary.to_css())
        css.append(self.auxiliary.to_css())
        css.append(self.highlight.to_css())
        css.append(self.info.to_css())
        css.append(self.success.to_css())
        css.append(self.warning.to_css())
        css.append(self.danger.to_css())
        css.append("</style>")
        return "\n".join(css)


class Light(ColorSchema):
    def __init__(self):
        self.border_radius = 0
        self.default: Style = Style("default", color="#383838", background="#FFFFFF")
        self.header: Style = Style("header", color="#383838", background="#FFFFFF")
        self.footer: Style = Style("footer", color="#383838", background="#FFFFFF")
        self.fieldset: Style = Style("fieldset", color="#383838", background="#FFFFFF")
        self.input: Style = Style("input", border="solid 1px #d9d9d9", background="#FFFFFF")
        self.primary:Style = Style("primary", color="#1351b4", background="#1351b4")
        self.secondary:Style = Style("secondary", color="#071e41")
        self.auxiliary:Style = Style("auxiliary", color="#2670e8", background="#f8f8f8")
        self.highlight:Style = Style("hightlight", color="#0c326f")
        self.info:Style = Style("info", color="#1351b4", background="#d4e5ff")
        self.success:Style = Style("success", color="#ffffff", background="#1351b4")
        self.warning:Style = Style("warning", color="#fff5c2")
        self.danger:Style = Style("danger", color="#e52207")


class Dark(ColorSchema):
    def __init__(self):
        self.border_radius = 3
        self.default: Style = Style("default", color="#c3d0e5", background="#0D1117")
        self.header: Style = Style("header", color="#383838", background="#FFFFFF")
        self.footer: Style = Style("footer", color="#383838", background="#FFFFFF")
        self.fieldset: Style = Style("fieldset", color="#91aad2", background="#262c35")
        self.input: Style = Style("input", border="0", background="#0D1117")
        self.primary:Style = Style("primary", color="#c3d0e5", background="#90C4F9")
        self.secondary:Style = Style("secondary", color="#071e41")
        self.auxiliary:Style = Style("auxiliary", color="#91aad2", background="#262c35")
        self.highlight:Style = Style("hightlight", color="#0c326f")
        self.info:Style = Style("info", color="#c3d0e5", background="#262c35")
        self.success:Style = Style("success", color="#c3d0e5", background="#121f1a", border="1px solid #3b622b")
        self.warning:Style = Style("warning", color="#fff5c2")
        self.danger:Style = Style("danger", color="#e52207")


class Groups(dict):
    def add(self, **kwargs):
        self.update(**kwargs)

class Menu(dict):
    def add(self, arg):
        self.update(arg)

    def process(self, request):
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
    def add(self, name, client_id, client_secret, redirect_uri, authorize_url, access_token_url, user_data_url, user_username, user_email=None, user_scope=None, user_create=False, user_logout_url=None):
        super().append(dict(name=name, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, authorize_url=authorize_url, access_token_url=access_token_url, user_data_url=user_data_url, user_username=user_username, user_email=user_email, user_scope=user_scope, user_create=user_create, user_logout_url=user_logout_url))

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
        self.todo:List = List()
        self.top:List = List()
        self.center:List = List()
        self.boxes:List = List()
        self.search:List = List()
        self.usermenu:List = List()
        self.adder:List = List()
        self.tools:List = List()
        self.settings:List = List()
        self.index = "dashboard"


class Theme:
    def __init__(self):
        self.light = Light()
        self.dark = Dark()


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
        self.brand = None
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
        logo = build_url(request, self.brand or self.logo)
        title = self.title if self.brand is None else None
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
                type="navbar", title=title, subtitle=self.subtitle, logo=logo, user=user, **endpoints
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

