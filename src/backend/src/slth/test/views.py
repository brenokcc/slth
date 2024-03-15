from ..views import Endpoint, ChildEndpoint
from . import forms
from django.forms import modelform_factory
from django.contrib.auth.models import User, Group
from .models import Pessoa, Telefone
from ..forms import ModelForm
from ..serializer import Serializar, LinkField


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class Register(Endpoint):
    form_class = forms.RegisterForm


class AddUser(Endpoint):
    form_class = forms.UserForm

class EditUser(Endpoint):
    form_class = forms.UserForm
    fieldsets = {
        'Dados Gerais': ('username', ('first_name', 'last_name'), 'email'),
        'Grupos': ('groups',)
    }

    def __init__(self, request, pk):
        self.source = User.objects.get(pk=pk)
        super().__init__(request)

class ListUsers(Endpoint):

    def __init__(self, request):
        self.source = User.objects.all()
        super().__init__(request)


class ViewUser(Endpoint):
    def __init__(self, request, pk):
        self.source = User.objects.get(pk=pk)
        super().__init__(request)
    

class CadastrarPessoa(Endpoint):
    def __init__(self, request):
        self.source = Pessoa()
        self.fieldsets = {
            'Dados Gerais': ('nome',),
            'Telefone Pessoal': ('telefone_pessoal',),
            'Telefones Profissionais': ('telefones_profissionais',)
        }
        super().__init__(request)

class VisualizarPessoa(Endpoint):
    def __init__(self, request, pk):
        self.source = self.objects('test.cidade').get(pk=pk)
        super().__init__(request)

    def get(self):
        return Serializar(self.source).fields('id', 'nome').serialize()

    def check_permission(self):
        return True
    
class VisualizarPessoa2(VisualizarPessoa):
    def get(self):
        return Serializar(self.source).fieldset('Dados Gerais', ('id', 'nome')).serialize()
    

class VisualizarCidade(Endpoint):
    def __init__(self, request, pk):
        self.source = self.objects('test.cidade').get(pk=pk)
        super().__init__(request)

    def get(self):
        return (
            Serializar(self.source, self.request)
            .fieldset('Dados Gerais', ('id', 'nome'), LinkField('prefeito', VisualizarPessoa))
            .fieldset('Prefeito', ('id', 'nome'), relation='prefeito')
            .endpoint('Cidades Vizinhas', CidadesVizinhas)
            .serialize()
        )


class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('test.cidade').all()
