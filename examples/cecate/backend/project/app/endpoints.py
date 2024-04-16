from slth.endpoints import Endpoint, ViewEndpoint, AdminEndpoint, AddEndpoint, InstanceFormEndpoint
from .forms import ResponderQuestionarioForm
from django.contrib.auth.models import User, Group
from .models import *


class Estados(AdminEndpoint[Estado]):
    def get(self):
        return super().get().actions(view='visualizarestado')

class VisualizarEstado(ViewEndpoint[Estado]):
    def get(self):
        return (
            super().get()
            .fieldset('Dados Gerais', [('sigla', 'nome')])
            .queryset('Municípios', 'municipio_set', actions=('edit', 'delete', 'add'), related_field='estado')
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

class ResponderQuestionario(InstanceFormEndpoint[ResponderQuestionarioForm]):
    class Meta:
        verbose_name = 'Responder Questionário'


class VisualizarQuestionario(ViewEndpoint[Questionario]):
    class Meta:
        modal = True
        verbose_name = 'Visualizar Questionário'

    def get(self):
        return (
            super().get()
            .queryset('Respostas', 'get_perguntas')
        )

class VisualizarPergunta(ViewEndpoint[Pergunta]):
    class Meta:
        modal = True
        verbose_name = 'Visualizar Pergunta'

    def get(self):
        return (
            super().get()
            .queryset('Respostas', 'get_respostas')
            .fields('get_estatistica')
        )
    
class ResponderQuestionarioPendente(Endpoint):
    class Meta:
        verbose_name = 'Responder Questionário'

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questionario = None
    

    def get(self):
        return ResponderQuestionarioForm(instance=self.questionario, request=self.request)
    
    def check_permission(self):
        self.questionario =  Questionario.objects.filter(
            respondente__cpf=self.request.user.username
        ).first()
        return self.questionario
