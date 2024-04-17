from slth.endpoints import Endpoint, ViewEndpoint, AdminEndpoint, AddEndpoint, InstanceFormEndpoint, ListEndpoint
from slth.queryset import QuerySet
from .forms import ResponderQuestionarioForm
from django.contrib.auth.models import User, Group
from .models import *

class TiposRedeSocial(AdminEndpoint[TipoRedeSocial]):
    pass

class NiveisEnsino(AdminEndpoint[NivelEnsino]):
    pass

class SituacoesEscolaridade(AdminEndpoint[SituacaoEscolaridade]):
    pass

class Poderes(AdminEndpoint[Poder]):
    pass

class Esferas(AdminEndpoint[Esfera]):
    pass

class TiposOrgao(AdminEndpoint[TipoOrgao]):
    pass

class Orgaos(AdminEndpoint[Orgao]):
    pass

class Estados(AdminEndpoint[Estado]):
    pass

class Municipios(AdminEndpoint[Municipio]):
    pass

class PessoasFisicas(AdminEndpoint[PessoaFisica]):
    pass


class InstrumentosAvaliativos(AdminEndpoint[InstrumentoAvaliativo]):
    pass

class ResponderQuestionario(InstanceFormEndpoint[ResponderQuestionarioForm]):
    class Meta:
        icon = 'pen-to-square'
        verbose_name = 'Responder Questionário'


class VisualizarRespostasQuestionario(ViewEndpoint[Questionario]):
    class Meta:
        icon = 'eye'
        modal = True
        verbose_name = 'Visualizar Questionário'

    def get(self):
        return (
            super().get()
            .queryset('Respostas', 'get_perguntas')
        )

class VisualizarPergunta(ViewEndpoint[Pergunta]):
    class Meta:
        icon = 'eye'
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
