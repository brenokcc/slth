from slth.endpoints import Endpoint, ViewEndpoint, EditEndpoint, ListEndpoint, AddEndpoint, InstanceEndpoint, DeleteEndpoint, FormEndpoint, ChildEndpoint, InstanceFormEndpoint
from .forms import RegisterForm, UserForm, CadastrarCidadeForm
from django.contrib.auth.models import User, Group
from .models import Pessoa, Cidade, Funcionario, Telefone
from slth.serializer import LinkField
from slth.components import Grid


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')

class CadastrarGrupo(AddEndpoint[Group]): pass
class EditarGrupo(EditEndpoint[Group]): pass
class VisualizarGrupo(ViewEndpoint[Group]): pass
class ExcluirGrupo(DeleteEndpoint[Group]): pass
class ListarGrupo(ListEndpoint[Group]): pass

class ListarTelefones(ListEndpoint[Telefone]): pass


class Register(FormEndpoint[RegisterForm]): pass


class AddUser(FormEndpoint[UserForm]): pass
class EditUser(InstanceFormEndpoint[UserForm]):
    def get(self):
        super().get().fieldset('Dados Gerais', ('username', ('first_name', 'last_name'), 'email')).fieldset('Grupos', ('groups',))

class ListUsers(ListEndpoint[User]):
    def get(self):
        return super().get().search('username').fields('username', 'is_superuser').filters('is_superuser', 'groups')


class ViewUser(ViewEndpoint[User]):

    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', (('username', 'email'),))
            .fieldset('Dados Pessoais', ('first_name', 'last_name'))
            .fields('password')
            .queryset('Grupos', 'groups')
        )

class CadastrarPessoa(AddEndpoint[Pessoa]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )

class CadastrarPessoa2(AddEndpoint[Pessoa]):
    class Meta:
        verbose_name = 'Cadastrar Pessoa'

    def get(self):
        return super().get().fields('nome', 'data_nascimento', 'salario', 'casado', 'sexo', 'cor_preferida')

class ExcluirPessoa(DeleteEndpoint[Pessoa]): pass

class EditarPessoa(EditEndpoint[Pessoa]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', ('nome',))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )

class ListarPessoas(ListEndpoint[Pessoa]):

    def get(self):
        return (
            super().get().search('nome').filters('data_nascimento', 'casado', 'sexo')
            .subsets('com_telefone_pessoal', 'sem_telefone_pessoal')
            .actions('visualizarpessoa2')
        )


class VisualizarPessoa(ViewEndpoint[Pessoa]): pass


class VisualizarPessoa2(InstanceEndpoint[Pessoa]):

    def get(self):
        return (
            super().get()
            .actions('editarpessoa')
            .fieldset('Dados Gerais', fields=[('id', 'nome')])
            .fieldset('Telefone Pessoal', ('ddd', 'numero'), attr='telefone_pessoal', actions=['editarpessoa'])
            .queryset('Telefones Profissionais', 'telefones_profissionais')
        )

class EstatisticaPessoal(Endpoint):
    def get(self):
        return Pessoa.objects.counter('sexo', chart='donut')

class Estatisticas(Endpoint):
    def get(self):
        grid = Grid()
        grid.append(Pessoa.objects.counter('sexo', chart='donut', title='Pessoas por Sexo'))
        grid.append(Pessoa.objects.counter('cor_preferida', chart='bar', title='Pessoas por Cor'))
        grid.append(Cidade.objects.counter('prefeito', chart='line', title='Cidades por Prefeito'))
        return grid 

class VisualizarPessoa3(InstanceEndpoint[Pessoa]):

    def get(self):
        return (
            super().get()
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
            .group('Group B')
                .section('Ponto')
                    .fieldset('Frequências', ())
                    .fieldset('Afastamentos', ())
                    .queryset('Usuários', 'get_usuarios')
                .parent()
                .section('Detalhamento')
                    .fieldset('XXXXX', ())
                    .endpoint('Estatística', 'estatisticapessoal')
                    .queryset('Telefones Profissionais', 'telefones_profissionais')
                .parent()
                .section('PGD')
                    .fieldset('Adesões', ())
                .parent()
            .parent()
        )
    

class EditarCidade(EditEndpoint[Cidade]): pass

class VisualizarCidade(ViewEndpoint[Cidade]):
    def get(self):
        return  (
            super().get()
            .fieldset('Dados Gerais', (('id', 'nome'), LinkField('prefeito', VisualizarPessoa), 'get_imagem'))
            # .fields('get_mapa')
            .fields('get_banner', 'get_steps', 'get_qrcode', 'get_badge', 'get_status', 'get_progresso', 'get_boxes', 'get_shell', 'get_link')
            .fieldset('Prefeito', [('id', 'nome')], attr='prefeito')
            .queryset('Vereadores', 'vereadores')
            .endpoint('Cidades Vizinhas', CidadesVizinhas)
        )


class ExcluirCidade(DeleteEndpoint[Cidade]): pass
class CadastrarCidade(AddEndpoint[Cidade]):
    def get(self):
        return (
            super().get().display(Pessoa.objects.first().serializer().fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']]))
        )

class CadastrarCidade2(FormEndpoint[CadastrarCidadeForm]): pass

class ListarCidades(Endpoint):
    def get(self):
        return self.objects('test.cidade').search('nome').filters('prefeito')


class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('test.cidade').all().actions(
            'cadastrarcidade',
            'editarcidade',
            'excluircidade'
        )
    


class ListarFuncionario(Endpoint):
    
    def get(self):
        return self.objects('test.funcionario').actions('cadastrarfuncionario')
    
class CadastrarFuncionario(AddEndpoint[Funcionario]): pass