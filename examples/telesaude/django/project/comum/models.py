import binascii

from slth.factory import FormFactory
from slth.serializer import Serializer
from . import signer
from random import randint
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from django.core.signing import Signer
from slth.db import models, meta, role
from slth.models import User
from slth.components import Scheduler, FileLink, WebConf, Image, Map, Text, Badge


class CategoriaProfissional(models.Model):
    codigo_familia_cbo = models.CharField(
        verbose_name="Código", max_length=4, unique=True
    )
    nome = models.CharField(max_length=150)

    class Meta:
        verbose_name = "Categoria Profissional"
        verbose_name_plural = "Categorias Profissionais"

    def __str__(self):
        return "%s - %s" % (self.codigo_familia_cbo, self.nome)


class CID(models.Model):
    codigo = models.CharField(verbose_name="Código", max_length=6, unique=True)
    doenca = models.CharField(verbose_name="Doença", max_length=250)

    class Meta:
        verbose_name = "CID"
        verbose_name_plural = "CIDs"

    def __str__(self):
        return "%s - %s" % (self.codigo, self.doenca)


class CIAP(models.Model):
    codigo = models.CharField(verbose_name="Código", max_length=6, unique=True)
    doenca = models.CharField(verbose_name="Doença", max_length=100)

    class Meta:
        verbose_name = "CIAP"
        verbose_name_plural = "CIAPs"

    def __str__(self):
        return "%s - %s" % (self.codigo, self.doenca)


class TipoEnfoqueResposta(models.Model):
    nome = models.CharField(max_length=150)
    enfoque_principal = models.BooleanField(default=False)

    class Meta:
        ordering = ("nome",)
        verbose_name = "Enfoque de Solicitação de Resposta"
        verbose_name_plural = "Enfoques de Solicitação de Resposta"

    def __str__(self):
        return "%s" % self.nome


class AreaTematicaQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'get_qtd_profissonais_saude').actions('profissionaissaudeareatematica', 'agendaareatematica')


class AreaTematica(models.Model):
    nome = models.CharField(max_length=60, unique=True)
    ativo = models.BooleanField(default=True)
    ativo_sincrona = models.BooleanField(default=False)

    objects = AreaTematicaQuerySet()

    class Meta:
        ordering = ("nome",)
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def get_profissonais_saude(self):
        return ProfissionalSaude.objects.filter(especialidade__area_tematica=self).fields('usuario', 'estabelecimento')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.get_profissonais_saude().count()
    
    @meta()
    def get_agenda(self, readonly=True):
        qs = HorarioProfissionalSaude.objects.filter(
            profissional_saude__especialidade__area_tematica=self
        ).order_by('data_hora')
        start_day = qs.values_list('data_hora', flat=True).first()
        scheduler = Scheduler(start_day=start_day, readonly=True)
        qs = qs.filter(data_hora__lt=scheduler.end_day)
        campos = ("data_hora", "profissional_saude__usuario__nome", "profissional_saude__especialidade__area_tematica__nome")
        qs1 = qs.filter(solicitacao__isnull=True)
        qs2 = qs.filter(solicitacao__isnull=False)
        horarios = {}
        for i, solicitacoes in enumerate([qs1, qs2]):
            for data_hora, nome, area in solicitacoes.values_list(*campos):
                if data_hora not in horarios:
                    horarios[data_hora] = []
                profissional = f'{nome} ({area.upper()} )' if area else nome
                horarios[data_hora].append(Text(profissional, color="#a4e2a4" if i==0 else "#f47c7c"))
        for data_hora, text in horarios.items():
            scheduler.append(data_hora, text, icon='stethoscope')
        return scheduler

    def __str__(self):
        return "%s" % self.nome


class TipoSolicitacao(models.Model):
    TELECONSULTA = 1
    TELETERCONSULTA = 2
    nome = models.CharField(verbose_name='Nome', max_length=30)

    class Meta:
        verbose_name = "Tipo de Serviço"
        verbose_name_plural = "Tipos de Serviços"

    def __str__(self):
        return "%s" % self.nome

@role('ge', username='gestores__cpf', estado='pk')
class UnidadeFederativa(models.Model):
    codigo = models.CharField(max_length=2, primary_key=True)
    sigla = models.CharField(max_length=2, unique=True)
    nome = models.CharField(max_length=60, unique=True)

    gestores = models.ManyToManyField(
        "comum.Usuario", verbose_name="Gestores", blank=True
    )

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        ordering = ["nome"]

    def __str__(self):
        return "%s/%s" % (self.nome, self.sigla)


class NivelFormacao(models.Model):
    nome = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Nível de Formação"
        verbose_name_plural = "Níveis de Formação"

    def __str__(self):
        return "%s" % self.nome


class Sexo(models.Model):
    SEXO_CHOICES = (("M", "Masculino"), ("F", "Feminino"), ("O", "Outro"))
    nome = models.CharField(max_length=10, choices=SEXO_CHOICES)

    def __str__(self):
        return "%s" % self.nome


class Perfil(models.Model):
    nome = models.CharField(max_length=25, unique=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return "%s" % self.nome

@role('gm', username='gestores__cpf', municipio='pk')
class Municipio(models.Model):
    estado = models.ForeignKey(UnidadeFederativa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6, unique=True)
    nome = models.CharField(max_length=60)

    gestores = models.ManyToManyField(
        "comum.Usuario",
        verbose_name="Gestores",
        blank=True,
        related_name="municipios_gerenciados",
    )

    class Meta:
        verbose_name = "Município"
        verbose_name_plural = "Municípios"

    def __str__(self):
        return "(%s) %s/%s" % (self.codigo, self.nome, self.estado.sigla)


class EstabelecimentoSaudeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search("codigo_cnes", "nome")
            .fields("foto", ("codigo_cnes", "get_qtd_profissonais_saude"),  "municipio")
            .filters("municipio").actions('agendaestabelecimentosaude', 'equipeestabelecimentosaude').cards()
        )

@role('gu', username='gestores__cpf', unidade='pk')
@role('ou', username='gestores__cpf', unidade='pk')
class EstabelecimentoSaude(models.Model):
    foto = models.ImageField(
        verbose_name="Foto", null=True, blank=True, upload_to="estabelecimentos_saude", width=200
    )

    codigo_cnes = models.CharField(verbose_name="CNES", max_length=12, unique=True)
    nome = models.CharField(max_length=100)
    municipio = models.ForeignKey(
        Municipio, related_name="estabelecimentos", on_delete=models.CASCADE
    )

    logradouro = models.CharField(max_length=120, null=True)
    numero = models.CharField(max_length=10, null=True)
    bairro = models.CharField(max_length=40, null=True)
    cep = models.CharField(max_length=10, null=True)

    latitude = models.CharField(verbose_name="Latitude", null=True, blank=True)
    longitude = models.CharField(verbose_name="Longitude", null=True, blank=True)

    gestores = models.ManyToManyField(
        "comum.Usuario", verbose_name="Gestores", blank=True
    )

    operadores = models.ManyToManyField(
        "comum.Usuario",
        verbose_name="Operadores",
        blank=True,
        related_name="estabelecimentos_operados",
    )

    objects = EstabelecimentoSaudeQuerySet()

    class Meta:
        icon = "building"
        verbose_name = "Unidade de Saúde"
        verbose_name_plural = "Unidades de Saúde"

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", ("nome", ("codigo_cnes", "municipio")))
            .group()
                .fieldset("Endereço", ("logradouro", ("numero", "bairro", "cep")))
                .fieldset("Geolocalização", (("latitude", "longitude"), 'get_mapa'))
                .queryset("Gestores", "gestores")
                .queryset("Operadores", "operadores")
                .queryset("Profissionais", "get_profissionais_saude")
            .parent()
            .fieldset("Agenda dos Próximos Dias", ("get_agenda",))
        )

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", ("foto", "nome", ("codigo_cnes", "municipio")))
            .fieldset("Endereço", ("logradouro", ("numero", "bairro", "cep")))
            .fieldset("Geolocalização", (("latitude", "longitude"),))
            .fieldset("Recursos Humanos", ("gestores", "operadores"))
        )

    def __str__(self):
        return "%s - %s" % (self.codigo_cnes, self.nome)
    
    @meta()
    def get_foto(self):
        return Image(self.foto, placeholder='/static/images/ubs.png', width='auto', height='auto')
    
    def get_mapa(self):
        return Map(self.latitude, self.longitude)

    @meta('Profissionais de Saúde')
    def get_profissionais_saude(self):
        return self.profissionalsaude_set.all().filters('especialidade')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    @meta()
    def get_agenda(self, readonly=True):
        qs = HorarioProfissionalSaude.objects.filter(
            profissional_saude__estabelecimento=self
        )
        start_day = qs.values_list('data_hora', flat=True).first()
        scheduler = Scheduler(start_day=start_day, readonly=True)
        campos = ("data_hora", "profissional_saude__usuario__nome", "profissional_saude__especialidade__area_tematica__nome")
        qs1 = qs.filter(solicitacao__isnull=True)
        qs2 = qs.filter(solicitacao__isnull=False)
        horarios = {}
        for i, solicitacoes in enumerate([qs1, qs2]):
            for data_hora, nome, area in solicitacoes.values_list(*campos):
                if data_hora not in horarios:
                    horarios[data_hora] = []
                profissional = f'{nome} ({area.upper()} )' if area else nome
                horarios[data_hora].append(Text(profissional, color="#a4e2a4" if i==0 else "#f47c7c"))
        for data_hora, text in horarios.items():
            scheduler.append(data_hora, text, icon='stethoscope')
        return scheduler


class EspecialidadeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search('nome')
            .fields('codigo_cbo', 'nome', 'area_tematica', 'get_qtd_profissonais_saude')
            .filters('categoria', 'area_tematica')
            .actions('profissionaissaudeespecialidade')
        )
    

class Especialidade(models.Model):

    codigo_cbo = models.CharField(verbose_name="Código", max_length=6, unique=True)
    nome = models.CharField(max_length=150)
    categoria = models.ForeignKey(
        "comum.CategoriaProfissional", on_delete=models.CASCADE
    )
    area_tematica = models.ForeignKey(AreaTematica, verbose_name='Área Temática', on_delete=models.CASCADE, null=True, blank=True)

    objects = EspecialidadeQuerySet()

    def get_profissonais_saude(self):
        return self.profissionalsaude_set.fields('usuario', 'estabelecimento')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    def __str__(self):
        return "%s - %s" % (self.codigo_cbo, self.nome)


class UsuarioQueryset(models.QuerySet):
    def all(self):
        return self.search("nome", "cpf").fields("nome", "cpf")


class Usuario(models.Model):

    foto = models.ImageField(
        verbose_name="Foto", null=True, blank=True, upload_to="pessoas_fisicas"
    )

    nome = models.CharField(verbose_name='Nome', max_length=80)
    nome_social = models.CharField(verbose_name='Nome Social', max_length=80, null=True, blank=True)
    cpf = models.CharField(verbose_name='CPF', max_length=14, unique=True)
    telefone = models.CharField(verbose_name='Telefone', max_length=15, blank=True, null=True)
    endereco = models.CharField(verbose_name='Endereço', max_length=255, blank=True, null=True)
    numero = models.CharField(verbose_name='Número', max_length=255, blank=True, null=True)
    cep = models.CharField(verbose_name='CEP', max_length=255, blank=True, null=True)
    bairro = models.CharField(verbose_name='Bairro', max_length=255, blank=True, null=True)
    complemento = models.CharField(verbose_name='Complemento', max_length=150, blank=True, null=True)
    municipio = models.ForeignKey(Municipio, verbose_name='Município', null=True, on_delete=models.PROTECT, blank=True)
    data_nascimento = models.DateField(verbose_name='Data de Nascimento', null=True)
    cns = models.CharField(verbose_name='CNS', max_length=15, null=True)
    perfil = models.ManyToManyField("Perfil", related_name="usuario")
    sexo = models.ForeignKey(
        Sexo, verbose_name='Sexo', related_name="usuarios", null=True, on_delete=models.PROTECT, blank=True
    )
    user = models.ForeignKey(User, related_name="usuario", on_delete=models.PROTECT, null=True)

    objects = UsuarioQueryset()

    class Meta:
        icon = "users"
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset(
                "Dados Gerais",
                (
                    ("nome", "nome_social"),
                    ("cpf", "data_nascimento"),
                    ("sexo", "telefone"),
                ),
            )
            .fieldset(
                "Endereço",
                ("endereco", ("numero", "cep"), ("bairro", "municipio"), "complemento"),
            )
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset(
                "Dados Gerais",
                (
                    ("nome", "nome_social"),
                    ("cpf", "data_nascimento"),
                    ("sexo", "telefone"),
                ),
            )
            .fieldset(
                "Endereço",
                ("endereco", ("numero", "cep"), ("bairro", "municipio"), "complemento"),
            )
        )

    def get_nome(self):
        if self.nome_social:
            return "%s / %s" % (self.nome_social, self.nome)
        else:
            return self.nome

    def __str__(self):
        if self.nome_social:
            return "%s / %s - %s" % (self.nome_social, self.nome, self.cpf)
        else:
            return "%s - %s" % (self.nome, self.cpf)

    def idade(self):
        today = date.today()
        if self.data_nascimento:
            return (
                today.year
                - self.data_nascimento.year
                - (
                    (today.month, today.day)
                    < (self.data_nascimento.month, self.data_nascimento.day)
                )
            )
        else:
            return "Não informada"


class AnexoUsuario(models.Model):
    usuario = models.ForeignKey(
        Usuario, related_name="foto_confirmacao", on_delete=models.PROTECT
    )
    arquivo = models.FileField(max_length=200, upload_to="imagens_reconhecimento")
    documento = models.FileField(max_length=200, upload_to="documento", null=True)


class ProfissionalSaudeQueryset(models.QuerySet):
    def all(self):
        return (
            self.search("usuario__nome", "usuario__cpf")
            .filters(
                "estabelecimento",
                "especialidade",
            )
            .fields(
                "estabelecimento",
                "especialidade",
            )
            .actions("agendaprofissionalsaude", "definirhorarioprofissionalsaude")
        ).cards()

@role('ps', username='usuario__cpf', unidade='estabelecimento')
class ProfissionalSaude(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        related_name="profissional_saude",
        on_delete=models.PROTECT,
        verbose_name="Profissional",
    )
    estabelecimento = models.ForeignKey(
        EstabelecimentoSaude,
        verbose_name='Unidade',
        null=True,
        on_delete=models.CASCADE,
    )
    formacao = models.ForeignKey(NivelFormacao, null=True, on_delete=models.CASCADE)
    registro_profissional = models.CharField(
        "Registro Profissional", max_length=30, blank=True
    )
    especialidade = models.ForeignKey(
        Especialidade, null=True, on_delete=models.CASCADE
    )
    registro_especialista = models.CharField(
        "Registro Especialista", max_length=30, blank=True, null=True
    )
    programa_provab = models.BooleanField(default=False)
    programa_mais_medico = models.BooleanField(default=False)
    residente = models.BooleanField(default=False)
    perceptor = models.BooleanField(default=False)
    ativo = models.BooleanField(default=False)

    objects = ProfissionalSaudeQueryset()

    class Meta:
        icon = "stethoscope"
        verbose_name = "Vínculo Profissional"
        verbose_name_plural = "Vínculos Profissionais"
        search_fields = 'usuario__cpf', 'usuario__nome'

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", ("estabelecimento", "usuario"))
            .fieldset(
                "Dados Profissionais",
                (("registro_profissional", "especialidade", "registro_especialista"),),
            )
            .fieldset(
                "Outras Informações",
                (
                    ("programa_provab", "programa_mais_medico"),
                    ("residente", "perceptor"),
                ),
            )
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", ("estabelecimento", "usuario"))
            .fieldset(
                "Dados Profissionais",
                (("registro_profissional", "especialidade", "registro_especialista"),),
            )
            .fieldset(
                "Outras Informações",
                (
                    ("programa_provab", "programa_mais_medico"),
                    ("residente", "perceptor"),
                ),
            )
            .fieldset("Agenda dos Próximos Dias", ("get_agenda",))
        )

    def __str__(self):
        return "%s (CPF: %s / CRM: %s)" % (
            self.usuario.nome,
            self.usuario.cpf,
            self.registro_profissional,
        )

    @meta(None)
    def get_agenda(self, readonly=True):
        qs = self.horarioprofissionalsaude_set.filter(data_hora__gte=date.today()).order_by('data_hora')
        scheduler = Scheduler(
            readonly=readonly,
        )
        for data_hora, solicitacao in qs.values_list("data_hora", "solicitacao"):
            scheduler.append(data_hora, f'Solicitação #{solicitacao}' if solicitacao else None, icon='stethoscope')
        qs2 = HorarioProfissionalSaude.objects.filter(
            data_hora__gte=date.today(),
            profissional_saude__usuario__cpf=self.usuario.cpf
        ).exclude(profissional_saude=self.pk)
        for data_hora, estabelecimento in qs2.values_list("data_hora", "profissional_saude__estabelecimento__nome"):
            scheduler.append(data_hora, estabelecimento, icon='x')
        return scheduler


class HorarioProfissionalSaude(models.Model):
    profissional_saude = models.ForeignKey(
        ProfissionalSaude,
        verbose_name="Profissional de Saúde",
        on_delete=models.CASCADE,
    )
    data_hora = models.DateTimeField(verbose_name="Data/Hora")

    class Meta:
        verbose_name = "Horário de Atendimento"
        verbose_name_plural = "Horários de Atendimento"

    def __str__(self):
        return "{} - {}".format(
            self.data_hora.strftime("%d/%m/%Y %H:%M"), self.profissional_saude
        )


class HistoricoAlteracaoProfissional(models.Model):
    ACOES_PROFISSIONAL = (
        ("criado", "Cadastro Realizado"),
        ("modificado", "Dados Alterados"),
        ("aceite", "Cadastro Aceito"),
        ("vinculo_modificado", "Alteração de Vínculos"),
    )

    profissional = models.ForeignKey(
        ProfissionalSaude, related_name="historico_alteracoes", on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(
        Usuario, related_name="historico_alteracoes", on_delete=models.CASCADE
    )
    acao = models.CharField(choices=ACOES_PROFISSIONAL, max_length=25)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Alteração Profissional"
        verbose_name_plural = "Histórico de Alteração de Profissional"


# TODO remover
class ProfissionalVinculo(models.Model):
    profissional = models.ForeignKey(
        ProfissionalSaude, related_name="vinculos", on_delete=models.CASCADE
    )
    estabelecimento = models.ForeignKey(
        EstabelecimentoSaude,
        related_name="vinculos",
        null=True,
        on_delete=models.CASCADE,
    )
    profissao = models.ForeignKey(
        Especialidade, related_name="vinculos", null=True, on_delete=models.CASCADE
    )
    residente = models.BooleanField(default=False)
    perceptor = models.BooleanField(default=False)
    ativo = models.BooleanField(default=False)

    def __str__(self):
        return "{0} / {1}".format(self.estabelecimento, self.profissao)


class SolicitacaoQuerySet(models.QuerySet):
    def all(self):
        return (
            self.filters("area_tematica", "paciente", "solicitante", "especialista")
            .calendar("agendado_para")
            .fields(
                ("area_tematica", "agendado_para", "tipo_solicitacao"),
                ("solicitante", "estabelecimento", "especialista"),
                ("get_tags")
            ).limit(5).order_by('-id')
        )


class Solicitacao(models.Model):
    # TODO remover
    motivadora = models.OneToOneField(
        "Solicitacao", related_name="duvida_filha", null=True, on_delete=models.PROTECT
    )
    # TODO remover
    vinculo = models.ForeignKey(
        ProfissionalVinculo, related_name="solicitacoes", on_delete=models.CASCADE, null=True
    )

    solicitante = models.ForeignKey(
        ProfissionalSaude,
        verbose_name='Responsável',
        related_name="solicitacoes_solicitante",
        on_delete=models.CASCADE,
        null=True,
        help_text='Profissional de saúde responsável pelo atendimento'
    )
    estabelecimento = models.ForeignKey(
        EstabelecimentoSaude, null=True, on_delete=models.CASCADE
    )
    especialista = models.ForeignKey(
        ProfissionalSaude,
        related_name="solicitacoes_especialista",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Profissional de saúde que será consultado pelo profissional responsável pelo atendimento'
    )

    area_tematica = models.ForeignKey(
        AreaTematica, verbose_name='Área', related_name="solicitacoes", on_delete=models.CASCADE
    )
    enfoque_solicitacao = models.ForeignKey(
        TipoEnfoqueResposta, related_name="solicitacoes", on_delete=models.CASCADE
    )
    tipo_solicitacao = models.ForeignKey(
        TipoSolicitacao, verbose_name='Tipo de Atendimento', related_name="solicitacoes", on_delete=models.CASCADE
    )
    # TODO remover
    ultimo_fluxo = models.OneToOneField(
        "FluxoSolicitacao",
        related_name="ultimo_fluxo_solicitacao",
        null=True,
        on_delete=models.PROTECT,
    )

    cid = models.ManyToManyField(CID, verbose_name='CID', related_name="cids")
    ciap = models.ManyToManyField(CIAP, verbose_name='CIAP', related_name="ciaps")

    data = models.DateTimeField(blank=True)
    assunto = models.CharField(max_length=200)
    duvida = models.TextField(max_length=2000)
    paciente = models.ForeignKey(
        "Usuario", verbose_name='Paciente', related_name="solicitacoes_paciente", on_delete=models.PROTECT
    )
    duracao = models.DurationField(null=True, default=timedelta(days=0))
    atraso = models.BooleanField(default=False, null=True)
    sugestao_sincrona = models.CharField(max_length=150, null=True)

    horario_profissional_saude = models.ForeignKey(
        HorarioProfissionalSaude,
        verbose_name="Horário",
        on_delete=models.SET_NULL,
        null=True,
    )
    horario_excepcional = models.BooleanField(
        verbose_name="Horário Exceptional",
        default=False,
        help_text="Marque essa opção caso deseje agendar em um horário fora da agenda do profissional.",
    )
    justificativa_horario_excepcional = models.TextField(
        verbose_name="Justificativa do Horário",
        null=True,
        blank=True,
        help_text="Obrigatório para agendamentos em horário excepcional.",
    )
    agendado_para = models.DateTimeField(verbose_name='Data de Início', null=True, blank=True)

    finalizado_em = models.DateTimeField(verbose_name='Data de Término', null=True)

    # Verificando quantas vezes o solicitante acessou a TC
    qtd_acessos = models.IntegerField(default=0)

    motivo_cancelamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)
    motivo_reagendamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)

    objects = SolicitacaoQuerySet()

    class Meta:
        icon = "laptop-file"
        verbose_name = "Teleconsulta"
        verbose_name_plural = "Teleconsultas"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset(
                "Dados Gerais",
                (
                    ("tipo_solicitacao", "area_tematica"),
                ),
            )
            .fieldset(
                "Detalhamento",
                (
                    "paciente:cadastrarusuario",
                    "assunto",
                    "duvida",
                    ("cid", "ciap"),
                ),
            )
            .fieldset(
                "Agendamento",
                (
                    "solicitante:consultaragenda",
                    "especialista",
                    "horario_profissional_saude",
                    "horario_excepcional",
                    "justificativa_horario_excepcional",
                    "agendado_para",
                ),
            )
        )
    
    def serializer(self):
        return (
            super()
            .serializer()
            .fields('get_tags')
            .actions('anexararquivo', 'salavirtual')
            .fieldset(
                "Dados Gerais",
                (
                    "tipo_solicitacao",
                    ("estabelecimento", "estabelecimento__municipio"),
                    ("agendado_para", "finalizado_em", "duracao_webconf"),
                )
            )
            .group()
                .section('Detalhamento')
                    .fieldset(
                        "Dados do Paciente", (
                            ("nome", "cpf"),
                            ("data_nascimento", "sexo")
                        ), attr="paciente"
                    )
                    .fieldset(
                        "Dados do Solicitante", (
                            "usuario__nome",
                            ("formacao", "registro_profissional"),
                            ("especialidade", "registro_especialista"),
                        ), attr="solicitante"
                    )
                    .fieldset(
                        "Dados do Especialista", (
                            "usuario__nome",
                            ("formacao", "registro_profissional"),
                            ("especialidade", "registro_especialista"),
                        ), attr="especialista", condition='especialista'
                    )
                    .fieldset(
                        "Dados da Consulta", (
                            ("assunto", "area_tematica"),
                            "duvida",
                            ("cid", "ciap"),
                        )
                    )
                .parent()
                .queryset('Histórico', 'get_historico')
                .queryset('Anexos', 'get_anexos')
                .queryset('Encaminhamentos/Condutas', 'get_condutas_ecaminhamentos')
            .parent()
        )
    
    @meta()
    def get_tags(self):
        tags = []
        if self.tipo_solicitacao_id == TipoSolicitacao.TELETERCONSULTA:
            color = "#265890"
            icon = 'people-group'
        else:
            color = '#5ca05d'
            icon = 'people-arrows'
        tag = Badge(color, self.tipo_solicitacao, icon=icon)
        tags.append(tag)

        if self.finalizado_em:
            tag = Badge("#5ca05d", 'Finalizada', icon='check')
        elif self.motivo_reagendamento:
            tag = Badge("orange", 'Reagendada', icon='calendar')
        elif self.motivo_cancelamento:
            tag = Badge("red", 'Cancelada', icon='x')
        else:
            tag = Badge("#265890", 'Agendada', icon='clock')
        tags.append(tag)
        return tags
    
    @meta('Histórico')
    def get_historico(self):
        return self.fluxos.fields(
            'data', ('status_novo', 'responsavel'), 'profissional_destino',
            'comentario', 'encaminhamento', 'conduta'
        ).timeline()
    
    @meta('Anexos')
    def get_anexos(self):
        return self.anexos.fields('get_nome_arquivo', 'autor', 'get_arquivo')
    
    @meta('Anexos')
    def get_anexos_webconf(self):
        return self.get_anexos().reloadable()
    
    
    @meta('Encaminhamentos e Condutas')
    def get_condutas_ecaminhamentos(self):
        return self.condutas_ecaminhamentos.fields('subjetivo', 'objetivo', 'plano').rows()
    
    @meta()
    def get_webconf(self):
        return WebConf('aaaa', 'bbbb')

    def get_token_paciente(self):
        signer = Signer()
        data_hora = datetime.now()
        dados = "{}".format(self.pk)
        return binascii.hexlify(signer.sign(dados).encode()).decode()

    @classmethod
    def parse_token_paciente(cls, token):
        signer = Signer()
        return signer.unsign(binascii.unhexlify(token.encode()).decode())

    @property
    def tempo_decorrido(self):
        try:
            resposta = self.resposta
            if resposta.finalizada:
                return timesince(self.data, self.resposta.data)
            else:
                return timesince(self.data, timezone.now())
        except Exception as e:
            return timesince(self.data, timezone.now())

    @meta('Duração')
    def duracao_webconf(self):
        if self.finalizado_em and self.agendado_para:
            return timesince(self.agendado_para, self.finalizado_em)
        return "-"

    @property
    def tempo_restante(self):
        return timesince(timezone.now(), self.data + timedelta(hours=72))

    @property
    def status_atual(self):
        return self.ultimo_fluxo.status_novo.get_status_display()

    @property
    def comentario_devolucao(self):
        if self.ultimo_fluxo.status_novo.status == "devolvida":
            return self.ultimo_fluxo.comentario

        return None

    # TODO remover
    def get_especialista(self):
        ultimo_fluxo = self.ultimo_fluxo
        ultimo_fluxo_status = ultimo_fluxo.status_novo.status
        if ultimo_fluxo_status in ("encaminhada", "agendada"):
            return ultimo_fluxo.profissional_destino
        elif ultimo_fluxo_status in ("aceita", "respondida", "devolvida"):
            return ultimo_fluxo.responsavel
        elif ultimo_fluxo_status == "finalizada":
            # Ao reaver uma solicitação, ela volta para o status nova, removendo o histórico anterior
            ultimo_fluxo = (
                self.fluxos.filter(status_novo__status="encaminhada")
                .select_related("profissional_destino")
                .last()
            )

            if hasattr(ultimo_fluxo, "profissional_destino"):
                return ultimo_fluxo.profissional_destino
            else:
                ultimo_fluxo = self.fluxos.filter(status_novo__status="aceita").last()

                if ultimo_fluxo:
                    return ultimo_fluxo.responsavel

        return None

    def __str__(self):
        return "%s - %s" % (self.id, self.assunto)

    def save(self, *args, **kwargs):
        if not self.estabelecimento_id and self.solicitante_id:
            self.estabelecimento = self.solicitante.estabelecimento
        if not self.enfoque_solicitacao_id:
            self.enfoque_solicitacao = TipoEnfoqueResposta.objects.get(pk=11)
        if not self.tipo_solicitacao_id:
            self.tipo_solicitacao = TipoSolicitacao.objects.get(pk=2)
        if not self.especialista_id and self.horario_profissional_saude_id:
            self.especialista = self.horario_profissional_saude.profissional_saude
        if not self.agendado_para and self.horario_profissional_saude_id:
            self.agendado_para = self.horario_profissional_saude.data_hora
        if not self.data:
            self.data = timezone.now()

        super(Solicitacao, self).save(*args, **kwargs)


class AnexoSolicitacao(models.Model):
    solicitacao = models.ForeignKey(
        Solicitacao, related_name="anexos", on_delete=models.CASCADE
    )
    arquivo = models.FileField(max_length=200, upload_to="anexos_teleconsuta")
    autor = models.ForeignKey(
        Usuario, related_name="anexos_solicitacoes", null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Anexo de Solicitação"
        verbose_name_plural = "Anexos de Solicitação"

    def __str__(self):
        return "%s" % self.solicitacao

    @meta('Nome do Arquivo')
    def get_nome_arquivo(self):
        return self.arquivo.name.split("/")[-1]
    
    def get_arquivo(self):
        return FileLink(self.arquivo, icon='file', modal=True)


class StatusSolicitacao(models.Model):

    STATUS_SOLICITACAO = (
        ("rascunho", "Rascunho"),
        ("nova", "Nova"),
        ("encaminhada", "Encaminhada"),
        ("aceita", "Aceita"),
        ("devolvida", "Devolvida"),
        ("respondida", "Respondida"),
        ("remarcada", "Devolvida ao Telerregulador"),
        ("finalizada", "Finalizada"),
        ("cancelada", "Cancelada"),
        ("reagendada", "Reagendamento"),
        ("agendada", "Agendada"),
        ("realizada", "Realizada"),
        ("nao_realizada", "Não Realizada"),
    )

    status = models.CharField(choices=STATUS_SOLICITACAO, max_length=20)

    class Meta:
        verbose_name = "Status de Solicitação"
        verbose_name_plural = "Status de Solicitação"

    def __str__(self):
        return "%s" % self.get_status_display()


class FluxoSolicitacao(models.Model):
    solicitacao = models.ForeignKey(
        Solicitacao, related_name="fluxos", on_delete=models.CASCADE
    )

    status_novo = models.ForeignKey(
        StatusSolicitacao, related_name="fluxos_novos", on_delete=models.CASCADE
    )

    responsavel = models.ForeignKey(
        ProfissionalSaude, related_name="fluxos_responsavel", on_delete=models.CASCADE
    )
    profissional_destino = models.ForeignKey(
        ProfissionalSaude,
        related_name="fluxos_profissional_destino",
        null=True,
        on_delete=models.CASCADE,
    )

    data = models.DateTimeField(auto_now_add=True, null=True)
    comentario = models.TextField(blank=True)

    encaminhamento = models.TextField(blank=True, null=True)
    conduta = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Histórico de Solicitação"
        verbose_name_plural = "Histórico de Solicitação"

    def __str__(self):
        return "%s" % self.status_novo.status

    def save(self, *args, **kwargs):
        super(FluxoSolicitacao, self).save(*args, **kwargs)

        # Caso a solicitação tenha sido salva como rascunho,
        # a data da mesma deve ser atualizada
        if (
            not self.solicitacao.ultimo_fluxo is None
            and self.status_novo.status == "nova"
        ):
            self.solicitacao.data = timezone.now()

        # Atualizando duracao do processo de resposta
        if self.status_novo.status == "respondida":
            self.solicitacao.duracao = (
                self.solicitacao.resposta.data - self.solicitacao.data
            )
        elif (
            self.status_novo.status == "rascunho"
            and self.status_novo.status == "finalizada"
        ):
            pass
        else:
            self.solicitacao.duracao = timezone.now() - self.solicitacao.data

        # Atualizando ultimo fluxo e flag de atraso da solicitacao associada
        self.solicitacao.atraso = self.solicitacao.duracao > timedelta(days=3)
        self.solicitacao.ultimo_fluxo = self
        self.solicitacao.save()


class AvaliacaoSolicitacao(models.Model):
    SATISFACAO = (
        (1, "Muito Satisfeito"),
        (2, "Satisfeito"),
        (3, "Indiferente"),
        (4, "Insatisfeito"),
        (5, "Muito Insatisfeito"),
    )
    RESPONDEU_DUVIDA = ((1, "Sim"), (2, "Parcialmente"), (3, "Não"))
    EVITOU_ENCAMINHAMENTO = (
        (1, "Sim, evitou"),
        (2, "Não, pois ainda será necessário referenciá-lo (encaminhá-lo)"),
        (3, "Não, pois não era minha intenção referenciá-lo antes da teleconsulta"),
        (4, "Não, por outros motivos"),
    )
    MUDOU_CONDUTA = (
        (1, "Sim"),
        (2, "Não, pois eu já seguia a conduta/abordagem sugerida"),
        (3, "Não, pois não concordo com a reposta"),
        (4, "Não, pois não há como seguir a conduta sugerida em nosso contexto"),
        (5, "Não, por outros motivos"),
    )
    POSSIBILIDADE_TEXTO_CHOICES = (
        (0, "Sim, pode ser plenamente respondida"),
        (1, "Sim, parcialmente"),
        (2, "Não, a dúvida necessita de teleconsulta por vídeo"),
        (3, "Não está clara qual é a dúvida"),
    )
    SIM_NAO_CHOICES = ((True, "Sim"), (False, "Não"))

    solicitacao = models.ForeignKey(
        Solicitacao, related_name="avaliacao", on_delete=models.PROTECT
    )

    satisfacao = models.IntegerField(choices=SATISFACAO)
    respondeu_duvida = models.IntegerField(choices=RESPONDEU_DUVIDA)
    evitou_encaminhamento = models.IntegerField(choices=EVITOU_ENCAMINHAMENTO)
    mudou_conduta = models.IntegerField(choices=MUDOU_CONDUTA)
    recomendaria = models.BooleanField(choices=SIM_NAO_CHOICES, default=None)
    data = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Avaliação de Solicitação"
        verbose_name_plural = "Avaliações de Solicitação"


# TODO remover
class ProfissionalSaudeRegulador(models.Model):
    profissional_saude = models.OneToOneField(
        ProfissionalSaude,
        related_name="regulador",
        primary_key=True,
        on_delete=models.PROTECT,
    )
    area_tematica = models.ManyToManyField(AreaTematica)


# TODO remover
class ProfissionalSaudeEspecialista(models.Model):
    profissional_saude = models.ForeignKey(
        ProfissionalSaude, related_name="especialista", on_delete=models.PROTECT
    )
    tipo_solicitacao = models.ManyToManyField(
        TipoSolicitacao, related_name="especialista"
    )
    area_tematica = models.ManyToManyField(AreaTematica, related_name="especialista")
    habilitado_iatae = models.BooleanField(default=False)
    receber_tcs = models.BooleanField(default=True)

    def __str__(self):
        return "%s (%s)" % (
            self.profissional_saude.usuario.nome,
            self.profissional_saude.profissao,
        )


# TODO remover
class ProfissionalSaudeGestorMunicipio(models.Model):
    profissional_saude = models.ForeignKey(
        ProfissionalSaude, related_name="gestor_municipio", on_delete=models.PROTECT
    )
    municipio = models.ForeignKey(
        Municipio, related_name="gestor_municipio", on_delete=models.CASCADE
    )

    def __str__(self):
        if hasattr(self.profissional_saude, "municipio"):
            return "%s (%s)" % (self.profissional_saude.nome, self.municipio)
        else:
            return "%s (%s)" % (self.profissional_saude.nome, "Não Informado")


class MotivoEncerramentoConferencia(models.Model):
    OPCOES_MOTIVO = (
        ("ausencia_solicitante", "Ausência do Solicitante"),
        ("ausencia_paciente", "Ausência do Paciente"),
        ("ausencia_ambos", "Ausência do Solicitante e Paciente"),
        ("outro", "Outro"),
    )

    solicitacao = models.ForeignKey(
        Solicitacao, related_name="motivo_realizacao", on_delete=models.PROTECT
    )
    profissional = models.ForeignKey(
        ProfissionalSaude, related_name="motivos_realizacao", on_delete=models.CASCADE
    )
    motivo = models.CharField(choices=OPCOES_MOTIVO, max_length=40)
    consideracoes = models.TextField()
    data = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Motivo de Encerramento de Conferência"
        verbose_name_plural = "Motivos de Encerramento de Conferência"

class EncaminhamentosCondutas(models.Model):
    solicitacao = models.ForeignKey(Solicitacao, related_name="condutas_ecaminhamentos", on_delete=models.CASCADE)
    responsavel = models.ForeignKey(ProfissionalSaude, related_name="condutas_ecaminhamentos", on_delete=models.CASCADE)

    # Método SOAP - Subjetivo, Objetivo, Avaliação, Plano
    subjetivo = models.TextField(verbose_name='S - subjetivo', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro da parte subjetiva da anamnese da consulta, ou seja, os dados dos sentimentos e percepções do cidadão em relação à sua saúde.')
    objetivo = models.TextField(verbose_name='O - objetivo', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro do exame físico, como os sinais e sintomas detectados, além do registro de resultados de exames realizados.')
    avaliacao = models.TextField(verbose_name='A - avaliacao', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro da conclusão feita pelo profissional de saúde a partir dos dados observados nos itens anteriores, como os motivos para aquele encontro, a anamnese do cidadão e dos exames físico e complementares.')
    plano = models.TextField(verbose_name='P - Plano', blank=True, null=True, help_text='Conjunto de funcionalidades que permite registrar o plano de cuidado ao cidadão em relação ao(s) problema(s) avaliado(s).')

    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encaminhamento e Condutas'
        verbose_name_plural = 'Encaminhamentos e Condutas'

    def __str__(self):
        return '{} - {}'.format(self.data.strftime('%d/%m/%Y %H:%M'), self.responsavel)


class CertificadoDigital(models.Model):
    user = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.CASCADE)
    arquivo = models.FileField(
        verbose_name="Arquivo", upload_to="certificados_digitais"
    )
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    validade = models.DateField(verbose_name="Validade")

    class Meta:
        verbose_name = "Certificado Digital"
        verbose_name_plural = "Certificados Digitais"

    def __str__(self):
        return "{} - (VÁLIDO ATÉ {})".format(
            self.descricao, self.validade.strftime("%d/%m/%Y")
        )

    def assinar(
        self, caminho_arquivo, senha, tipo_documento=None, codigo_autenticacao=None
    ):
        return signer.sign(
            pfx_file_path=self.arquivo.path,
            passwd=senha,
            sign_img=True,
            bgcolor="#ebf3e5",
            pdf_file_path=caminho_arquivo,
            document_type=tipo_documento,
            authentication_code=codigo_autenticacao,
            x=0,
            y=0,
        )

    def testar(self, senha):
        try:
            return self.descricao == signer.subject(self.arquivo.path, senha).get("CN")
        except Exception:
            return False

    def save(self, *args, **kwargs):
        self.descricao = ""
        self.validade = date.today()
        super().save(*args, **kwargs)
        try:
            self.validade = signer.expiration_date(self.arquivo.path, self.passwd)
            self.descricao = signer.subject(self.arquivo.path, self.passwd).get("CN")
            super().save(*args, **kwargs)
        except Exception:
            pass
