from slth import endpoints
from slth.components import Scheduler, ZoomMeet
from .models import *
from slth import forms



class CIDs(endpoints.AdminEndpoint[CID]):
    def check_permission(self):
        return self.check_role('g')


class CIAPs(endpoints.AdminEndpoint[CIAP]):
    def check_permission(self):
        return self.check_role('g')


class Areas(endpoints.AdminEndpoint[Area]):
    def check_permission(self):
        return self.check_role('g')


class TiposAtendimento(endpoints.AdminEndpoint[TipoAtendimento]):
    pass


class UnidadesFederativas(endpoints.AdminEndpoint[Estado]):
    def check_permission(self):
        return self.check_role('g')


class Sexos(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipios(endpoints.AdminEndpoint[Municipio]):
    def check_permission(self):
        return self.check_role('g')

class UnidadesOrganizacionais(endpoints.AdminEndpoint[UnidadeOrganizacional]):
    def check_permission(self):
        return self.check_role('g')

class Unidades(endpoints.AdminEndpoint[Unidade]):
    def check_permission(self):
        return self.check_role('g')


class Especialidades(endpoints.AdminEndpoint[Especialidade]):
    def check_permission(self):
        return self.check_role('g')


class PessoasFisicas(endpoints.AdminEndpoint[PessoaFisica]):
    def get(self):
        return super().get().actions(add='cadastrarpessoafisica')
    def check_permission(self):
        return self.check_role('g')


class CadastrarPessoaFisica(endpoints.AddEndpoint[PessoaFisica]):
    def check_permission(self):
        return self.check_role('g', 'o')


class ProfissionaisSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    def check_permission(self):
        return self.check_role('g', 'o')


class Atendimentos(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        modal = False
        icon = "laptop-file"
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return super().get().all().actions('visualizaratendimento', 'cadastraratendimento')

    def check_permission(self):
        return self.check_role('g', 'o')
    

class VisualizarAtendimento(endpoints.ViewEndpoint[Atendimento]):
    class Meta:
        modal = False
        verbose_name = 'Acessar '

    def get(self):
        return (
            super().get()
        )

    def check_permission(self):
        return self.check_role('g', 'ps') or self.instance.paciente.cpf == self.request.user.username

    

class MeusAtendimentos(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        verbose_name= 'Meus Atendimentos'
    
    def get(self):
        return (
            super().get().all().actions('visualizaratendimento')
            .lookup('ps', profissional__pessoa_fisica__cpf='username')
            #.lookup('ps', especialista__pessoa_fisica__cpf='username')
            .lookup('pf', paciente__cpf='username')
        )

    def check_permission(self):
        return self.request.user.is_authenticated and self.get().apply_lookups(self.request.user).exists()

class MeusLocaisAtendimento(endpoints.ListEndpoint[ProfissionalSaude]):
    
    class Meta:
        verbose_name= 'Vínculos'
    
    def get(self):
        return super().get().filter(pessoa_fisica__cpf=self.request.user).fields('uo', 'especialidade').actions("definirhorarioprofissionalsaude")

    def check_permission(self):
        return self.check_role('ps')


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
        print(7777)
        return queryset
    
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
        controller.reload('profissional')

    def get_profissional_queryset(self, queryset, values):
        area = values.get('area')
        if area:
            return queryset.filter(especialidade__area=area)
        return queryset.none()
    
    def on_profissional_change(self, controller, values):
        controller.reload('horario_profissional_saude')

    def get_horario_profissional_saude_queryset(self, queryset, values):
        profissional = values.get('profissional')
        if profissional:
            return queryset.filter(profissional_saude=profissional)
        return queryset.none()
    
    def check_permission(self):
        return self.check_role('g', 'o')



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


class EquipeUnidade(endpoints.InstanceEndpoint[Unidade]):
    class Meta:
        icon = 'people-line'
        verbose_name = 'Equipe de Unidade de Saúde'

    def get(self):
        return (
            self.serializer()
            .queryset("Gestores", "gestores")
            .queryset("Operadores", "operadores")
            .queryset("Profissionais", "get_profissionais_saude")
        )
    
    def check_permission(self):
        return True

class AgendaUnidade(endpoints.InstanceEndpoint[Unidade]):
    class Meta:
        icon = 'clock'
        verbose_name = 'Agenda de Unidade de Saúde'

    def get(self):
        return self.serializer().fields('nome', 'get_agenda')
    
    def check_permission(self):
        return True
    
class AgendaProfissionalSaude(endpoints.InstanceEndpoint[ProfissionalSaude]):
    class Meta:
        icon = 'clock'
        verbose_name = 'Agenda de Profissional de Saúde'
    
    def get(self):
        return self.serializer().fieldset(
            "Dados do Profissional",
            ("pessoa_fisica", ("uo", "especialidade")),
        ).fieldset('Agenda', ('get_agenda',))
    
    def check_permission(self):
        return True
    

class AgendaArea(endpoints.InstanceEndpoint[Area]):
    class Meta:
        icon = 'clock'
        verbose_name = 'Agenda da Área'
    
    def get(self):
        return self.serializer().fields(
            "nome"
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
                ("pessoa_fisica", ("uo", "especialidade")),
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
        self.instance.check_webconf()
        return (
            self.serializer().actions('anexararquivo')
            .endpoint('VideoChamada', 'videochamada', wrap=False)
            .queryset('Anexos', 'get_anexos_webconf')
            .endpoint('Condutas e Enaminhamentos', 'registrarecanminhamentoscondutas', wrap=False)
        )
    
    def check_permission(self):
        return self.check_role('ps') or self.instance.paciente.cpf == self.request.user.username

class RegistrarEcanminhamentosCondutas(endpoints.ChildEndpoint):

    class Meta:
        icon = 'file-signature'
        verbose_name = 'Registrar Condutas e Enaminhamentos'

    def get(self):
        instance = EncaminhamentosCondutas.objects.filter(
            atendimento=self.source, responsavel=self.source.especialista
        ).first()
        if instance is None:
            instance = EncaminhamentosCondutas(
                atendimento=self.source,
                responsavel=ProfissionalSaude.objects.get(
                    pessoa_fisica__cpf=self.request.user.username
                )
            )
        return (
            self.formfactory(instance)
            .fieldset('Método SOAP', ('subjetivo', 'objetivo', 'avaliacao', 'plano'))
            .fieldset('Outras Informações', ('comentario', 'encaminhamento', 'conduta'))
        )
    
    def check_permission(self):
        return self.check_role('ps')


class VideoChamada(endpoints.InstanceEndpoint[Atendimento]):
    def get(self):
        return ZoomMeet(self.instance.numero_webconf, self.instance.senha_webconf, self.request.user.username)
    
    def check_permission(self):
        return self.request.user.is_superuser or self.request.user.username in (
            self.instance.profissional.pessoa_fisica.cpf, self.instance.especialista.pessoa_fisica.cpf if self.instance.especialista_id else '', self.instance.paciente.cpf
        )

class AnexarArquivo(endpoints.ChildEndpoint):
    class Meta:
        icon = 'upload'
        verbose_name = 'Anexar Arquivo'

    def get(self):
        autor = PessoaFisica.objects.filter(cpf=self.request.user.username).first() or self.source.especialista.pessoa_fisica
        instance = AnexoAtendimento(atendimento=self.source, autor=autor)
        return self.formfactory(instance).fields('arquivo')
    

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
                'area', 'uo__municipio', 'uo', 'profissional', 'especialista', ''
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

