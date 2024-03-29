from slth.endpoints import Endpoint, ChildEndpoint, FormFactory
from .forms import RegisterForm, UserForm, CadastrarCidadeForm
from django.contrib.auth.models import User, Group
from .models import Pessoa, Cidade
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
        self.serializer = (
            User.objects.search('username').fields('username', 'is_superuser').filters('is_superuser', 'groups').contextualize(request)
        )
        

class ViewUser(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(User.objects.get(pk=pk), request=request)
            .fieldset('Dados Gerais', (('username', 'email'),))
            .fieldset('Dados Pessoais', ('first_name', 'last_name'))
            .fields('password')
            .queryset('Grupos', 'groups')
        )
    

class CadastrarPessoa(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = (
            FormFactory(request, Pessoa())
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
            .form()
        )

class CadastrarPessoa2(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = (
            FormFactory(request, instance=Pessoa())
            .fields('nome', 'data_nascimento', 'salario', 'casado', 'sexo', 'cor_preferida')
            .form()
        )

class EditarPessoa(Endpoint):

    class Meta:
        icon = 'edit'
        verbose_name = 'Editar Pessoa'

    def __init__(self, request, pk):
        super().__init__(request)
        self.form = (
            FormFactory(request, Pessoa.objects.get(pk=pk))
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
            .form()
        )

    def check_permission(self):
        return True


class ListarPessoas(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.serializer = (
            Pessoa.objects.search('nome')
            .subsets('com_telefone_pessoal', 'sem_telefone_pessoal')
            .actions(
                'slth.test.endpoints.cadastrarpessoa',
                'slth.test.endpoints.editarpessoa'
            )
            .contextualize(request)
        )


class VisualizarPessoa(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(Pessoa.objects.get(pk=pk), request)
            .fields('id', 'nome', 'telefone_pessoal', 'telefones_profissionais')
        )

    def check_permission(self):
        return True
    
class VisualizarPessoa2(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(Pessoa.objects.get(pk=pk), request)
            .actions('slth.test.endpoints.editarpessoa')
            .fieldset('Dados Gerais', ('id', 'nome'), 'slth.test.endpoints.editarpessoa')
            .fieldset('Telefone Pessoal', ('ddd', 'numero'), attr='telefone_pessoal')
            .queryset('Telefones Profissionais', 'telefones_profissionais')
        )

class EstatisticaPessoal(Endpoint):
    def __init__(self, request, *args):
        super().__init__(request)
        self.serializer = Pessoa.objects.counter('sexo')

class VisualizarPessoa3(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(Pessoa.objects.get(pk=pk), request)
            .fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']])
            .fieldset('Dados para Contato', ['telefone_pessoal', 'get_qtd_telefones_profissionais'])
            .queryset('Telefones Profissionais', 'telefones_profissionais')
            .section('Ensino')
                .fieldset('Diários', ())
                .fieldset('Projetos Finais', ())
            .parent()
            .group('Group A')
                .fieldset('Fieldset A1', ())
                .fieldset('Fieldset A2', ())
            .parent()
            .dimention('Recursos Humanos')
                .section('Ponto')
                    .fieldset('Frequências', ())
                    .fieldset('Afastamentos', ())
                    .queryset('Usuários', 'get_usuarios')
                .parent()
                .fieldset('XXXXX', ())
                .endpoint('Estatística', 'slth.test.endpoints.estatisticapessoal')
                .queryset('Telefones Profissionais', 'telefones_profissionais')
                .section('PGD')
                    .fieldset('Adesões', ())
                .parent()
            .parent()
        )
    

class VisualizarCidade(Endpoint):
    def __init__(self, request, pk):
        super().__init__(request)
        self.serializer = (
            Serializer(self.objects('test.cidade').get(pk=pk), self.request)
            .fieldset('Dados Gerais', (('id', 'nome'), LinkField('prefeito', VisualizarPessoa)))
            .fieldset('Prefeito', ('id', 'nome'), attr='prefeito')
            .endpoint('Cidades Vizinhas', CidadesVizinhas)
        )

class CadastrarCidade(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = (
            FormFactory(request, Cidade())
            .form()
            .display(Serializer(Pessoa.objects.first()).fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']]))
        )

class CadastrarCidade2(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = CadastrarCidadeForm(Cidade.objects.first(), request)


class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('test.cidade').all()
    


class ListarFuncionario(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.serializer = self.objects('test.funcionario').actions('slth.test.endpoints.cadastrarfuncionario').contextualize(request)
    
class CadastrarFuncionario(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = FormFactory(request, self.objects('test.funcionario').model()).form()
