from slth import endpoints
from slth.components import Scheduler, WebConf
from .models import *
from slth import forms



class CIDs(endpoints.AdminEndpoint[CID]):
    def check_permission(self):
        return self.check_role('ge')


class CIAPs(endpoints.AdminEndpoint[CIAP]):
    def check_permission(self):
        return self.check_role('ge')


class Areass(endpoints.AdminEndpoint[Area]):
    def check_permission(self):
        return self.check_role('ge')


class TiposAtendimento(endpoints.AdminEndpoint[TipoAtendimento]):
    pass


class UnidadesFederativas(endpoints.AdminEndpoint[Estado]):
    def check_permission(self):
        return self.check_role('ge')


class Sexos(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipios(endpoints.AdminEndpoint[Municipio]):
    def check_permission(self):
        return self.check_role('ge')


class EstabelecimentosSaude(endpoints.AdminEndpoint[Unidade]):
    def check_permission(self):
        return self.check_role('ge')


class Especialidades(endpoints.AdminEndpoint[Especialidade]):
    def check_permission(self):
        return self.check_role('ge')


class PessoaFisicas(endpoints.AdminEndpoint[PessoaFisica]):
    def check_permission(self):
        return self.check_role('ge')

class ProfissionaisSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    def check_permission(self):
        return self.check_role('ge')


class Atendimentos(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        modal = False
        icon = "laptop-file"
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return super().get().all().actions('visualizaratendimento', 'cadastraratendimento', 'delete')

    def check_permission(self):
        return self.check_role('ge')
    

class VisualizarAtendimento(endpoints.ViewEndpoint[Atendimento]):
    class Meta:
        modal = False
        verbose_name = 'Acessar '

    def get(self):
        return (
            super().get()
        )

    def check_permission(self):
        return self.check_role('ge', 'ps') or self.instance.paciente.cpf == self.request.user.username

    

class MinhasTeleconsultas(endpoints.ListEndpoint[Atendimento]):
    
    class Meta:
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return (
            super().get().all().actions('visualizaratendimento')
            .lookup('ps', profissional__pessoafisica__cpf='username')
            #.lookup('ps', especialista__pessoafisica__cpf='username')
            .lookup('pf', paciente__cpf='username')
        )

    def check_permission(self):
        return self.request.user.is_authenticated and not self.check_role('ge')

class MeusLocaisAtendimento(endpoints.ListEndpoint[ProfissionalSaude]):
    
    class Meta:
        verbose_name= 'Vínculos'
    
    def get(self):
        return super().get().filter(pessoafisica__cpf=self.request.user).fields('estabelecimento', 'especialidade').actions("definirhorarioprofissionalsaude")

    def check_permission(self):
        return self.check_role('ps')


class CadastrarAtendimento(endpoints.AddEndpoint[Atendimento]):
    class Meta:
        verbose_name = 'Cadastrar Atendimento'

    def get(self):
        return (
            super().get().hidden('especialista', 'justificativa_horario_excepcional', 'agendado_para')
        )
    
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
        return self.check_role('ge')



class CertificadosDigitais(endpoints.AdminEndpoint[CertificadoDigital]):
    def check_permission(self):
        return self.check_role('ge')


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
            ("pessoafisica", ("estabelecimento", "especialidade")),
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
                ("pessoafisica", ("estabelecimento", "especialidade")),
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
        return self.check_role('ge') or self.instance.pessoafisica.cpf == self.request.user.username


class SalaVirtual(endpoints.InstanceEndpoint[Atendimento]):

    class Meta:
        icon = 'display'
        modal = False
        verbose_name = 'Sala Virtual'

    def get(self):
        return (
            self.serializer().actions('anexararquivo')
            .endpoint('VideoChamada', 'videochamada', wrap=False)
            .queryset('Anexos', 'get_anexos_webconf')
            .endpoint('Condutas e Enaminhamentos', 'registrarcondutasecanminhamentos', wrap=False)
        )
    
    def check_permission(self):
        return self.check_role('ps') or self.instance.paciente.cpf == self.request.user.username

class RegistrarCondutasEcanminhamentos(endpoints.ChildEndpoint):

    class Meta:
        verbose_name = 'Registrar Condutas e Enaminhamentos'

    def get(self):
        instance = EncaminhamentosCondutas.objects.filter(
            atendimento=self.source, responsavel=self.source.especialista
        ).first()
        if instance is None:
            instance = EncaminhamentosCondutas(
                atendimento=self.source, responsavel=self.source.especialista
            )
        return self.formfactory(instance).fields('subjetivo', 'objetivo', 'avaliacao', 'plano')


class VideoChamada(endpoints.InstanceEndpoint[Atendimento]):
    def get(self):
        caller = self.request.user.username
        if self.request.user.username == self.instance.profissional.pessoafisica.cpf:
            receiver = self.instance.paciente.cpf
        else:
            receiver = self.instance.profissional.pessoafisica.cpf
        print(self.request.user.username, caller, receiver, 9999)
        return WebConf(caller, receiver)
    
    def check_permission(self):
        return self.request.user.username in (
            self.instance.profissional.pessoafisica.cpf, self.instance.especialista.pessoafisica.cpf if self.instance.especialista_id else '', self.instance.paciente.cpf
        )

class AnexarArquivo(endpoints.ChildEndpoint):
    class Meta:
        icon = 'upload'
        verbose_name = 'Anexar Arquivo'

    def get(self):
        autor = PessoaFisica.objects.filter(cpf=self.request.user.username).first() or self.source.especialista.pessoafisica
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
                'area', 'estabelecimento__municipio', 'estabelecimento', 'profissional', 'especialista', ''
            )
            .bi(
                ('get_total', 'get_total_profissioinais', 'get_total_pacientes'),
                ('get_total_por_tipo', 'get_total_por_area'),
                'get_total_por_mes',
                'get_total_por_area_e_unidade'
            )
        )
    
    def check_permission(self):
        return self.check_role('ge', 'gm', 'gu')

