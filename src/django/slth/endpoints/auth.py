
from django.conf import settings
from django.core.exceptions import ValidationError
from slth import forms
from django.contrib.auth import authenticate
from ..models import Token, UserTimeZone, TimeZone
from ..components import Response
from .. import oauth
from . import PublicEndpoint, Endpoint, ChildInstanceEndpoint
from django.utils import timezone

def login_response(user, redirect='/api/dashboard/'):
    token = Token.objects.create(user=user)
    current_timezone = timezone.get_current_timezone()
    timezone_instance = TimeZone.objects.get_or_create(name=current_timezone.__str__())[0]
    user_timezone = UserTimeZone.objects.filter(user=user).first()
    if user_timezone is None:
        UserTimeZone.objects.create(user=user, timezone=timezone_instance)
    else:
        user_timezone.key = current_timezone.__str__()
        user_timezone.save()
    return Response(
        message="Bem-vindo!",
        redirect=redirect,
        store=dict(token=token.key, application=None),
    )


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
                return login_response(user)
        return self.formfactory().fields("username", "password")

    def post(self):
        user = authenticate(
            self.request,
            username=self.cleaned_data.get("username"),
            password=self.cleaned_data.get("password"),
        )
        if user:
            return login_response(user)
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


class LoginAs(ChildInstanceEndpoint):
    class Meta:
        icon = "user-secret"
        verbose_name = "Login As"

    def get(self):
        return self.formfactory().fields().info("Você acessará o sistema com o usuário {}.".format(self.source))
    
    def post(self):
        return login_response(self.source)
