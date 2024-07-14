import os
from uuid import uuid1
from django.core.files.base import ContentFile
from slth import endpoints
from slth.components import Scheduler, ZoomMeet, TemplateContent, Response
from .models import *
from slth import forms
from .utils import buscar_endereco
from slth import printer
from slth.tests import RUNNING_TESTING
from .mail import send_mail
import requests
import base64


MENSAGEM_ASSINATURA_DIGITAL = '''
    Para realizar a assinatura digital, você deverá estar com o aplicativo Vadaas instalado em seu celular.
    Você receberá uma notificação para autorizar a assinatura após clicar no botão "Enviar".
    Conceda a autorização e aguarde até o que o documento seja assinado.

'''

class CIDs(endpoints.AdminEndpoint[CID]):
    def check_permission(self):
        return self.check_role('a')


class CIAPs(endpoints.AdminEndpoint[CIAP]):
    def check_permission(self):
        return self.check_role('a')


class ConselhosClasse(endpoints.AdminEndpoint[ConselhoClasse]):
    def check_permission(self):
        return self.check_role('a')


class Areas(endpoints.AdminEndpoint[Area]):
    def check_permission(self):
        return self.check_role('a')


class TiposAtendimento(endpoints.AdminEndpoint[TipoAtendimento]):
    pass


class UnidadesFederativas(endpoints.AdminEndpoint[Estado]):
    def check_permission(self):
        return self.check_role('a')


class Sexos(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipios(endpoints.AdminEndpoint[Municipio]):
    def check_permission(self):
        return self.check_role('a')

class Nucleos(endpoints.AdminEndpoint[Nucleo]):
    def get(self):
        return super().get().lookup(gestores__cpf='username')
    
    def check_permission(self):
        return self.check_role('a', 'g')
    
    def check_view_permission(self):
        return self.check_role('a', 'g')
    
    def check_add_permission(self):
        return self.check_role('a')
    
    def check_delete_permission(self):
        return self.check_role('a')

class CadastrarProfissionalSaudeNucleo(endpoints.RelationEndpoint[ProfissionalSaude]):
    class Meta:
        icon = 'plus'
        verbose_name = 'Adicionar Profissional'
    
    def formfactory(self):
        return (
            super()
            .formfactory().fields(nucleo=self.source.instance)
            .fieldset("Dados Gerais", ("nucleo", "pessoa_fisica:cadastrarpessoafisica",))
            .fieldset("Dados Profissionais", ("especialidade", ("conselho_profissional", "registro_profissional"), ("conselho_especialista", "registro_especialista"),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"),("residente", "perceptor"),),)
        )
    
    def get_nucleo_queryset(self, queryset, values):
        return queryset.lookup('g', gestores__cpf='username')
    
    def check_permission(self):
        return self.check_role('a', 'g')

class CadastrarProfissionalSaudeUnidade(endpoints.RelationEndpoint[ProfissionalSaude]):
    class Meta:
        icon = 'plus'
        verbose_name = 'Adicionar Profissional'
    def formfactory(self):
        return (
            super()
            .formfactory().fields(unidade=self.source.instance)
            .fieldset("Dados Gerais", ("unidade", "pessoa_fisica:cadastrarpessoafisica",))
            .fieldset("Dados Profissionais", ("especialidade", ("conselho_profissional", "registro_profissional")),)
            .fieldset(
                "Informações Adicionais", (
                    ("programa_provab", "programa_mais_medico"),
                    ("residente", "perceptor"),
                ),
            )
        )

class Unidades(endpoints.AdminEndpoint[Unidade]):
    def check_permission(self):
        return self.check_role('g', 'a')
    
    def check_add_permission(self):
        return self.check_role('g', 'a')
    
    def check_edit_permission(self):
        return self.check_role('g', 'a')
    
    def check_delete_permission(self):
        return self.check_role('a')
    
    def check_view_permission(self):
        return self.check_role('g', 'a')
    

class CadastrarUnidade(endpoints.AddEndpoint[Unidade]):
    class Meta:
        verbose_name = 'Cadastrar Unidade'

    def on_cep_change(self, controller, values):
        controller.set(**buscar_endereco(values.get('cep')))

    def check_permission(self):
        return self.check_role('g', 'a')

class Especialidades(endpoints.AdminEndpoint[Especialidade]):
    def check_permission(self):
        return self.check_role('a')


class PessoasFisicas(endpoints.AdminEndpoint[PessoaFisica]):
    def get(self):
        return super().get()
    def check_permission(self):
        return self.check_role('a')


class CadastrarPessoaFisica(endpoints.AddEndpoint[PessoaFisica]):
    def check_permission(self):
        return self.check_role('g', 'o')
    
    def on_cep_change(self, controller, values):
        dados = buscar_endereco(values.get('cep'))
        if dados:
            dados['endereco'] = dados.pop('logradouro')
        controller.set(**dados)


class ProfissionaisSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    def get(self):
        return (
            super().get().lookup('a')
            .lookup('g', nucleo__gestores__cpf='username')
            .lookup('o', nucleo__operadores__cpf='username')
        )

    def check_permission(self):
        return self.check_role('g', 'o', 'a')
    
    def check_add_permission(self):
        return False

    def check_edit_permission(self):
        return self.check_role('a', 'g')
    
    def check_delete_permission(self):
        return self.check_role('a')
    
    def contribute(self, entrypoint):
        if entrypoint == 'menu' and self.check_role('o', superuser=False):
            return False
        return super().contribute(entrypoint)

class EnviarNotificacaoAtendimento(endpoints.ChildEndpoint):

    class Meta:
        icon = "mail-bulk"
        verbose_name = 'Enviar Notificações'

    def get(self):
        return super().formfactory().fields()
    
    def post(self):
        usernames = []
        usernames.append(self.source.paciente.cpf)
        usernames.append(self.source.profissional.pessoa_fisica.cpf)
        if self.source.especialista_id:
            usernames.append(self.source.especialista.pessoa_fisica.cpf)
        title = 'Lembrete de tele-atendimento'
        message = 'Você possui um tele-atendimento agendado para {}.'.format(self.source.agendado_para.strftime('%d/%m/%Y as %H:%M'))
        url = f'/app/visualizaratendimento/{self.source.pk}/'
        for user in self.objects('slth.user').filter(username__in=usernames):
            0 and user.send_push_notification(title, message, url=url)
        
        url = self.absolute_url(url)
        text = '{} Para acessar, clique em {}.'.format(message, url)
        html = '{} Para acessar, clique em <a href="{}">{}</a>.'.format(message, url, url)
        if self.source.paciente.email:
            send_mail([self.source.paciente.email], title, text, html)
        if self.source.profissional.pessoa_fisica.email:
            send_mail([self.source.profissional.pessoa_fisica.email], title, text, html)
        if self.source.especialista_id and self.source.especialista.pessoa_fisica.email:
            send_mail([self.source.especialista.pessoa_fisica.email], title, text, html)
        return super().post()
    
    def check_permission(self):
        return self.request.user.is_superuser

class Atendimentos(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        modal = False
        icon = "laptop-file"
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return super().get().all().actions('visualizaratendimento', 'cadastraratendimento', 'delete')

    def check_permission(self):
        return self.check_role('a', 'g')
    

class VisualizarAtendimento(endpoints.ViewEndpoint[Atendimento]):
    class Meta:
        icon = 'eye'
        modal = False
        verbose_name = 'Acessar'

    def get(self):
        return (
            super().get()
        )

    def check_permission(self):
        return self.check_role('g', 'ps', 'o') or self.instance.paciente.cpf == self.request.user.username


class ProximosAtendimentosProfissionalSaude(endpoints.ListEndpoint[Atendimento]):
    class Meta:
        verbose_name= 'Próximos Atendimentos'

    def get(self):
        return super().get().proximos().fields('get_numero', 'tipo', 'paciente', 'assunto', 'get_agendado_para').actions('visualizaratendimento').lookup('ps', profissional__pessoa_fisica__cpf='username', especialista__pessoa_fisica__cpf='username')
    
    def check_permission(self):
        return self.check_role('ps', superuser=False)


class ProximosAtendimentosPaciente(endpoints.ListEndpoint[Atendimento]):
    class Meta:
        verbose_name= 'Próximos Atendimentos'

    def get(self):
        return super().get().proximos().fields('profissional', 'assunto', 'get_agendado_para').actions('visualizaratendimento').lookup('p', paciente__cpf='username')
    
    def check_permission(self):
        return self.check_role('p', superuser=False)

class AgendaAtendimentos(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        icon = 'calendar-days'
        verbose_name= 'Agenda de Atendimentos'
    
    def get(self):
        return (
            super().get().all().actions('cadastraratendimento', 'visualizaratendimento')
            .lookup('g', profissional__nucleo__gestores__cpf='username')
            .lookup('o', unidade__nucleo__operadores__cpf='username')
            .lookup('ps', profissional__pessoa_fisica__cpf='username', especialista__pessoa_fisica__cpf='username')
            .lookup('p', paciente__cpf='username')
            .calendar("agendado_para")
        )

    def check_permission(self):
        return self.request.user.is_authenticated

class MeusVinculos(endpoints.ListEndpoint[ProfissionalSaude]):
    
    class Meta:
        verbose_name= 'Meus Vínculos'
    
    def get(self):
        return super().get().filter(pessoa_fisica__cpf=self.request.user).fields('get_estabelecimento', 'especialidade').actions("alteraragendaprofissionalsaude")

    def check_permission(self):
        return self.check_role('ps', superuser=False)
    


class MinhaAgenda(endpoints.Endpoint):
    class Meta:
        icon = 'calendar-days'
        verbose_name = 'Minha Agenda'

    def get(self):
        return ProfissionalSaude.objects.filter(pessoa_fisica__cpf=self.request.user.username).first().get_agenda()
    
    def check_permission(self):
        return self.check_role('ps', superuser=False)


class ConsultarHorariosDisponiveis(endpoints.AddEndpoint[Atendimento]):
    class Meta:
        verbose_name = 'Consultar Horários Disponíveis'

    def get(self):
        profissional = ProfissionalSaude.objects.filter(pk=self.request.GET.get('profissional')).first()
        especialista = ProfissionalSaude.objects.filter(pk=self.request.GET.get('especialista')).first()
        is_teleconsulta = self.request.GET.get('tipo') == '1'
        return Atendimento.objects.agenda(profissional, especialista, is_teleconsulta)

    def check_permission(self):
        return True


class CadastrarAtendimento(endpoints.AddEndpoint[Atendimento]):
    class Meta:
        icon = 'plus'
        modal = False
        verbose_name = 'Cadastrar Atendimento'

    def get(self):
        return super().get().hidden('especialista')
    
    def getform(self, form):
        form = super().getform(form)
        form.fields['agendado_para'] = forms.SchedulerField(scheduler=Atendimento.objects.agenda())
        if self.check_role('ps'):
            form.fields['unidade'].pick = True
            form.fields['profissional'].pick = True
        return form
    
    def get_unidade_queryset(self, queryset, values):
        if self.check_role('o'):
            qs = queryset.none()
            for nucleo in Nucleo.objects.filter(operadores__cpf=self.request.user.username):
                qs = qs | nucleo.unidades.all()
        elif self.check_role('ps'):
            return queryset.filter(profissionalsaude__pessoa_fisica__cpf=self.request.user.username)
        else:
            qs = queryset.none()
        return qs
    
    def get_area_queryset(self, queryset, values):
        tipo = values.get('tipo')
        if tipo:
            if self.check_role('o'):
                return queryset
            elif self.check_role('ps'):
                if tipo.id == TipoAtendimento.TELECONSULTA:
                    return queryset.filter(especialidade__profissionalsaude__pessoa_fisica__cpf=self.request.user.username)
                else:
                    return queryset
        return queryset.none()
        
    def on_tipo_change(self, controller, values):
        tipo = values.get('tipo')
        controller.reload('area', 'profissional', 'especialista', 'agendado_para')
        if tipo and tipo.id == TipoAtendimento.TELE_INTERCONSULTA:
            controller.show('especialista')
        else:
            controller.hide('especialista')
    
    def on_area_change(self, controller, values):
        controller.reload('profissional', 'especialista', 'agendado_para')
        controller.set(profissional=None)

    def get_profissional_queryset(self, queryset, values):
        tipo = values.get('tipo')
        unidade = values.get('unidade')
        area = values.get('area')
        if unidade and area and tipo:
            queryset = queryset.filter(unidade=unidade)
            if tipo.id == TipoAtendimento.TELECONSULTA:
                queryset = queryset.filter(especialidade__area=area)
            if self.check_role('ps'):
                queryset = queryset.filter(pessoa_fisica__cpf=self.request.user.username)
            return queryset
        return queryset.none()
    
    def get_especialista_queryset(self, queryset, values):
        tipo = values.get('tipo')
        area = values.get('area')
        if tipo and area:
            if tipo.id == TipoAtendimento.TELE_INTERCONSULTA:
                queryset = queryset.filter(nucleo__isnull=False, especialidade__area=area)
            print(tipo, area, queryset)
            return queryset
        return queryset.none()
    
    def on_profissional_change(self, controller, values):
        controller.reload('agendado_para')
    
    def on_especialista_change(self, controller, values):
        controller.reload('agendado_para')

    def clean_agendado_para(self, cleaned_data):
        duracao = cleaned_data.get('duracao')
        agendado_para = cleaned_data.get('agendado_para')
        profissional = cleaned_data.get('profissional')
        especialista = cleaned_data.get('especialista')
        if not profissional.pode_realizar_atendimento(agendado_para, duracao):
            raise endpoints.ValidationError('O horário selecionado é incompatível com a duração informada.')
        if especialista and not especialista.pode_realizar_atendimento(agendado_para, duracao):
            raise endpoints.ValidationError('O horário selecionado é incompatível com a duração informada.')
        return agendado_para

    def check_permission(self):
        return self.check_role('o', 'ps')
    
    def post(self):
        return self.redirect('/api/visualizaratendimento/{}/'.format(self.instance.pk))


class CertificadosDigitais(endpoints.AdminEndpoint[CertificadoDigital]):
    def check_permission(self):
        return self.check_role('g')


class ProfissionaisSaudeEspecialidade(endpoints.InstanceEndpoint[Especialidade]):
    class Meta:
        icon = "stethoscope"
        verbose_name = 'Profissionais de Saúde'
    
    def get(self):
        return self.instance.get_profissonais_saude()
    
class ProfissionaisSaudeArea(endpoints.InstanceEndpoint[Area]):
    class Meta:
        icon = "stethoscope"
        verbose_name = 'Profissionais de Saúde'
    
    def get(self):
        return self.instance.get_profissonais_saude()


class AgendaNucleo(endpoints.InstanceEndpoint[Nucleo]):
    class Meta:
        icon = 'clock'
        verbose_name = 'Agenda de Horários'

    def get(self):
        return self.serializer().fields('nome', 'get_agenda')
    
    def check_permission(self):
        return True
    
class AgendaProfissionalSaude(endpoints.InstanceEndpoint[ProfissionalSaude]):
    class Meta:
        icon = 'calendar-days'
        verbose_name = 'Visualizar Agenda'
    
    def get(self):
        return self.serializer().fieldset(
            "Dados do Profissional",
            ("pessoa_fisica", ("nucleo", "especialidade")),
        ).fieldset('Agenda', ('get_agenda',))
    
    def check_permission(self):
        return True

class ConsultarAgenda(endpoints.Endpoint):
    class Meta:
        icon = 'clock'
        verbose_name = 'Consultar Agenda'

    def get(self):
        area = self.request.GET.get('area')
        if area:
            return Area.objects.get(pk=area).get_agenda()
        return Scheduler()
    
    def check_permission(self):
        return True


class AlterarAgendaProfissionalSaude(endpoints.InstanceEndpoint[ProfissionalSaude]):

    class Meta:
        icon = "calendar-plus"
        verbose_name = "Alterar Agenda"

    def get(self):
        return (
            self.formfactory()
            .display(
                "Dados do Profissional",
                (("pessoa_fisica", "especialidade"),),
            )
            .fields()
        )

    def getform(self, form):
        form.fields["horarios"] = forms.SchedulerField(
            scheduler=self.instance.get_agenda(readonly=False)
        )
        return form

    def post(self):
        for data_hora in self.cleaned_data["horarios"]["select"]:
            HorarioProfissionalSaude.objects.create(data_hora=data_hora, profissional_saude=self.instance)
        for data_hora in self.cleaned_data["horarios"]["deselect"]:
            HorarioProfissionalSaude.objects.filter(data_hora=data_hora, profissional_saude=self.instance).delete()
        return super().post()
    
    def check_permission(self):
        return self.check_role('g', 'o') or self.instance.pessoa_fisica.cpf == self.request.user.username


class DefinirHorarioProfissionalSaude(endpoints.InstanceEndpoint[ProfissionalSaude]):
    horarios = forms.SchedulerField(scheduler=Scheduler(weekly=True, chucks=3))

    class Meta:
        icon = "user-clock"
        verbose_name = "Definir Horários"

    def getform(self, form):
        form.fields['horarios'] = forms.SchedulerField(scheduler=self.instance.get_horarios_atendimento(False))
        return super().getform(form)

    def get(self):
        return (self.formfactory().fields('horarios'))
    
    def post(self):
        self.instance.atualizar_horarios_atendimento(self.cleaned_data['horarios']['select'], self.cleaned_data['horarios']['deselect'])
        return super().post()


class DefinirHorarioProfissionaisSaude(endpoints.Endpoint):
    horarios = forms.SchedulerField(scheduler=Scheduler(weekly=True, chucks=3))

    class Meta:
        icon = "user-clock"
        verbose_name = "Definir Horários de Atendimento"

    def get(self):
        return (self.formfactory().fields('horarios'))
    
    def post(self):
        for profissional_saude in ProfissionalSaude.objects.all():
            profissional_saude.atualizar_horarios_atendimento(self.cleaned_data['horarios']['select'], self.cleaned_data['horarios']['deselect'])
        return super().post()


class SalaEspera(endpoints.PublicEndpoint):
    class Meta:
        verbose_name = 'Sala de Espera'

    def get(self):
        atendimento = Atendimento.objects.get(token=self.request.GET.get('token'))
        if atendimento.numero_webconf:
            if self.request.user.is_authenticated:
                self.redirect('/api/salavirtual/{}/'.format(atendimento.pk))
            self.redirect('/api/salavirtual/{}/?token={}'.format(atendimento.pk, atendimento.token))
        return self.render(dict(atendimento=atendimento), autoreload=10)


class SalaVirtual(endpoints.InstanceEndpoint[Atendimento]):

    class Meta:
        icon = 'display'
        modal = False
        verbose_name = 'Sala Virtual'

    def get(self):
        # se a sala virtual ainda não foi criada
        if self.instance.numero_webconf is None and not RUNNING_TESTING:
            # criar sala virtual caso esteja sendo acessado pelo profissional responsável
            if self.instance.profissional.pessoa_fisica.cpf == self.request.user.username:
                self.instance.check_webconf()
            # redirecionar para a sala de espera
            else:
                self.redirect('/api/salaespera/?token={}'.format(self.instance.token))
        return (
            self.serializer().actions('anexararquivo')
            .endpoint('VideoChamada', 'videochamada', wrap=False)
            .queryset('Anexos', 'get_anexos_webconf')
            .endpoint('Condutas e Enaminhamentos', 'registrarecanminhamentoscondutas', wrap=False)
        )
    
    def check_permission(self):
        return (
            self.instance.finalizado_em is None
            and self.instance.is_termo_consentimento_assinado()
            and (
                self.check_role('ps')
                or self.instance.paciente.cpf == self.request.user.username
                or self.request.GET.get('token') == self.instance.token
            )
        )


class VideoChamada(endpoints.InstanceEndpoint[Atendimento]):
    def get(self):
        cpf = self.request.user.username if self.request.user.is_authenticated else self.instance.paciente.cpf
        return ZoomMeet(self.instance.numero_webconf, self.instance.senha_webconf, cpf)
    
    def check_permission(self):
        return (
            self.instance.finalizado_em is None
            and not RUNNING_TESTING
            and (
                self.request.GET.get('token') == self.instance.token
                or self.request.user.username == self.instance.paciente.cpf
                or self.request.user.username == self.instance.profissional.pessoa_fisica.cpf
                or self.instance.especialista and self.request.user.username == self.instance.especialista.pessoa_fisica.cpf
            )
        )


class RegistrarEcanminhamentosCondutas(endpoints.ChildEndpoint):

    class Meta:
        icon = 'file-signature'
        verbose_name = 'Registrar Enaminhamento'

    def get(self):
        responsavel = ProfissionalSaude.objects.get(
            pessoa_fisica__cpf=self.request.user.username
        )
        instance = EncaminhamentosCondutas.objects.filter(
            atendimento=self.source, responsavel=responsavel
        ).first()
        if instance is None:
            instance = EncaminhamentosCondutas(
                atendimento=self.source, responsavel=responsavel
            )
        return (
            self.formfactory(instance)
            .fieldset('Método SOAP', ('subjetivo', 'objetivo', 'avaliacao', 'plano'))
            .fieldset('Outras Informações', ('comentario', 'encaminhamento', 'conduta'))
        )
    
    def post(self):
        self.redirect(f'/api/visualizaratendimento/{self.source.id}/')

    def check_permission(self):
        return self.source.finalizado_em is None and self.check_role('ps') and self.source.is_termo_consentimento_assinado()


class AnexarArquivo(endpoints.ChildEndpoint):
    class Meta:
        icon = 'upload'
        verbose_name = 'Anexar Arquivo'

    def get(self):
        autor = PessoaFisica.objects.filter(cpf=self.request.user.username).first() or self.source.paciente
        instance = AnexoAtendimento(atendimento=self.source, autor=autor)
        return self.formfactory(instance).fields('nome', 'arquivo')
    
    def check_permission(self):
        return (
            self.source.finalizado_em is None
            and (
                self.request.GET.get('token') == self.source.token
                or self.request.user.username == self.source.paciente.cpf
                or self.request.user.username == self.source.profissional.pessoa_fisica.cpf
                or self.source.especialista and self.request.user.username == self.source.especialista.pessoa_fisica.cpf
            )
        )
    

class FinalizarAtendimento(endpoints.ChildEndpoint):

    class Meta:
        verbose_name = 'Finalizar Atendimento'

    def get(self):
        return self.formfactory(self.source).fields(finalizado_em=datetime.now())
    
    def check_permission(self):
        return self.source.finalizado_em is None and self.request.user.username == self.source.profissional.pessoa_fisica.cpf and self.source.encaminhamentoscondutas_set.filter(responsavel__pessoa_fisica__cpf=self.request.user.username).exists()

class FazerAlgo(endpoints.Endpoint):
    class Meta:
        modal = False

    x = forms.CharField(label='X')

    def get(self):
        return self.formfactory().fields('x').onsuccess(message='Fantástico :D', dispose=True)
    
class Estatistica(endpoints.PublicEndpoint):
    class Meta:
        icon = 'line-chart'
        verbose_name = 'Painel de Monitoramento'
    
    def get(self):
        return (
            Atendimento.objects
            .filters(
                'area', 'unidade__municipio', 'unidade', 'profissional', 'especialista'
            )
            .bi(
                ('get_total', 'get_total_profissioinais', 'get_total_pacientes'),
                ('get_total_por_tipo', 'get_total_por_area'),
                'get_total_por_mes',
                'get_total_por_area_e_unidade'
            )
        )
    
    def check_permission(self):
        return self.check_role('g', 'gm', 'gu')


from . import tasks
class FazerAlgumaCoisa(endpoints.Endpoint):
    total = forms.IntegerField(label='Total')

    class Meta:
        modal = False
    
    def post(self):
        return tasks.FazerAlgumaCoisa()

class Vidaas(endpoints.Endpoint):
    class Meta:
        verbose_name = 'Configurar Vidaas'

    def get(self):
        self.redirect('{}?code={}'.format(self.cache.get('vidaas_forward'), self.request.GET.get('code')))

    def _get(self):
        profissional_saude = ProfissionalSaude.objects.get(pessoa_fisica__cpf=self.request.user.username)
        code_verifier = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstwcM'
        authorization_code = self.request.GET.get('code')
        redirect_url = self.absolute_url('/app/vidaas/')
        redirect_url = 'push://http://viddas.com.br'
        if authorization_code:
            profissional_saude.configurar_vidaas(authorization_code, redirect_url, code_verifier)
            # profissional_saude.assinar_arquivo_imagem('/Users/breno/Downloads/file.jpeg')
            return Response('Configuração realizada com sucesso.', redirect='/api/dashboard/')
        else:
            login_hint = self.request.user.username
            if redirect_url.startswith('push://'):
                url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/authorizations?client_id={}&code_challenge={}&code_challenge_method=S256&response_type=code&scope=signature_session&login_hint={}&lifetime=900&redirect_uri={}'.format(
                    os.environ.get('VIDAAS_API_KEY'), code_verifier, login_hint, redirect_url
                )
                authorization_code = requests.get(url).text
                ok = profissional_saude.configurar_vidaas(authorization_code, redirect_url, code_verifier)
                if ok:
                    print('[OK]')
                    profissional_saude.assinar_arquivo_imagem('/Users/breno/Downloads/file.jpeg')
                self.redirect('/app/dashboard/')
            else:
                url = 'https://certificado.vidaas.com.br/v0/oauth/authorize?client_id={}&code_challenge={}&code_challenge_method=S256&response_type=code&scope=signature_session&login_hint={}&lifetime=900&redirect_uri={}'.format(
                    os.environ.get('VIDAAS_API_KEY'), code_verifier, login_hint, redirect_url
                )
                self.redirect(url)

    def check_permission(self):
        return self.check_role('ps')


class ConfigurarZoom(endpoints.Endpoint):
    class Meta:
        verbose_name = 'Configurar Zoom'

    def get(self):
        authorization_code = self.request.GET.get('code')
        print(authorization_code, 99999)
        redirect_url = self.absolute_url('/app/configurarzoom/')
        if authorization_code:
            profissional_saude = ProfissionalSaude.objects.get(pessoa_fisica__cpf=self.request.user.username)
            profissional_saude.configurar_zoom(authorization_code, redirect_url)
            return Response('Configuração realizada com sucesso.', redirect='/api/dashboard/')
        else:
            url = 'https://zoom.us/oauth/authorize?response_type=code&client_id={}&redirect_uri={}'.format(os.environ.get('ZOOM_API_KEY'), redirect_url)
            self.redirect(url)

    def check_permission(self):
        return self.check_role('ps') or ProfissionalSaude.objects.filter(peossoa_fisica__cpf=self.request.user.username, zoom_token__isnull=True).exists()


class ImprimirAtendimento(endpoints.InstanceEndpoint[Atendimento]):
    class Meta:
        modal = True
        verbose_name = 'Imprimir Atendimento'

    def get(self):
        self.render(dict(nome='X', qrcode=(printer.qrcode_base64('https://zoom.us/'))), pdf=True)

class ImprimirTermoConsentimento(endpoints.InstanceEndpoint[Atendimento]):
    class Meta:
        icon = 'print'
        modal = False
        verbose_name = 'Imprimir Termo de Consentimento'

    def get(self):
        self.render(dict(atendimento=self.instance), pdf=True)

    def check_permission(self):
        return self.check_role('ps', 'o')


class AnexarTermoConsentimento(endpoints.InstanceEndpoint[Atendimento]):
    imagem = forms.ImageField(label='Imagem', width=800)
    class Meta:
        icon = 'upload'
        modal = False
        verbose_name = 'Anexar Termo de Consentimento'

    def get(self):
        return self.formfactory().fields('imagem')

    def post(self):
        termo_consentimento = self.instance.get_termo_consentimento()
        if termo_consentimento:
            termo_consentimento.delete()
        imagem = printer.image_base64(self.request.FILES['imagem'].read())
        signature = printer.Signature(date=datetime.now(), validation_url='https://validar.iti.gov.br/')
        signature.add_signer('{} - {}'.format(self.instance.profissional.pessoa_fisica.nome, self.instance.profissional.get_registro_profissional()), None)
        autor = PessoaFisica.objects.filter(cpf=self.request.user.username).first()
        anexo = AnexoAtendimento(atendimento=self.instance, autor=autor, nome='Termo de Consentimento')
        content = printer.to_pdf(dict(imagem=imagem), 'termoconsentimento2.html', signature=signature)
        anexo.arquivo.save('{}.pdf'.format(uuid1().hex), ContentFile(content.getvalue()))
        anexo.save()
        self.redirect(f'/api/visualizaratendimento/{self.instance.pk}/')

    def check_permission(self):
        return self.check_role('ps', 'o')


class AssinarAnexo(endpoints.InstanceEndpoint[AnexoAtendimento]):
    class Meta:
        modal = False
        icon = 'signature'
        verbose_name = 'Assinar'

    def get(self):
        return self.formfactory().fields().info(MENSAGEM_ASSINATURA_DIGITAL)

    def post(self):
        if RUNNING_TESTING:
            self.redirect(f'/api/visualizaratendimento/{self.instance.atendimento_id}/')
        profissional_saude = ProfissionalSaude.objects.get(pessoa_fisica__cpf=self.request.user.username)
        cpf = '04770402414' or profissional_saude.pessoa_fisica.cpf.replace('.', '').replace('-', '')
        code_verifier = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstwcM'
        redirect_url = 'push://http://viddas.com.br'
        url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/authorizations?client_id={}&code_challenge={}&code_challenge_method=S256&response_type=code&scope=signature_session&login_hint={}&lifetime=900&redirect_uri={}'.format(os.environ.get('VIDAAS_API_KEY'), code_verifier, cpf, redirect_url)
        response = requests.get(url)
        print(url)
        print(response.status_code, response.text)
        authentication_code = response.text
        url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/authentications?{}'.format(authentication_code)
        print(url)
        authorization_code = None
        for i in range(0, 3):
            sleep(10)
            response = requests.get(url)
            print(response.status_code, response.text)
            if response.status_code == 200:
                data = response.json()
                authorization_code = response.json()['authorizationToken']
                break
        
        if authorization_code:
            url = 'https://certificado.vidaas.com.br/v0/oauth/token'
            client_id = os.environ.get('VIDAAS_API_KEY')
            client_secret = os.environ.get('VIDAAS_API_SEC')
            data = dict(grant_type='authorization_code', code=authorization_code, redirect_uri=redirect_url, code_verifier=code_verifier, client_id=client_id, client_secret=client_secret)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(url, headers=headers, data=data).json()
            access_token = response['access_token']
            print(access_token, 11111)
            caminho_arquivo = self.instance.arquivo.path
            if not self.instance.possui_assinatura(cpf):
                url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/signatures'
                filename = caminho_arquivo.split('/')[-1]
                filecontent = open(caminho_arquivo, 'r+b').read()
                base64_content = base64.b64encode(filecontent).decode()
                sha256 = hashlib.sha256()
                sha256.update(filecontent)
                hash=sha256.hexdigest()
                headers = {'Content-type': 'application/json', 'Authorization': 'Bearer {}'.format(access_token)}
                data = {"hashes": [{"id": filename, "alias": filename, "hash": hash, "hash_algorithm": "2.16.840.1.101.3.4.2.1", "signature_format": "CAdES_AD_RB", "base64_content": base64_content,}]}
                response = requests.post(url, json=data, headers=headers).json()
                file_content=base64.b64decode(response['signatures'][0]['file_base64_signed'].replace('\r\n', ''))
                open(caminho_arquivo, 'w+b').write(file_content)
                self.instance.checar_assinaturas()
            self.redirect(f'/api/visualizaratendimento/{self.instance.atendimento_id}/')
        else:
            raise endpoints.ValidationError('Não foi possível realizar a assinatura do documento. Tente outra vez!')

    def check_permission(self):
        return self.check_role('ps')


class AssinarAnexoQrCode(endpoints.InstanceEndpoint[AnexoAtendimento]):
    class Meta:
        modal = False
        icon = 'qrcode'
        verbose_name = 'Assinar'

    def get(self):
        if RUNNING_TESTING:
            self.redirect(f'/api/visualizaratendimento/{self.instance.pk}/')
        self.cache.set('vidaas_forward', self.request.path)
        profissional_saude = ProfissionalSaude.objects.get(pessoa_fisica__cpf=self.request.user.username)
        cpf = '04770402414' or profissional_saude.pessoa_fisica.cpf.replace('.', '').replace('-', '')
        code_verifier = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstwcM'
        redirect_url = self.absolute_url('/app/vidaas/')
        authorization_code = self.request.GET.get('code')
        if authorization_code is None:
            url = 'https://certificado.vidaas.com.br/v0/oauth/authorize?client_id={}&code_challenge={}&code_challenge_method=S256&response_type=code&scope=signature_session&login_hint={}&lifetime=900&redirect_uri={}'.format(os.environ.get('VIDAAS_API_KEY'), code_verifier, cpf, redirect_url)
            self.redirect(url)
        else:
            url = 'https://certificado.vidaas.com.br/v0/oauth/token'
            client_id = os.environ.get('VIDAAS_API_KEY')
            client_secret = os.environ.get('VIDAAS_API_SEC')
            data = dict(grant_type='authorization_code', code=authorization_code, redirect_uri=redirect_url, code_verifier=code_verifier, client_id=client_id, client_secret=client_secret)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(url, headers=headers, data=data).json()
            access_token = response['access_token']
            print(access_token, 11111)
            caminho_arquivo = self.instance.arquivo.path
            if not self.instance.possui_assinatura(cpf):
                url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/signatures'
                filename = caminho_arquivo.split('/')[-1]
                filecontent = open(caminho_arquivo, 'r+b').read()
                base64_content = base64.b64encode(filecontent).decode()
                sha256 = hashlib.sha256()
                sha256.update(filecontent)
                hash=sha256.hexdigest()
                headers = {'Content-type': 'application/json', 'Authorization': 'Bearer {}'.format(access_token)}
                data = {"hashes": [{"id": filename, "alias": filename, "hash": hash, "hash_algorithm": "2.16.840.1.101.3.4.2.1", "signature_format": "CAdES_AD_RB", "base64_content": base64_content,}]}
                response = requests.post(url, json=data, headers=headers).json()
                file_content=base64.b64decode(response['signatures'][0]['file_base64_signed'].replace('\r\n', ''))
                open(caminho_arquivo, 'w+b').write(file_content)
                self.instance.checar_assinaturas()
                self.redirect(f'/api/visualizaratendimento/{self.instance.atendimento_id}/')

    def check_permission(self):
        return self.check_role('ps')
    

class AssinarTermoConsentimento(endpoints.InstanceEndpoint[Atendimento]):
    tipo_assinatura = forms.ChoiceField(label='Tipo', choices=[['QrCode', 'QrCode'], ['Notificação', 'Notificação']], pick=True)
    class Meta:
        modal = False
        icon = 'signature'
        verbose_name = 'Assinar Termo de Consentimento'

    def get(self):
        return self.formfactory().image('/static/images/signature.png').fields('tipo_assinatura')

    def post(self):
        tipo_assinatura = self.cleaned_data['tipo_assinatura']
        anexo = self.instance.get_termo_consentimento()
        if anexo:
            if tipo_assinatura == 'QrCode':
                self.redirect(f'/api/assinaranexoqrcode/{anexo.id}/')
            else:
                self.redirect(f'/api/assinaranexo/{anexo.id}/')
        else:
            raise endpoints.ValidationError('O termo de consentimento ainda não foi enviado.')
        return super().post()
    
    def check_permission(self):
        return self.check_role('ps') and self.instance.get_termo_consentimento()


    
