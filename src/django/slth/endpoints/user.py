from .. import endpoints
from .. import forms
from ..models import User
from ..components import Response


class Users(endpoints.ListEndpoint[User]):
    pass


class Add(endpoints.AddEndpoint[User]):
    class Meta:
        icon = "user-plus"


class View(endpoints.ViewEndpoint[User]):
    pass


class Edit(endpoints.EditEndpoint[User]):
    class Meta:
        icon = "user-pen"


class Delete(endpoints.DeleteEndpoint[User]):
    class Meta:
        icon = "user-minus"


class ChangePassword(endpoints.ChildInstanceEndpoint):
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
    

class SendPushNotification(endpoints.ChildInstanceEndpoint):
    title = forms.CharField(label='Título')
    message = forms.CharField(label="Texto", widget=forms.Textarea())
    url = forms.CharField(label='URL', required=False)

    class Meta:
        icon = "mail-bulk"
        verbose_name = "Enviar Notificação"

    def get(self):
        return self.formfactory().fields("title", "message", "url")

    def post(self):
        self.instance.send_push_notification(
            self.cleaned_data["title"], self.cleaned_data["message"], url=self.cleaned_data["url"]
        )
        return Response(message="Notificação enviada com sucesso.")

