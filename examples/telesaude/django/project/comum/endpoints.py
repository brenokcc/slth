from slth import endpoints
from slth.components import Scheduler
from .models import *
from slth import forms


class CategoriasProfissional(endpoints.AdminEndpoint[CategoriaProfissional]):
    pass


class CIDs(endpoints.AdminEndpoint[CID]):
    def check_permission(self):
        return self.check_role('ge')


class CIAPs(endpoints.AdminEndpoint[CIAP]):
    def check_permission(self):
        return self.check_role('ge')


class TiposEnfoqueResposta(endpoints.AdminEndpoint[TipoEnfoqueResposta]):
    pass


class AreasTematicas(endpoints.AdminEndpoint[AreaTematica]):
    def check_permission(self):
        return self.check_role('ge')


class TiposSolicitacao(endpoints.AdminEndpoint[TipoSolicitacao]):
    pass


class UnidadesFederativas(endpoints.AdminEndpoint[UnidadeFederativa]):
    def check_permission(self):
        return self.check_role('ge')


class NiveisFormacao(endpoints.AdminEndpoint[NivelFormacao]):
    pass


class Sexos(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipios(endpoints.AdminEndpoint[Municipio]):
    def check_permission(self):
        return self.check_role('ge')


class EstabelecimentosSaude(endpoints.AdminEndpoint[EstabelecimentoSaude]):
    def check_permission(self):
        return self.check_role('ge')


class Especialidades(endpoints.AdminEndpoint[Especialidade]):
    def check_permission(self):
        return self.check_role('ge')


class Usuarios(endpoints.AdminEndpoint[Usuario]):
    def check_permission(self):
        return self.check_role('ge')

class ProfissionaisSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    def check_permission(self):
        return self.check_role('ge')


class Solicitacoes(endpoints.ListEndpoint[Solicitacao]):
    
    class Meta:
        modal = False
        icon = "laptop-file"
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return super().get().all().actions('visualizarsolititacao', 'cadastrarsolicitacao')

    def check_permission(self):
        return self.check_role('ge')
    

class VisualizarSolititacao(endpoints.ViewEndpoint[Solicitacao]):
    class Meta:
        modal = False
        verbose_name = 'Acessar '

    def get(self):
        return (
            super().get()
        )

    def check_permission(self):
        return self.check_role('ge', 'ps')

    

class MinhasTeleconsultas(endpoints.ListEndpoint[Solicitacao]):
    
    class Meta:
        verbose_name= 'Teleconsultas'
    
    def get(self):
        return (
            super().get().all().actions('visualizarsolititacao')
            .lookup('ps', solicitante__usuario__cpf='username')
            .lookup('ps', especialista__usuario__cpf='username')
        )

    def check_permission(self):
        return self.request.user.is_authenticated and not self.check_role('ge')

class MeusLocaisAtendimento(endpoints.ListEndpoint[ProfissionalSaude]):
    
    class Meta:
        verbose_name= 'Vínculos'
    
    def get(self):
        return super().get().filter(usuario__cpf=self.request.user).fields('estabelecimento', 'especialidade').actions("definirhorarioprofissionalsaude")

    def check_permission(self):
        return self.request.user.is_authenticated and not self.check_role('ge')


class CadastrarSolicitacao(endpoints.AddEndpoint[Solicitacao]):
    class Meta:
        verbose_name = 'Cadastrar Atendimento'

    def get(self):
        return (
            super().get().hidden('especialista', 'justificativa_horario_excepcional', 'agendado_para')
        )
    
    def on_tipo_solicitacao_change(self, controller, values):
        tipo_solicitacao = values.get('tipo_solicitacao')
        if tipo_solicitacao and tipo_solicitacao.id == TipoSolicitacao.TELETERCONSULTA:
            controller.show('especialista')
        else:
            controller.hide('especialista')
    
    def on_horario_excepcional_change(self, controller, values):
        if values.get('horario_excepcional'):
            controller.show('justificativa_horario_excepcional', 'agendado_para')
        else:
            controller.hide('justificativa_horario_excepcional', 'agendado_para')

    def get_solicitante_queryset(self, queryset, values):
        area_tematica = values.get('area_tematica')
        if area_tematica:
            return queryset.filter(especialidade__area_tematica=area_tematica)
        return queryset
    
    def get_horario_profissional_saude_queryset(self, queryset, values):
        solicitante = values.get('solicitante')
        if solicitante:
            return queryset.filter(profissional_saude=solicitante)
        return queryset.none()
    
    def check_permission(self):
        return self.check_role('ge')


class StatusSolicitacao(endpoints.AdminEndpoint[StatusSolicitacao]):
    pass


class CertificadosDigitais(endpoints.AdminEndpoint[CertificadoDigital]):
    def check_permission(self):
        return self.check_role('ge')


class ProfissionaisSaudeEspecialidade(endpoints.InstanceEndpoint[Especialidade]):
    class Meta:
        icon = "stethoscope"
        verbose_name = 'Profissionais de Saúde'
    
    def get(self):
        return self.instance.get_profissonais_saude()
    
class ProfissionaisSaudeAreaTematica(endpoints.InstanceEndpoint[AreaTematica]):
    class Meta:
        icon = "stethoscope"
        verbose_name = 'Profissionais de Saúde'
    
    def get(self):
        return self.instance.get_profissonais_saude()


class EquipeEstabelecimentoSaude(endpoints.InstanceEndpoint[EstabelecimentoSaude]):
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

class AgendaEstabelecimentoSaude(endpoints.InstanceEndpoint[EstabelecimentoSaude]):
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
            ("usuario", ("estabelecimento", "especialidade")),
        ).fieldset('Agenda', ('get_agenda',))
    
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
                ("usuario", ("estabelecimento", "especialidade")),
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
        return self.check_role('ge') or self.instance.usuario.cpf == self.request.user.username


class SalaVirtual(endpoints.InstanceEndpoint[Solicitacao]):

    class Meta:
        icon = 'display'
        modal = False
        verbose_name = 'Sala Virtual'

    def get(self):
        return (
            self.serializer().actions('anexararquivo')
            .field('get_webconf')
            .queryset('Anexos', 'get_anexos_webconf')
            .endpoint('Condutas e Enaminhamentos', 'registrarcondutasecanminhamentos', wrap=False)
        )
    
    def check_permission(self):
        return self.check_role('ps')

class RegistrarCondutasEcanminhamentos(endpoints.ChildEndpoint):

    class Meta:
        verbose_name = 'Registrar Condutas e Enaminhamentos'

    def get(self):
        instance = EncaminhamentosCondutas.objects.filter(
            solicitacao=self.source, responsavel=self.source.especialista
        ).first()
        if instance is None:
            instance = EncaminhamentosCondutas(
                solicitacao=self.source, responsavel=self.source.especialista
            )
        return self.formfactory(instance).fields('subjetivo', 'objetivo', 'avaliacao', 'plano')


class AnexarArquivo(endpoints.ChildEndpoint):
    class Meta:
        icon = 'upload'
        verbose_name = 'Anexar Arquivo'

    def get(self):
        autor = Usuario.objects.filter(cpf=self.request.user.username).first() or self.source.especialista.usuario
        instance = AnexoSolicitacao(solicitacao=self.source, autor=autor)
        return self.formfactory(instance).fields('arquivo')