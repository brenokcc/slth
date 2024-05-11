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


class Solicitacoes(endpoints.AdminEndpoint[Solicitacao]):
    def check_permission(self):
        return self.check_role('ge')

class StatusSolicitacao(endpoints.AdminEndpoint[StatusSolicitacao]):
    pass


class CertificadosDigitais(endpoints.AdminEndpoint[CertificadoDigital]):
    def check_permission(self):
        return self.check_role('ge')


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
        self.instance.horarioprofissionalsaude_set.all().delete()
        for data_hora in self.cleaned_data["horarios"]:
            HorarioProfissionalSaude.objects.create(
                data_hora=data_hora, profissional_saude=self.instance
            )
        return super().post()
    
    def check_permission(self):
        return self.check_role('ge')


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