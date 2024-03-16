from slth.endpoints import Endpoint, ChildEndpoint, FormFactory
from .forms import RegisterForm, UserForm
from django.contrib.auth.models import User, Group
from .models import Pessoa, Telefone
from slth.serializer import Serializer, LinkField


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class Register(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = RegisterForm(endpoint=self)


class AddUser(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = UserForm(instance=User(), request=request)

class EditUser(Endpoint):

    def __init__(self, request, pk):
        super().__init__(request)
        self.form = (
            UserForm(instance=User.objects.get(pk=pk), request=request)
            .fieldset('Dados Gerais', ('username', ('first_name', 'last_name'), 'email'))
            .fieldset('Grupos', ('groups',))
        )

class ListUsers(Endpoint):

    def __init__(self, request):
        super().__init__(request)
        self.serializer = Serializer(User.objects.all())
        

class ViewUser(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(User.objects.get(pk=pk), request=request)
            .fieldset('Dados Gerais', (('username', 'email'),))
            .fieldset('Dados Pessoais', ('first_name', 'last_name'))
            .fields('password')
            .relation('groups')
        )
    

class CadastrarPessoa(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = (
            FormFactory(instance=Pessoa(), request=request)
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )


class ListarPessoas(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.serializer = Serializer(Pessoa.objects, request)


class VisualizarPessoa(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = Serializer(Pessoa.objects.get(pk=pk), request).fields('id', 'nome')

    def check_permission(self):
        return True
    
class VisualizarPessoa2(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = Serializer(Pessoa.objects.get(pk=pk), request).fieldset('Dados Gerais', ('id', 'nome'))
    

class VisualizarCidade(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(self.objects('test.cidade').get(pk=pk), self.request)
            .fieldset('Dados Gerais', ('id', 'nome'), LinkField('prefeito', VisualizarPessoa))
            .fieldset('Prefeito', ('id', 'nome'), relation='prefeito')
            .endpoint('Cidades Vizinhas', CidadesVizinhas)
            .serialize()
        )



class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('test.cidade').all()
