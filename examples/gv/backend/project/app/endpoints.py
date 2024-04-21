from .models import *
from slth import endpoints, meta
from .forms import ConsultarIAForm, EnviarRespostaForm


class Estados(endpoints.AdminEndpoint[Estado]):
    pass

class Prioridades(endpoints.AdminEndpoint[Prioridade]):
    pass

class Assuntos(endpoints.AdminEndpoint[Assunto]):
    pass

class VisualizarTopico(endpoints.ViewEndpoint[Topico]):
    pass

class PerguntasFrequentes(endpoints.AdminEndpoint[PerguntaFrequente]):
    pass

class Especialistas(endpoints.AdminEndpoint[Especialista]):
    pass

class Clientes(endpoints.AdminEndpoint[Cliente]):
    pass

class Consultantes(endpoints.AdminEndpoint[Consultante]):
    pass

class Consultas(endpoints.AdminEndpoint[Consulta]):
    pass

class MinhasConsultas(endpoints.ListEndpoint[Consulta]):
    def get(self):
        return (
            super().get().fields('get_prioridade', 'topico', 'pergunta')
            .search('pergunta')
            .filters('prioridade', 'topico')
            .actions('consultar', 'visualizarresposta')
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
        return True


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
    
# class X(endpoints.InstanceEndpoint[Consulta]):
#     def get(self):
#         return super().formfactory().fields('data_consulta')


# class Y(endpoints.InstanceEndpoint[Consulta]):
#     def get(self):
#         return super().formfactory().fields('data_consulta')
    
#     def check_permission(self):
#         return not self.get_instance().data_consulta
        
