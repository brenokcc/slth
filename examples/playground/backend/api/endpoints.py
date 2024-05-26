from slth.endpoints import Endpoint, ViewEndpoint, EditEndpoint, AdminEndpoint, ListEndpoint, AddEndpoint, InstanceEndpoint, DeleteEndpoint, ChildEndpoint
from .forms import RegisterForm, UserForm, CadastrarCidadeForm, ResponderQuestionarioForm
from django.contrib.auth.models import User, Group
from .models import *
from slth.components import Grid


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')

class Grupos(AdminEndpoint[Group]):
    def get(self):
        return super().get().limit(2)

class ListarTelefones(ListEndpoint[Telefone]):
    pass


class AddUser(AddEndpoint[User]):
    pass

class EditUser(EditEndpoint[User]):
    def get(self):
        return super().get().fieldset('Dados Gerais', ('username', ('first_name', 'last_name'), 'email'))

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
            .fieldset('Dados Gerais', ('nome', 'foto'))
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )

class CadastrarPessoa2(AddEndpoint[Pessoa]):
    class Meta:
        verbose_name = 'Cadastrar Pessoa'

    def get(self):
        return super().get().fields('nome', 'foto', 'data_nascimento', 'salario', 'casado', 'sexo', 'cor_preferida')

class ExcluirPessoa(DeleteEndpoint[Pessoa]): pass

class EditarPessoa(EditEndpoint[Pessoa]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', ['nome','foto', ('sexo', 'data_nascimento')])
            .fieldset('Telefone Pessoal', ('telefone_pessoal',))
            .fieldset('Telefones Profissionais', ('telefones_profissionais',))
        )
    def check_permission(self):
        return True

class ListarPessoas(ListEndpoint[Pessoa]):
    class Meta:
        verbose_name = 'Listar Pessoas'
    def get(self):
        return (
            super().get().fields('nome', 'get_foto', 'sexo', 'cor_preferida', 'get_hello').search('nome').filters('data_nascimento', 'casado', 'sexo')
            .subsets('homens', 'mulheres')
            .actions('visualizarpessoa2', 'edit', 'add').limit(2, 4)
        )


class VisualizarPessoa(ViewEndpoint[Pessoa]): pass

class VisualizarPessoa2(ViewEndpoint[Pessoa]):
    class Meta:
        modal = False
        verbose_name = 'Visualizar'
        
    def get(self):
        return (
            super().get()
            .actions('edit')
            .fieldset('Dados Gerais', fields=[('id', 'nome')])
            .fieldset('Telefone Pessoal', [('ddd', 'numero')], attr='telefone_pessoal', actions=['edit'])
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
            .fieldset('Dados Gerais', (('id', 'nome'), 'prefeito', 'get_imagem'))
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
            super().get().display(
                Pessoa.objects.first().serializer().fieldset('Dados Gerais', ['nome', ['sexo', 'data_nascimento']])
            ).actions(prefeito='cadastrarpessoa')
        )

class CadastrarCidade2(AddEndpoint[Cidade]): pass

class ListarCidades(Endpoint):
    def get(self):
        return self.objects('api.cidade').search('nome').filters('prefeito').actions('add', 'edit')


class CidadesVizinhas(ChildEndpoint):

    def get(self):
        return self.objects('api.cidade').all().actions(
            'cadastrarcidade',
            'editarcidade',
            'excluircidade'
        )



class ListarFuncionario(Endpoint):

    def get(self):
        return self.objects('api.funcionario').actions('cadastrarfuncionario')


class CadastrarFuncionario(AddEndpoint[Funcionario]):
    class Meta:
        icon = 'plus'
        verbose_name = 'Cadastrar Funcionário'
    def get(self):
        return super().get().info('Preencha o formulário corretamente')
    
class Estados(AdminEndpoint[Estado]):
    def get(self):
        return super().get().actions(view='visualizarestado')

class VisualizarEstado(ViewEndpoint[Estado]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', [('sigla', 'nome')])
            .queryset('Municípios', 'municipio_set')
        )

class Municipios(AdminEndpoint[Municipio]):
    pass

class PessoasFisicas(AdminEndpoint[PessoaFisica]):
    class Meta:
        verbose_name = 'Pessoas Físicas'

    def get(self):
        return super().get().actions(add='cadastrarpessoafisica')

class CadastrarPessoaFisica(AddEndpoint[PessoaFisica]):
    class Meta:
        verbose_name = 'Cadastrar Pessoa Física'

    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', ('foto', ('cpf', 'nome')))
            .fieldset('Dados para Contato', (('telefone', 'email'),))
        )

class InstrumentosAvaliativos(AdminEndpoint[InstrumentoAvaliativo]):
    def get(self):
        return super().get().actions(view='visualizarinstrumentoavaliativo')

class VisualizarInstrumentoAvaliativo(ViewEndpoint[InstrumentoAvaliativo]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', ['responsavel', ('data_inicio', 'data_termino'), 'instrucoes'])
            .queryset('Perguntas', 'pergunta_set', actions=('edit', 'delete', 'add', 'visualizarpergunta'), related_field='instrumento_avaliativo')
            .queryset('Questionários', 'questionario_set', actions=('add', 'responderquestionario', 'visualizarquestionario'), related_field='instrumento_avaliativo')
        )
