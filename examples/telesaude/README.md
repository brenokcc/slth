# Telesaúde

## Migração

```
python manage.py dumpdata auth.user auth.group comum.perfil

python manage.py dumpdata auth.user comum.CategoriaProfissional comum.CID comum.CIAP comum.TipoEnfoqueResposta comum.AreaTematica comum.TipoSolicitacao comum.UnidadeFederativa comum.NivelFormacao comum.Sexo comum.Municipio comum.EstabelecimentoSaude comum.Especialidade comum.Usuario comum.AnexoUsuario comum.ProfissionalSaude comum.HistoricoAlteracaoProfissional comum.ProfissionalVinculo comum.Solicitacao comum.AnexoSolicitacao comum.StatusSolicitacao comum.FluxoSolicitacao comum.AvaliacaoSolicitacao comum.ProfissionalSaudeRegulador comum.ProfissionalSaudeEspecialista comum.ProfissionalSaudeGestorMunicipio comum.MotivoEncerramentoConferencia comum.CertificadoDigital EncaminhamentosCondutas > dados.json

```
