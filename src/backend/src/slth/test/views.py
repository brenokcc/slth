from ..views import Endpoint
from . import forms
from django.forms import modelform_factory
from django.contrib.auth.models import User, Group
from .models import Pessoa, Telefone
from ..forms import ModelForm


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
        self.source = User.objects.get(pk=pk)

    
