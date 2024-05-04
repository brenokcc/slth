from .models import *
from slth import endpoints, meta
from slth import forms
from slth.components import WebConf


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
            super().get().fields(('get_prioridade', 'topico', 'data_pergunta'), 'pergunta')
            .search('pergunta')
            .filters('prioridade', 'topico')
            .actions('consultar', 'visualizarminhaconsulta')
            .subsets('nao_respondidas', 'respondidas')
            .filter(consultante__cpf=self.request.user.username)
        ).rows()
    
    def check_permission(self):
        return self.check_role('consultante', superuser=False)

class Consultar(endpoints.AddEndpoint[Consulta]):
    def get(self):
        return super().get().fields(
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
            .actions('videochamada')
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


class EstatisticaConsultoria(endpoints.Endpoint):
    class Meta:
        verbose_name = 'Estatísticas'
    
    def get(self):
        return (
            Consulta.objects
            .filters(
                'prioridade', 'topico', 'topico__assunto',
                'consultante', 'consultante__cliente', 'especialista', 'consultante__cliente__estado'
            )
            .bi(
                ('quantidade_geral', 'total_clientes', 'total_consultantes'),
                ('total_especialistas', 'total_por_estado', 'total_por_especialista'),
                ('total_por_prioridade', 'total_por_assunto', 'total_por_topico'),
                ('total_por_mes', 'total_por_cliente'),
            )
        )
    def check_permission(self):
        return self.check_role('administrador')

class VisualizarConsulta(endpoints.ViewEndpoint[Consulta]):
    
    def check_permission(self):
        return self.check_role('administrador', 'especialista')

class ConsultasAguardandoEspecialista(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return (
            super().get().aguardando_especialista().filters('topico', 'prioridade', 'consultante__cliente')
            .filter(topico__assunto__in=especialista.assuntos.values_list('pk', flat=True))
            .filter(consultante__cliente__estado__in=especialista.estados.values_list('pk', flat=True))
            .fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'get_limite_resposta')
            .actions('visualizarconsulta'))
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)
    
class ConsultasEmAtendimento(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return super().get().filters('topico', 'prioridade', 'consultante__cliente').filter(especialista=especialista, data_resposta__isnull=True).fields('prioridade', 'topico', 'pergunta', 'data_pergunta', 'get_limite_resposta').actions('visualizarconsulta')
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)
    
class ConsultasAtendidas(endpoints.ListEndpoint[Consulta]):
    def get(self):
        especialista=Especialista.objects.get(cpf=self.request.user.username)
        return super().get().filters('topico', 'prioridade', 'consultante__cliente').filter(especialista=especialista, data_resposta__isnull=False).fields(('prioridade', 'topico'), ('data_pergunta', 'data_resposta'), 'pergunta', 'resposta').actions('visualizarconsulta').rows()
    
    def check_permission(self):
        return self.check_role('especialista', superuser=False)


class AdicionarABaseConhecimento(endpoints.ChildInstanceEndpoint):
    class Meta:
        icon = 'file-circle-plus'
        verbose_name = 'Adicionar a Base de Conhecimento'

    def get(self):
        return self.formfactory().fields()

    def post(self):
        pergunta_frequente = PerguntaFrequente.objects.create(
            topico=self.instance.topico,
            pergunta=self.instance.pergunta_ia,
            resposta=self.instance.resposta
        )
        self.instance.pergunta_frequente = pergunta_frequente
        return super().post()

    def check_permission(self):
        instance = self.get_instance()
        return self.check_role('administrador') and instance.data_resposta and not instance.pergunta_frequente_id

class AssumirConsulta(endpoints.ChildInstanceEndpoint):
    class Meta:
        icon = 'file-circle-check'
        verbose_name = 'Assumir Consulta'
    
    def get(self):
        observacao = '''Ao assumir a consulta, ela ficará bloqueada para os demais especialistas. Portanto,
        'realize essa ação quando for respondê-la. Caso não esteja apto para concluir a resposta depois de
        'assumi-la, libere-a para que outro especialista possa respondê-la.'''
        return super().formfactory().info(observacao).fields(
            especialista=Especialista.objects.get(cpf=self.request.user.username)
        )
    
    def check_permission(self):
        return self.check_role('especialista') and not self.get_instance().especialista_id

class ConsultarIA(endpoints.ChildInstanceEndpoint):
    arquivos = forms.ModelMultipleChoiceField(Arquivo.objects, label='Arquivos', pick=True, required=False)
    class Meta:
        icon = 'robot'
        modal = True
        verbose_name = 'Consultar I.A.'

    def get(self):
        return (
            self.formfactory()
            .display('Dados Gerais', (('topico', 'get_limite_resposta'),))
            .info('Abaixo serão listados os arquivos específicos do cliente. Para realizar a consulta com base neles ao invés dos arquivos da base de conhecimento, selecione uma ou mais opção.')
            .initial(pergunta_ia=self.instance.pergunta)
            .choices(arquivos=self.instance.consultante.cliente.arquivocliente_set.all())
            .fields('pergunta_ia', 'arquivos')
        )

    def post(self):
        self.instance.data_consulta = datetime.datetime.now()
        self.instance.resposta_ia = self.instance.topico.perguntar_inteligencia_artificial(
            self.cleaned_data['pergunta_ia'], self.cleaned_data['arquivos']
        )
        self.instance.save()
        return super().post()

    def check_permission(self):
        return self.check_role('especialista') and self.get_instance().especialista_id and not self.get_instance().data_resposta
    
    def get_arquivos_queryset(self, queryset, values):
        return queryset
    
    def on_consultante_change(self, controller, values):
        if values.get('pergunta_ia'): controller.show('pergunta_ia')
        else: controller.show('pergunta_ia')

class EnviarResposta(endpoints.ChildInstanceEndpoint):
    class Meta:
        icon = 'location-arrow'
        modal = True
        verbose_name = 'Enviar Resposta'

    def get(self):
        return self.formfactory().initial(resposta=self.instance.resposta_ia).fields('resposta')

    def post(self):
        self.instance.data_resposta = datetime.datetime.now()
        self.instance.save()
        return super().post()

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


class VideoChamada(endpoints.InstanceEndpoint[Consulta]):

    class Meta:
        icon = 'video'
        title = 'Video Chamada'
        modal = False

    def get(self):
        consulta = self.get_instance()
        if self.request.user.username == consulta.consultante.cpf:
            receiver = consulta.especialista.cpf
        if self.request.user.username == consulta.especialista.cpf:
            receiver = consulta.consultante.cpf
        return WebConf(self.request.user.username, receiver)

    def check_permission(self):
        consulta = self.get_instance()
        usernames = [consulta.consultante.cpf, consulta.especialista and consulta.especialista.cpf]
        return consulta.especialista_id and self.request.user.username in usernames
