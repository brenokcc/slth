from .models import *
from slth import endpoints, meta
from .forms import ConsultarIAForm, EnviarRespostaForm, AdicionarABaseConhecimentoForm


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
            .actions('consultar', 'visualizarminhaconsulta')
            .subsets('nao_respondidas', 'respondidas')
            .filter(consultante__cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('consultante', superuser=False)

class Consultar(endpoints.AddEndpoint[Consulta]):
    def get(self):
        return super().get().setvalue(
            consultante=Consultante.objects.get(cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('consultante')

class VisualizarMinhaConsulta(endpoints.InstanceEndpoint[Consulta]):
    class Meta:
        modal = False
        verbose_name = 'Visualizar'

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
        return self.get_instance()
    
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
    
    def check_permission(self):
        return self.check_role('administrador', 'especialista')

class ConsultasAguardandoEspecialista(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return (
            super().get().aguardando_especialista()
            .filter(topico__assunto__in=especialista.assuntos.values_list('pk', flat=True))
            .filter(consultante__cliente__estado__in=especialista.estados.values_list('pk', flat=True))
            .fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'get_limite_resposta')
            .actions('visualizarconsulta'))
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)
    
class ConsultasEmAtendimento(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return super().get().filter(especialista=especialista, data_resposta__isnull=True).fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'get_limite_resposta').actions('visualizarconsulta')
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)
    
class ConsultasAtendidas(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return super().get().filter(especialista=especialista, data_resposta__isnull=False).fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'data_resposta').actions('visualizarconsulta')
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)


class AdicionarABaseConhecimento(endpoints.ChildInstanceFormEndpoint[AdicionarABaseConhecimentoForm]):
    class Meta:
        icon = 'file-circle-plus'
        verbose_name = 'Adicionar a Base de Conhecimento'

    def check_permission(self):
        instance = self.get_instance()
        return self.check_role('administrador') and instance.data_resposta and not instance.pergunta_frequente_id

class AssumirConsulta(endpoints.ChildInstanceEndpoint):
    class Meta:
        icon = 'file-circle-check'
        verbose_name = 'Assumir Consulta'
    
    def get(self):
        return super().formfactory().fields(
            especialista=Especialista.objects.get(cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('especialista') and not self.get_instance().especialista_id

class ConsultarIA(endpoints.ChildInstanceFormEndpoint[ConsultarIAForm]):
    class Meta:
        icon = 'robot'
        modal = True
        verbose_name = 'Consultar I.A.'

    def check_permission(self):
        return self.check_role('especialista') and self.get_instance().especialista_id and not self.get_instance().data_resposta

class EnviarResposta(endpoints.InstanceFormEndpoint[EnviarRespostaForm]):
    class Meta:
        icon = 'location-arrow'
        modal = True
        verbose_name = 'Enviar Resposta'

    def check_permission(self):
        return self.check_role('especialista') and self.get_instance().data_consulta and not self.get_instance().data_resposta

class LiberarConsulta(endpoints.ChildInstanceEndpoint):
    class Meta:
        icon = 'file-export'
        verbose_name = 'Liberar Consulta'
    
    def get(self):
        return super().formfactory().fields(especialista=None)
    
    def check_permission(self):
        return self.check_role('especialista', 'administrador') and self.get_instance().especialista_id and not self.get_instance().data_resposta

