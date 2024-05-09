from slth import endpoints
from slth.components import Scheduler
from .models import *
from slth import forms


class CategoriasProfissional(endpoints.AdminEndpoint[CategoriaProfissional]):
    pass


class CIDs(endpoints.AdminEndpoint[CID]):
    pass


class CIAPs(endpoints.AdminEndpoint[CIAP]):
    pass


class TiposEnfoqueResposta(endpoints.AdminEndpoint[TipoEnfoqueResposta]):
    pass


class AreasTematicas(endpoints.AdminEndpoint[AreaTematica]):
    pass


class TiposSolicitacao(endpoints.AdminEndpoint[TipoSolicitacao]):
    pass


class UnidadesFederativas(endpoints.AdminEndpoint[UnidadeFederativa]):
    pass


class NiveisFormacao(endpoints.AdminEndpoint[NivelFormacao]):
    pass


class Sexos(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipios(endpoints.AdminEndpoint[Municipio]):
    pass


class EstabelecimentosSaude(endpoints.AdminEndpoint[EstabelecimentoSaude]):
    pass


class Especialidades(endpoints.AdminEndpoint[Especialidade]):
    pass


class Usuarios(endpoints.AdminEndpoint[Usuario]):
    pass


class AnexosUsuario(endpoints.AdminEndpoint[AnexoUsuario]):
    pass


class ProfissionaisSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    pass


class Solicitacoes(endpoints.AdminEndpoint[Solicitacao]):
    pass


class AnexosSolicitacao(endpoints.AdminEndpoint[AnexoSolicitacao]):
    pass


class StatusSolicitacao(endpoints.AdminEndpoint[StatusSolicitacao]):
    pass


class CertificadosDigitais(endpoints.AdminEndpoint[CertificadoDigital]):
    pass


class ConsultarAgenda(endpoints.Endpoint):
    def get(self):
        return Scheduler()


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
            scheduler=self.instance.get_horarios(readonly=False)
        )
        return form

    def post(self):
        self.instance.horarioprofissionalsaude_set.all().delete()
        for data_hora in self.cleaned_data["horarios"]:
            HorarioProfissionalSaude.objects.create(
                data_hora=data_hora, profissional_saude=self.instance
            )
        return super().post()
