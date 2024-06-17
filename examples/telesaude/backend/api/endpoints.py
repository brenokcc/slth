import os
from slth import endpoints
from slth.components import Scheduler, ZoomMeet, TemplateContent
from .models import *
from slth import forms
from .utils import buscar_endereco
from slth.tests import RUNNING_TESTING
from .mail import send_mail


class CIDs(endpoints.AdminEndpoint[CID]):
    def check_permission(self):
        return self.check_role('a')


class CIAPs(endpoints.AdminEndpoint[CIAP]):
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
            .fieldset("Dados Profissionais", (("registro_profissional", "especialidade", "registro_especialista"),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"),("residente", "perceptor"),),)
        )
    
    def get_nucleo_queryset(self, queryset, values):
        return queryset.lookup('g', gestores__cpf='username')
    
    def check_permission(self):
        return self.check_role('a', 'g')



class AssinarTermoConsentimento(endpoints.InstanceEndpoint[Atendimento]):
    aceito = forms.BooleanField(label='Concordo com o termo acima apresentado')
    class Meta:
        icon = 'signature'
        verbose_name = 'Assinar Termo de Consentimento'

    def get(self):
        return self.formfactory().fields('aceito').display(None, ('get_termo_consentimento',))
    
    def post(self):
        self.instance.assinar_termo(self.request.user)
        self.redirect(f'/api/salavirtual/{self.instance.pk}/')

    def check_permission(self):
        return True

class CadastrarProfissionalSaudeUnidade(endpoints.RelationEndpoint[ProfissionalSaude]):
    class Meta:
        icon = 'plus'
        verbose_name = 'Adicionar Profissional'
    def formfactory(self):
        return (
            super()
            .formfactory().fields(unidade=self.source.instance)
            .fieldset("Dados Gerais", ("unidade", "pessoa_fisica:cadastrarpessoafisica",))
            .fieldset(
                "Dados Profissionais", (("registro_profissional", "especialidade", "registro_especialista"),),
            )
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
        if entrypoint == 'menu' and self.check_role('o'):
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
        return self.check_role('g', 'ps') or self.instance.paciente.cpf == self.request.user.username


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
            .lookup('o', profissional__nucleo__operadores__cpf='username')
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
        return super().get().filter(pessoa_fisica__cpf=self.request.user).fields('get_estabelecimento', 'especialidade').actions("definirhorarioprofissionalsaude")

    def check_permission(self):
        return self.check_role('ps', superuser=False)
    


class MinhaAgenda(endpoints.Endpoint):
    class Meta:
        verbose_name = 'Minha Agenda'

    def get(self):
        return ProfissionalSaude.objects.filter(pessoa_fisica__cpf=self.request.user.username).first().get_agenda()
    
    def check_permission(self):
        return self.check_role('ps', superuser=False)



class CadastrarAtendimento(endpoints.AddEndpoint[Atendimento]):
    class Meta:
        icon = 'plus'
        modal = False
        verbose_name = 'Cadastrar Atendimento'

    def get(self):
        return (
            super().get().hidden('especialista', 'justificativa_horario_excepcional', 'agendado_para')
        )
    
    def get_unidade_queryset(self, queryset, values):
        qs = queryset.none()
        for nucleo in Nucleo.objects.filter(operadores__cpf=self.request.user.username):
            qs = qs | nucleo.unidades.all()
        return qs
    
    def on_tipo_change(self, controller, values):
        tipo = values.get('tipo')
        if tipo and tipo.id == TipoAtendimento.TELETERCONSULTA:
            controller.show('especialista')
        else:
            controller.hide('especialista')
    
    def on_horario_excepcional_change(self, controller, values):
        if values.get('horario_excepcional'):
            controller.show('justificativa_horario_excepcional', 'agendado_para')
        else:
            controller.hide('justificativa_horario_excepcional', 'agendado_para')

    def on_area_change(self, controller, values):
        controller.reload('profissional', 'especialista')

    def get_profissional_queryset(self, queryset, values):
        unidade = values.get('unidade')
        area = values.get('area')
        if unidade and area:
            return unidade.get_profissionais_telessaude(area)
        return queryset.none()
    
    def get_especialista_queryset(self, queryset, values):
        unidade = values.get('unidade')
        area = values.get('area')
        if unidade and area:
            return unidade.get_profissionais_telessaude(area)
        return queryset.none()
    
    def on_profissional_change(self, controller, values):
        controller.reload('horarios_profissional_saude')

    def on_especialista_change(self, controller, values):
        controller.reload('horarios_profissional_saude')

    def get_horarios_profissional_saude_queryset(self, queryset, values):
        profissional = values.get('profissional')
        especialista = values.get('especialista')
        if profissional:
            qs = queryset.filter(profissional_saude=profissional).disponiveis()
            if especialista:
                qs = qs.filter(data_hora__in=(
                    queryset.filter(profissional_saude=especialista).disponiveis().values_list('data_hora', flat=True)
                ))
            return qs.order_by('data_hora')
        return queryset.none()
    
    def check_permission(self):
        return self.check_role('o')


class CadastrarAtendimentoPS(endpoints.AddEndpoint[Atendimento]):
    class Meta:
        icon = 'plus'
        modal = False
        verbose_name = 'Cadastrar Teleatendimento'

    def getform(self, form):
        form.fields['unidade'].pick = True
        form.fields['agendado_para'] = forms.SchedulerField(label="Data/Hora", scheduler = ProfissionalSaude.objects.get(
            pessoa_fisica__cpf=self.request.user.username
        ).get_agenda(readonly=False, single_selection=True, available=False))
        return super().getform(form)

    def get(self):
        return (
            self
            .formfactory()
            .fieldset("Dados Gerais", ("unidade", "tipo", "area", "profissional"),)
            .fieldset("Detalhamento", ("paciente:cadastrarpessoafisica", "assunto", "duvida", ("cid", "ciap"),),)
            .fieldset("Agendamento", ("duracao", "agendado_para", "especialista", "horarios_especialista",),
            ).hidden('agendado_para', 'especialista', 'horarios_especialista')
        )
    
    def get_unidade_queryset(self, queryset, values):
        return queryset.filter(profissionalsaude__pessoa_fisica__cpf=self.request.user.username)
    
    def on_tipo_change(self, controller, values):
        tipo = values.get('tipo')
        controller.visible(tipo and tipo.id == TipoAtendimento.TELECONSULTA, 'agendado_para')
        controller.visible(tipo and tipo.id == TipoAtendimento.TELETERCONSULTA, 'especialista', 'horarios_especialista')
        controller.reload('area')
    
    def get_area_queryset(self, queryset, values):
        tipo = values.get('tipo')
        if tipo and tipo.id == TipoAtendimento.TELECONSULTA:
            queryset = queryset.filter(especialidade__profissionalsaude__pessoa_fisica__cpf=self.request.user.username)
        return queryset

    def get_profissional_queryset(self, queryset, values):
        return queryset.filter(pessoa_fisica__cpf=self.request.user.username)
    
    def get_especialista_queryset(self, queryset, values):
        area = values.get('area')
        if area:
            return queryset.filter(especialidade__area=area)
        return queryset.none()
    
    def on_area_change(self, controller, values):
        tipo = values.get('tipo')
        if tipo and tipo.id == TipoAtendimento.TELETERCONSULTA:
            controller.reload('especialista')
    
    def on_duracao_change(self, controller, values):
        controller.reload('horarios_profissional_saude')

    def on_especialista_change(self, controller, values):
        controller.reload('horarios_especialista')

    def get_horarios_especialista_queryset(self, queryset, values):
        especialista = values.get('especialista')
        if especialista:
            return queryset.filter(profissional_saude=especialista).disponiveis().order_by('data_hora')
        return queryset.none()
    
    def check_permission(self):
        return self.check_role('ps') and ProfissionalSaude.objects.filter(pessoa_fisica__cpf=self.request.user.username, unidade__isnull=False)


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
        icon = 'clock'
        verbose_name = 'Visualizar Horário'
    
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


class DefinirHorarioProfissionalSaude(endpoints.InstanceEndpoint[ProfissionalSaude]):

    class Meta:
        icon = "user-clock"
        verbose_name = "Definir Horário"

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


class SalaVirtual(endpoints.InstanceEndpoint[Atendimento]):

    class Meta:
        icon = 'display'
        modal = False
        verbose_name = 'Sala Virtual'

    def get(self):
        if self.instance.is_termo_assinado_por(self.request.user):
            if not RUNNING_TESTING:
                self.instance.check_webconf()
            return (
                self.serializer().actions('anexararquivo')
                .endpoint('VideoChamada', 'videochamada', wrap=False)
                .queryset('Anexos', 'get_anexos_webconf')
                .endpoint('Condutas e Enaminhamentos', 'registrarecanminhamentoscondutas', wrap=False)
            )
        else:
            self.redirect(f'/api/assinartermoconsentimento/{self.instance.pk}/')
    
    def check_permission(self):
        return self.instance.finalizado_em is None and (self.check_role('ps') or self.instance.paciente.cpf == self.request.user.username)

class RegistrarEcanminhamentosCondutas(endpoints.ChildEndpoint):

    class Meta:
        icon = 'file-signature'
        verbose_name = 'Registrar Condutas e Enaminhamentos'

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
        return self.source.finalizado_em is None and self.check_role('ps')


class VideoChamada(endpoints.InstanceEndpoint[Atendimento]):
    def get(self):
        return ZoomMeet(self.instance.numero_webconf, self.instance.senha_webconf, self.request.user.username)
    
    def check_permission(self):
        return self.request.user.is_superuser or self.request.user.username in (
            self.instance.profissional.pessoa_fisica.cpf, self.instance.especialista.pessoa_fisica.cpf if self.instance.especialista_id else '', self.instance.paciente.cpf
        ) and not RUNNING_TESTING

class AnexarArquivo(endpoints.ChildEndpoint):
    class Meta:
        icon = 'upload'
        verbose_name = 'Anexar Arquivo'

    def get(self):
        autor = PessoaFisica.objects.filter(cpf=self.request.user.username).first() or self.source.especialista.pessoa_fisica
        instance = AnexoAtendimento(atendimento=self.source, autor=autor)
        return self.formfactory(instance).fields('nome', 'arquivo')
    
    def check_permission(self):
        return self.source.finalizado_em is None and self.check_role('p', 'ps')
    

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
