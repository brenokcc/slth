from . import ListEndpoint, DeleteEndpoint, Endpoint
from ..models import Role
from .. import forms
from ..components import Response


class Roles(ListEndpoint[Role]):
    def get(self):
        return super().get().actions('role.delete')
    

class Delete(DeleteEndpoint[Role]):
    class Meta:
        icon = 'x'
        verbose_name = 'Excluir Papel'

    def get(self):
        return (
            super().get()
        )


class Change(Endpoint):
    role = forms.ModelChoiceField(Role.objects, label="Papel", widget=forms.RadioSelect())

    def get(self):
        qs = Role.objects.filter(username=self.request.user.username)
        qs.update(active=False)
        qs.filter(pk=self.request.GET['role']).update(active=True)
        return Response(
            message="Papel alterado com sucesso.",
            redirect="/api/dashboard/",
            store=dict(application=None),
        )
    
    def check_permission(self):
        return self.request.user.is_authenticated
