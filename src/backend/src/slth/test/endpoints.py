from slth.endpoints import Endpoint, ChildEndpoint, FormFactory
from .forms import RegisterForm, UserForm, CadastrarCidadeForm
from django.contrib.auth.models import User, Group
from .models import Pessoa, Cidade
from slth.serializer import Serializer, LinkField


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class Register(Endpoint):
    def get(self):
        return RegisterForm(request=self.request)


class AddUser(Endpoint):
    def get(self,):
        return UserForm(instance=User(), request=self.request)

class EditUser(Endpoint):

    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            UserForm(instance=User.objects.get(pk=self.pk), request=self.request)
            .fieldset('Dados Gerais', ('username', ('first_name', 'last_name'), 'email'))
            .fieldset('Grupos', ('groups',))
        )

class ListUsers(Endpoint):

    def get(self):
        return (
            User.objects.search('username').fields('username', 'is_superuser').filters('is_superuser', 'groups')
        )
        

class ViewUser(Endpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            Serializer(User.objects.get(pk=self.pk), request=self.request)
            .fieldset('Dados Gerais', (('username', 'email'),))
            .fieldset('Dados Pessoais', ('first_name', 'last_name'))
            .fields('password')
            .queryset('Grupos', 'groups')
        )
    

class CadastrarPessoa(Endpoint):
    def get(self):
        return (
            FormFactory(Pessoa())
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )

class CadastrarPessoa2(Endpoint):
    class Meta:
        verbose_name = 'Cadastrar Pessoa'

    def get(self):
        return (
            FormFactory(Pessoa())
            .fields('nome', 'data_nascimento', 'salario', 'casado', 'sexo', 'cor_preferida')
        )
    
class ExcluirPessoa(Endpoint):
    def __init__(self, pk):
        super().__init__()
        self.obj = self.objects('test.pessoa').get(pk=pk)

    def get(self):
        return FormFactory(self.obj, delete=True)

class EditarPessoa(Endpoint):

    class Meta:
        icon = 'edit'
        verbose_name = 'Editar Pessoa'

    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            FormFactory(Pessoa.objects.get(pk=self.pk))
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )

    def check_permission(self):
        return True


class ListarPessoas(Endpoint):
    class Meta:
        verbose_name = 'Pessoas'
    
    def get(self):
        return (
            Pessoa.objects.search('nome')
            .subsets('com_telefone_pessoal', 'sem_telefone_pessoal')
            .actions(
                'slth.test.endpoints.cadastrarpessoa',
                'slth.test.endpoints.editarpessoa',
                'slth.test.endpoints.excluirpessoa',
            )
        )


class VisualizarPessoa(Endpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            Serializer(Pessoa.objects.get(pk=self.pk))
            .fields('id', 'nome', 'telefone_pessoal', 'telefones_profissionais')
        )

    def check_permission(self):
        return True


class VisualizarPessoa2(Endpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            Serializer(Pessoa.objects.get(pk=self.pk))
            .actions('slth.test.endpoints.editarpessoa')
            .fieldset('Dados Gerais', ('id', 'nome'), 'slth.test.endpoints.editarpessoa')
            .fieldset('Telefone Pessoal', ('ddd', 'numero'), attr='telefone_pessoal')
            .queryset('Telefones Profissionais', 'telefones_profissionais')
        )

class EstatisticaPessoal(Endpoint):
    def get(self):
        return Pessoa.objects.counter('sexo', chart='donut') 

class VisualizarPessoa3(Endpoint):
    def __init__(self, pk):
        self.pk = pk
        super().__init__()

    def get(self):
        return (
            Serializer(Pessoa.objects.get(pk=self.pk), request=self.request)
            .fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']])
            .fieldset('Dados para Contato', ['telefone_pessoal', 'get_qtd_telefones_profissionais'])
            .queryset('Telefones Profissionais', 'telefones_profissionais')
            .section('Ensino')
                .fieldset('Diários', ())
                .fieldset('Projetos Finais', ())
            .parent()
            .group('Group A')
                .fieldset('Fieldset A1', (['id']))
                .fieldset('Fieldset A2', (['sexo']))
                .section('Section A3')
                    .fieldset('Frequências', ())
                    .fieldset('Afastamentos', ())
                    .queryset('Usuários', 'get_usuarios')
                .parent()
            .parent()
            .dimention('Recursos Humanos')
                .section('Ponto')
                    .fieldset('Frequências', ())
                    .fieldset('Afastamentos', ())
                    .queryset('Usuários', 'get_usuarios')
                .parent()
                .section('Detalhamento')
                    .fieldset('XXXXX', ())
                    .endpoint('Estatística', 'slth.test.endpoints.estatisticapessoal')
                    .queryset('Telefones Profissionais', 'telefones_profissionais')
                .parent()
                .section('PGD')
                    .fieldset('Adesões', ())
                .parent()
            .parent()
        )
    

class EditarCidade(Endpoint):
    def __init__(self, pk):
        super().__init__()
        self.obj = self.objects('test.cidade').get(pk=pk)

    def get(self):
        return CadastrarCidadeForm(request=self.request)

class VisualizarCidade(Endpoint):
    def __init__(self, pk):
        super().__init__()
        self.obj = self.objects('test.cidade').get(pk=pk)
    
    def get(self):
        return  (
            self.obj.serializer()
            .fieldset('Dados Gerais', (('id', 'nome'), LinkField('prefeito', VisualizarPessoa), 'get_imagem'))
            # .fields('get_mapa')
            .fields('get_banner', 'get_steps', 'get_qrcode', 'get_badge', 'get_status', 'get_progresso', 'get_boxes', 'get_shell', 'get_link')
            .fieldset('Prefeito', [('id', 'nome')], attr='prefeito')
            .queryset('Vereadores', 'vereadores')
            .endpoint('Cidades Vizinhas', CidadesVizinhas)
        )


class ExcluirCidade(Endpoint):
    def __init__(self, pk):
        super().__init__()
        self.obj = self.objects('test.cidade').get(pk=pk)

    def get(self):
        return FormFactory(self.obj, delete=True)

class CadastrarCidade(Endpoint):
    def get(self):
        return (
            FormFactory(Cidade()).display(Pessoa.objects.first().serializer().fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']]))
        )

class CadastrarCidade2(Endpoint):
    
    def get(self):
        return CadastrarCidadeForm(Cidade.objects.first(), self.request)


class ListarCidades(Endpoint):
    class Meta:
        verbose_name = 'Cidades'

    def get(self):
        return self.objects('test.cidade').all()


class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('test.cidade').all().actions(
            'slth.test.endpoints.cadastrarcidade',
            'slth.test.endpoints.editarcidade',
            'slth.test.endpoints.excluircidade'
        )
    


class ListarFuncionario(Endpoint):
    def get(self):
        return (
            self.objects('test.funcionario')
            .actions('slth.test.endpoints.cadastrarfuncionario')
        )
    
class CadastrarFuncionario(Endpoint):
    def get(self):
        return FormFactory(
            self.objects('test.funcionario').model()
        )