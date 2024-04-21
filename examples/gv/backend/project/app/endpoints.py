from .models import *
from slth import endpoints, meta
from .forms import ConsultarIAForm, EnviarRespostaForm


class Administradores(endpoints.AdminEndpoint[Administrador]):
    def check_permission(self):
        return self.check_role('administrador')

class Estados(endpoints.AdminEndpoint[Estado]):
    def check_permission(self):
        return self.check_role('administrador')

class Prioridades(endpoints.AdminEndpoint[Prioridade]):
    def check_permission(self):
        return self.check_role('administrador')

class Assuntos(endpoints.AdminEndpoint[Assunto]):
    def check_permission(self):
        return self.check_role('administrador')
    
class VisualizarTopico(endpoints.ViewEndpoint[Topico]):
    def check_permission(self):
        return self.check_role('administrador')

class PerguntasFrequentes(endpoints.AdminEndpoint[PerguntaFrequente]):
    def check_permission(self):
        return self.check_role('administrador')

class Especialistas(endpoints.AdminEndpoint[Especialista]):
    def check_permission(self):
        return self.check_role('administrador')

class Clientes(endpoints.AdminEndpoint[Cliente]):
    def check_permission(self):
        return self.check_role('administrador')

class Consultas(endpoints.AdminEndpoint[Consulta]):
    def check_permission(self):
        return self.check_role('administrador')

class MinhasConsultas(endpoints.ListEndpoint[Consulta]):
    def get(self):
        return (
            super().get().fields('get_prioridade', 'topico', 'pergunta')
            .search('pergunta')
            .filters('prioridade', 'topico')
            .actions('consultar', 'visualizarresposta')
            .subsets('nao_respondidas', 'respondidas')
            .filter(consultante__cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('consultante')

class Consultar(endpoints.AddEndpoint[Consulta]):
    def get(self):
        return super().get().setvalue(
            consultante=Consultante.objects.get(cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('consultante')

class VisualizarResposta(endpoints.InstanceEndpoint[Consulta]):
    class Meta:
        modal = False
        verbose_name = 'Visualizar Resposta'

    def get(self):
        return (
            self.serializer()
            .field('get_passos')
            .fieldset('Dados Gerais', ('consultante', ('get_prioridade', 'topico'), 'pergunta', 'observacao'))
            .fieldset('Datas', (('data_pergunta', 'data_consulta', 'data_resposta'),))
            .queryset('Anexos', 'get_anexos')
            .queryset('Interações', 'get_interacoes')
            .fieldset('Resposta', ('resposta',))
        )
    
    def check_permission(self):
        return self.get_instance().data_resposta

class ConsultarIA(endpoints.InstanceFormEndpoint[ConsultarIAForm]):
    class Meta:
        icon = 'robot'
        modal = True
        verbose_name = 'Consultar I.A.'

class EnviarResposta(endpoints.InstanceFormEndpoint[EnviarRespostaForm]):
    class Meta:
        icon = 'location-arrow'
        modal = True
        verbose_name = 'Enviar Resposta'

    def check_permission(self):
        return self.get_instance().data_consulta
    
class Estatisticas(endpoints.Endpoint):
    def get(self):
        return (
            self.serializer()
            .fieldset('Consultas', (('consultas_por_prioridade', 'consultas_por_topico'),))
        )

    @meta('Consultas por Prioridade')
    def consultas_por_prioridade(self):
        return Consulta.objects.counter('prioridade', chart='donut')
    
    @meta('Consultas por Tópico')
    def consultas_por_topico(self):
        return Consulta.objects.counter('topico', chart='donut')
    
class Bi(endpoints.Endpoint):
    def get(self):
        return (
            Consulta.objects.filters('consultante', 'consultante__cliente')
            .bi(
                ('quantidade_geral', 'total_por_cliente'),
                ('total_por_prioridade', 'total_por_topico'),
                ('total_por_mes',)
            )
        )

class VisualizarConsulta(endpoints.ViewEndpoint[Consulta]):
    def get(self):
        return super().get().actions('assumirconsulta', 'deixarconsulta')
    
    def check_permission(self):
        return self.check_role('administrador', 'especialista')

class ConsultasAguardandoEspecialista(endpoints.ListEndpoint[Consulta]):
    def get(self):
        return super().get().aguardando_especialista().fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'get_limite_resposta').actions('visualizarconsulta')
    def check_permission(self):
        return self.check_role('especialista')

class AssumirConsulta(endpoints.ChildInstanceEndpoint):
    class Meta:
        verbose_name = 'Assumir Consulta'
    def get(self):
        return super().formfactory().fields('especialista').setvalue(
            especialista=Especialista.objects.get(cpf=self.request.user.username)
        )
    def check_permission(self):
        return self.check_role('especialista') and not self.get_instance().especialista_id
    
class DeixarConsulta(endpoints.ChildInstanceEndpoint):
    class Meta:
        verbose_name = 'Deixar Consulta'
    def get(self):
        return super().formfactory().fields('especialista')
    def check_permission(self):
        return self.check_role('especialista') and self.get_instance().especialista_id
