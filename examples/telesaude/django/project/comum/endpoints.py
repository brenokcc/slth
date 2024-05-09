from slth import endpoints
from .models import *


class CategoriaProfissional(endpoints.AdminEndpoint[CategoriaProfissional]):
    pass


class CID(endpoints.AdminEndpoint[CID]):
    pass


class CIAP(endpoints.AdminEndpoint[CIAP]):
    pass


class TipoEnfoqueResposta(endpoints.AdminEndpoint[TipoEnfoqueResposta]):
    pass


class AreaTematica(endpoints.AdminEndpoint[AreaTematica]):
    pass


class TipoSolicitacao(endpoints.AdminEndpoint[TipoSolicitacao]):
    pass


class UnidadeFederativa(endpoints.AdminEndpoint[UnidadeFederativa]):
    pass


class NivelFormacao(endpoints.AdminEndpoint[NivelFormacao]):
    pass


class Sexo(endpoints.AdminEndpoint[Sexo]):
    pass


class Municipio(endpoints.AdminEndpoint[Municipio]):
    pass


class EstabelecimentoSaude(endpoints.AdminEndpoint[EstabelecimentoSaude]):
    pass


class Especialidade(endpoints.AdminEndpoint[Especialidade]):
    pass


class Usuario(endpoints.AdminEndpoint[Usuario]):
    pass


class AnexoUsuario(endpoints.AdminEndpoint[AnexoUsuario]):
    pass


class ProfissionalSaude(endpoints.AdminEndpoint[ProfissionalSaude]):
    pass


class HistoricoAlteracaoProfissional(
    endpoints.AdminEndpoint[HistoricoAlteracaoProfissional]
):
    pass


class ProfissionalVinculo(endpoints.AdminEndpoint[ProfissionalVinculo]):
    pass


class Solicitacao(endpoints.AdminEndpoint[Solicitacao]):
    pass


class AnexoSolicitacao(endpoints.AdminEndpoint[AnexoSolicitacao]):
    pass


class StatusSolicitacao(endpoints.AdminEndpoint[StatusSolicitacao]):
    pass


class FluxoSolicitacao(endpoints.AdminEndpoint[FluxoSolicitacao]):
    pass


class AvaliacaoSolicitacao(endpoints.AdminEndpoint[AvaliacaoSolicitacao]):
    pass


class ProfissionalSaudeRegulador(endpoints.AdminEndpoint[ProfissionalSaudeRegulador]):
    pass


class ProfissionalSaudeEspecialista(
    endpoints.AdminEndpoint[ProfissionalSaudeEspecialista]
):
    pass


class MotivoEncerramentoConferencia(
    endpoints.AdminEndpoint[MotivoEncerramentoConferencia]
):
    pass


class CertificadoDigital(endpoints.AdminEndpoint[CertificadoDigital]):
    pass
