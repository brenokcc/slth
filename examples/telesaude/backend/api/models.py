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
from slth.models import User, RoleFilter
from slth.components import Scheduler, FileLink, WebConf, Image, Map, Text, Badge, TemplateContent



class CIDQuerySet(models.QuerySet):
    def all(self):
        return self.search('codigo', 'doenca')


class CID(models.Model):
    codigo = models.CharField(verbose_name="Código", max_length=6, unique=True)
    doenca = models.CharField(verbose_name="Doença", max_length=250)

    objects = CIDQuerySet()
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


class AreaQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'get_qtd_profissonais_saude').actions('profissionaissaudearea')


class Area(models.Model):
    nome = models.CharField(max_length=60, unique=True)

    objects = AreaQuerySet()

    class Meta:
        ordering = ("nome",)
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def get_profissonais_saude(self):
        return ProfissionalSaude.objects.filter(especialidade__area=self).fields('pessoa_fisica', 'nucleo', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.get_profissonais_saude().count()
    
    def __str__(self):
        return self.nome


class TipoAtendimento(models.Model):
    TELECONSULTA = 1
    TELETERCONSULTA = 2
    nome = models.CharField(verbose_name='Nome', max_length=30)

    class Meta:
        verbose_name = "Tipo de Atendimento"
        verbose_name_plural = "Tipos de Atendimentos"

    def __str__(self):
        return "%s" % self.nome


class EstadoQuerySet(models.QuerySet):
    def all(self):
        return self.search('sigla', 'nome', 'codigo')


class Estado(models.Model):
    codigo = models.CharField(verbose_name='Código IBGE', max_length=2, unique=True)
    sigla = models.CharField(verbose_name='Sigla', max_length=2, unique=True)
    nome = models.CharField(verbose_name='Nome', max_length=60, unique=True)

    objects = EstadoQuerySet()

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        ordering = ["nome"]

    @property
    def id(self):
        return self.codigo

    def __str__(self):
        return "%s/%s" % (self.nome, self.sigla)


class Sexo(models.Model):
    nome = models.CharField(verbose_name='Nome')

    def __str__(self):
        return self.nome


class MunicipioQuerySet(models.QuerySet):
    def all(self):
        return self.search('nome', 'codigo').filters('estado')


class Municipio(models.Model):
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=7, verbose_name='Código IBGE', unique=True)
    nome = models.CharField(verbose_name='Nome', max_length=60)

    objects = MunicipioQuerySet()

    class Meta:
        verbose_name = "Município"
        verbose_name_plural = "Municípios"

    def __str__(self):
        return "(%s) %s/%s" % (self.codigo, self.nome, self.estado.sigla)


class UnidadeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search("cnes", "nome")
            .fields("foto", "cnes",  "municipio")
            .filters("municipio__estado", "municipio").cards()
        )

class Unidade(models.Model):
    foto = models.ImageField(
        verbose_name="Foto", null=True, blank=True, upload_to="unidades", width=300
    )

    cnes = models.CharField(verbose_name="CNES", max_length=12, null=True, blank=True)
    nome = models.CharField(max_length=100)
    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE
    )

    logradouro = models.CharField(verbose_name='Logradouro', max_length=120, null=True, blank=True)
    numero = models.CharField(verbose_name='Número', max_length=10, null=True, blank=True)
    bairro = models.CharField(verbose_name='Bairro', max_length=40, null=True, blank=True)
    cep = models.CharField(verbose_name='CEP', max_length=10, null=True, blank=True)

    latitude = models.CharField(verbose_name="Latitude", null=True, blank=True)
    longitude = models.CharField(verbose_name="Longitude", null=True, blank=True)

    objects = UnidadeQuerySet()

    class Meta:
        icon = "building"
        verbose_name = "Unidade de Saúde"
        verbose_name_plural = "Unidades de Saúde"

    def serializer(self):
        return (
            super()
            .serializer().actions('edit')
            .fieldset("Dados Gerais", (("nome", "cnes"),))
            .fieldset("Endereço", (("cep", "bairro"), "logradouro", ("numero", "municipio")))
            .fieldset("Geolocalização", (("latitude", "longitude"), 'get_mapa'))
            .queryset("Profissionais de Saúde", 'get_profissionais_saude')
        )

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("nome", "cnes"),))
            .fieldset("Endereço", (("cep", "bairro"), "logradouro", ("numero", "municipio")))
            .fieldset("Geolocalização", (("latitude", "longitude"),))
        )

    def __str__(self):
        return self.nome
    
    @meta()
    def get_foto(self):
        return Image(self.foto, placeholder='/static/images/sus.png', width='auto', height='auto')
    
    @meta('Mapa')
    def get_mapa(self):
        return Map(self.latitude, self.longitude) if self.latitude and self.longitude else None
    
    @meta('Profissionais de Saúde')
    def get_profissionais_saude(self):
        return self.profissionalsaude_set.all().actions('cadastrarprofissionalsaudeunidade')

    @meta('Profissionais de Saúde')
    def get_profissionais_telessaude(self, area=None):
        qs = ProfissionalSaude.objects.filter(unidades=self)
        if area:
            qs = qs.filter(especialidade__area=area)
        return qs


class EspecialidadeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search('nome')
            .fields('cbo', 'nome', 'area', 'get_qtd_profissonais_saude')
            .filters('categoria', 'area')
            .actions('profissionaissaudeespecialidade')
        )
    

class Especialidade(models.Model):

    cbo = models.CharField(verbose_name="Código", max_length=6, unique=True)
    nome = models.CharField(max_length=150)

    area = models.ForeignKey(Area, verbose_name='Área', on_delete=models.CASCADE, null=True, blank=True)

    objects = EspecialidadeQuerySet()

    def get_profissonais_saude(self):
        return self.profissionalsaude_set.fields('pessoa_fisica', 'nucleo', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    def __str__(self):
        return "%s - %s" % (self.cbo, self.nome)


class PessoaFisicaQueryset(models.QuerySet):
    def all(self):
        return self.search("nome", "cpf").fields("nome", "cpf").filters('municipio', papel=RoleFilter('cpf'))

class PessoaFisica(models.Model):

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
    cns = models.CharField(verbose_name='CNS', max_length=15, null=True, blank=True)

    sexo = models.ForeignKey(Sexo, verbose_name='Sexo', null=True, on_delete=models.PROTECT, blank=True)

    nome_responsavel = models.CharField(verbose_name='Nome do Responsável', max_length=80, null=True, blank=True)
    cpf_responsavel = models.CharField(verbose_name='CPF do Responsável', max_length=14, null=True, blank=True)

    objects = PessoaFisicaQueryset()

    class Meta:
        icon = "users"
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("cpf", "nome"), ("data_nascimento", "nome_social"), ("sexo", "telefone"),))
            .fieldset("Dados do Responsável", (("cpf_responsavel", "nome_responsavel"),),)
            .fieldset("Endereço", (("cep", "bairro"), "endereco", ("numero", "municipio")))
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
            .fieldset("Endereço", (("cep", "bairro"), "endereco", ("numero", "municipio")))
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


class NucleoQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'gestores', 'operadores', 'get_qtd_profissonais_saude').actions('agendanucleo')


@role('g', username='gestores__cpf', nucleo='pk')
@role('o', username='operadores__cpf', nucleo='pk')
class Nucleo(models.Model):
    nome = models.CharField(verbose_name='Nome')
    gestores = models.ManyToManyField(PessoaFisica, verbose_name="Gestores", blank=True)
    operadores = models.ManyToManyField(PessoaFisica, verbose_name="Operadores", blank=True, related_name='r2')
    unidades = models.ManyToManyField(Unidade, verbose_name='Unidades Atendidas', blank=True)

    objects = NucleoQuerySet()

    class Meta:
        icon = "building-user"
        verbose_name = "Núcleo de Telesaúde"
        verbose_name_plural = "Núcleos de Telesaúde"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", ("nome", 'gestores:cadastrarpessoafisica', 'operadores:cadastrarpessoafisica'))
            .fieldset("Atuação", ("unidades",),)
        )

    def serializer(self):
        return (
            super()
            .serializer().actions('edit')
            .fieldset("Dados Gerais", ("nome", 'gestores', 'operadores'))
            .group('Detalhamento')
                .queryset('Unidades Atendidas', 'get_unidades')
                .queryset('Profissionais de Saúde', 'get_profissionais_saude')
            .parent()
        )
    
    @meta('Profissionais de Saúde')
    def get_profissionais_saude(self):
        return self.profissionalsaude_set.all().filters('especialidade').actions('cadastrarprofissionalsaudenucleo')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    @meta('Gestores')
    def get_gestores(self):
        return self.gestores.fields('cpf', 'nome')
    
    @meta('Operadores')
    def get_operadores(self):
        return self.operadores.fields('cpf', 'nome')

    @meta()
    def get_agenda(self, readonly=True):
        qs = HorarioProfissionalSaude.objects.filter(
            profissional_saude__nucleo=self, data_hora__gte=datetime.now()
        )
        start_day = qs.values_list('data_hora', flat=True).first()
        scheduler = Scheduler(start_day=start_day, readonly=True)
        campos = ("data_hora", "profissional_saude__pessoa_fisica__nome", "profissional_saude__especialidade__area__nome")
        qs1 = qs.filter(atendimentos_especialista__isnull=True)
        qs2 = qs.filter(atendimentos_especialista__isnull=False)
        horarios = {}
        for i, atendimentos in enumerate([qs1, qs2]):
            for data_hora, nome, area in atendimentos.values_list(*campos):
                if data_hora not in horarios:
                    horarios[data_hora] = []
                profissional = f'{nome} ({area.upper()} )' if area else nome
                horarios[data_hora].append(Text(profissional, color="#a4e2a4" if i==0 else "#f47c7c"))
        for data_hora, text in horarios.items():
            scheduler.append(data_hora, text, icon='stethoscope')
        return scheduler
    
    @meta('Unidades de Atuação')
    def get_unidades(self):
        return self.unidades.all()
    
    def __str__(self):
        return self.nome

class ProfissionalSaudeQueryset(models.QuerySet):
    def all(self):
        return (
            self.search("pessoa_fisica__nome", "pessoa_fisica__cpf")
            .filters("nucleo", "especialidade",)
            .fields("get_estabelecimento", "especialidade")
            .actions("agendaprofissionalsaude", "definirhorarioprofissionalsaude")
        ).cards()
@role('ps', username='pessoa_fisica__cpf')
class ProfissionalSaude(models.Model):
    pessoa_fisica = models.ForeignKey(
        PessoaFisica,
        on_delete=models.PROTECT,
        verbose_name="Pessoa Física",
    )
    registro_profissional = models.CharField(
        "Registro Profissional", max_length=30, blank=False
    )
    especialidade = models.ForeignKey(
        Especialidade, null=True, on_delete=models.CASCADE
    )
    registro_especialista = models.CharField(
        "Registro Especialista", max_length=30, blank=True, null=True
    )
    programa_provab = models.BooleanField(verbose_name='Programa PROVAB', default=False)
    programa_mais_medico = models.BooleanField(verbose_name='Programa Mais Médico', default=False)
    residente = models.BooleanField(verbose_name='Residente', default=False)
    perceptor = models.BooleanField(verbose_name='Perceptor', default=False)
    
    ativo = models.BooleanField(default=False)
    # Atenção primária
    unidade = models.ForeignKey(Unidade, verbose_name='Unidade', null=True, on_delete=models.CASCADE)
    # Teleatendimento
    nucleo = models.ForeignKey(Nucleo, verbose_name='Núcleo', null=True, on_delete=models.CASCADE)
    
    objects = ProfissionalSaudeQueryset()

    class Meta:
        icon = "stethoscope"
        verbose_name = "Profissional de Saúde"
        verbose_name_plural = "Profissionais de Saúde"
        search_fields = 'pessoa_fisica__cpf', 'pessoa_fisica__nome'

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("pessoa_fisica:cadastrarpessoafisica",),))
            .fieldset("Dados Profissionais", (("registro_profissional", "especialidade", "registro_especialista"),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
        ) if self.pk is None else (
            super()
            .formfactory()
            .fieldset("Dados Profissionais", (("registro_profissional", "especialidade", "registro_especialista"),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", (("nucleo", "pessoa_fisica"),))
            .fieldset("Dados Profissionais", (("registro_profissional", "especialidade", "registro_especialista"),),)
            .fieldset("Outras Informações", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
        )

    def __str__(self):
        return "%s (CPF: %s / CRM: %s)" % (
            self.pessoa_fisica.nome,
            self.pessoa_fisica.cpf,
            self.registro_profissional,
        )

    @meta(None)
    def get_agenda(self, readonly=True):
        scheduler = Scheduler(readonly=readonly)
        qs = self.horarioprofissionalsaude_set.filter(data_hora__gte=date.today()).order_by('data_hora')
        for data_hora, atendimento, especialista_id in qs.values_list("data_hora", "atendimentos_profissional_saude", "atendimentos_profissional_saude__especialista_id"):
            descricao, icon = ('Teleinterconsulta', 'people-group') if especialista_id else ('Teleconsulta', 'people-arrows')
            scheduler.append(data_hora, f'{descricao} #{atendimento}' if atendimento else None, icon=icon)
        for data_hora, atendimento, especialista_id in qs.values_list("data_hora", "atendimentos_especialista", "atendimentos_especialista__especialista_id"):
            if atendimento:
                descricao, icon = ('Teleinterconsulta', 'people-group') if especialista_id else ('Teleconsulta', 'people-arrows')
                scheduler.append(data_hora, f'{descricao} #{atendimento}' if atendimento else None, icon=icon)
        qs2 = HorarioProfissionalSaude.objects.filter(data_hora__gte=date.today(),profissional_saude__pessoa_fisica__cpf=self.pessoa_fisica.cpf
        ).exclude(profissional_saude=self.pk)
        for data_hora, nucleo in qs2.values_list("data_hora", "profissional_saude__nucleo__nome"):
            scheduler.append(data_hora, nucleo, icon='x')
        return scheduler

    @meta('Estabelecimento')
    def get_estabelecimento(self):
        return self.nucleo if self.nucleo_id else self.unidade


class HorarioProfissionalQuerySet(models.QuerySet):
    def disponiveis(self):
        return self.filter(
            atendimentos_profissional_saude__isnull=True,
            atendimentos_especialista__isnull=True,
            data_hora__gte=datetime.now()
        )


class HorarioProfissionalSaude(models.Model):
    profissional_saude = models.ForeignKey(
        ProfissionalSaude,
        verbose_name="Profissional de Saúde",
        on_delete=models.CASCADE,
    )
    data_hora = models.DateTimeField(verbose_name="Data/Hora")

    objects = HorarioProfissionalQuerySet()

    class Meta:
        verbose_name = "Horário de Atendimento"
        verbose_name_plural = "Horários de Atendimento"

    def __str__(self):
        return "{}".format(
            self.data_hora.strftime("%d/%m/%Y %H:%M")
        )



class AtendimentoQuerySet(models.QuerySet):
    def all(self):
        return (
            self.filters("area", "unidade", "paciente", "profissional", "especialista")
            .fields(
                ("area", "agendado_para", "tipo"),
                ("unidade", "profissional", "paciente"),
                "especialista", "get_tags"
            ).limit(5).order_by('-id')
        )
    
    def proximos(self):
        return self.filter(agendado_para__gte=datetime.now())
    
    @meta('Total de Atendimentos')
    def get_total(self):
        return self.total()
    
    @meta('Profissionais Envolvidos')
    def get_total_profissioinais(self):
        return self.total('profissional')
    
    @meta('Pacientes Atendidos')
    def get_total_pacientes(self):
        return self.total('paciente')
    
    @meta('Total por Tipo de Atendimento')
    def get_total_por_tipo(self):
        return self.counter('tipo', chart='bar')
    
    @meta('Total por Especialidade')
    def get_total_por_area(self):
        return self.counter('area', chart='donut')
    
    @meta('Total por Mês')
    def get_total_por_mes(self):
        return self.counter('agendado_para__month', chart='line')
    
    @meta('Atendimentos por Unidade e Especialidade')
    def get_total_por_area_e_unidade(self):
        return self.counter('area', 'unidade')

@role('p', username='paciente__cpf')
class Atendimento(models.Model):
    profissional = models.ForeignKey(
        ProfissionalSaude,
        verbose_name='Profissional Responsável',
        related_name="atendimentos_profissional",
        on_delete=models.CASCADE,
        null=True, pick=True,
    )
    unidade = models.ForeignKey(
        Unidade, null=True, on_delete=models.CASCADE
    )
    especialista = models.ForeignKey(
        ProfissionalSaude,
        related_name="atendimentos_especialista",
        on_delete=models.CASCADE,
        null=True, blank=True, pick = True,
        help_text='Profissional de saúde que será consultado pelo profissional responsável pelo atendimento'
    )

    area = models.ForeignKey(
        Area, verbose_name='Área', on_delete=models.CASCADE, pick=True
    )

    tipo = models.ForeignKey(
        TipoAtendimento, verbose_name='Tipo de Atendimento', on_delete=models.CASCADE, pick=True
    )

    cid = models.ManyToManyField(CID, verbose_name='CID')
    ciap = models.ManyToManyField(CIAP, verbose_name='CIAP')

    data = models.DateTimeField(blank=True)
    assunto = models.CharField(verbose_name='Motivo',max_length=200)
    duvida = models.TextField(verbose_name='Dúvida/Queixa', max_length=2000)
    paciente = models.ForeignKey(
        "PessoaFisica", verbose_name='Paciente', related_name="atendimentos_paciente", on_delete=models.PROTECT
    )
    duracao = models.IntegerField(verbose_name='Duração', null=True, choices=[(30, '30min'), (60, '1h'), (90, '1h30min')], pick=True)

    # horario_profissional_saude = models.ForeignKey(
    #     HorarioProfissionalSaude,
    #     verbose_name="Horário",
    #     on_delete=models.SET_NULL,
    #     null=True, pick=True
    # )
    # horario_especialista = models.ForeignKey(
    #     HorarioProfissionalSaude,
    #     verbose_name="Horário",
    #     on_delete=models.SET_NULL,
    #     null=True, related_name='atendimento2'
    # )
    horarios_profissional_saude = models.ManyToManyField(HorarioProfissionalSaude, verbose_name='Horários', blank=True, related_name='atendimentos_profissional_saude', pick=True)
    horarios_especialista = models.ManyToManyField(HorarioProfissionalSaude, verbose_name='Horários', blank=True, related_name='atendimentos_especialista', pick=True)
    horario_excepcional = models.BooleanField(
        verbose_name="Horário Excepcional",
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
    finalizado_em = models.DateTimeField(verbose_name='Data de Término', null=True, blank=True)

    motivo_cancelamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)
    motivo_reagendamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)

    numero_webconf = models.CharField(verbose_name='Número da WebConf', null=True)
    senha_webconf = models.CharField(verbose_name='Senha da WebConf', null=True)
    limite_webconf = models.DateTimeField(verbose_name='Limite da WebConf', null=True)

    termo_assinado_paciente = models.BooleanField(verbose_name='Termo assinado pelo Paciente', default=False)
    termo_assinado_profissional = models.BooleanField(verbose_name='Termo assinado pelo Profissional', default=False)
    termo_assinado_especialista = models.BooleanField(verbose_name='Termo assinado pelo Especialista', default=False)

    objects = AtendimentoQuerySet()

    class Meta:
        icon = "laptop-file"
        verbose_name = "Teleconsulta"
        verbose_name_plural = "Teleconsultas"

    def is_termo_assinado_por(self, user):
        if self.paciente.cpf == user.username:
            return self.termo_assinado_paciente
        if self.profissional.pessoa_fisica.cpf == user.username:
            return self.termo_assinado_profissional
        if self.especialista.pessoa_fisica.cpf == user.username:
            return self.termo_assinado_especialista
        return False
    
    def assinar_termo(self, user):
        if self.paciente.cpf == user.username:
            self.termo_assinado_paciente = True
        if self.profissional.pessoa_fisica.cpf == user.username:
            self.termo_assinado_profissional = True
        if self.especialista.pessoa_fisica.cpf == user.username:
            self.termo_assinado_especialista = True
        self.save()

    def check_webconf(self):
        from . import zoom
        if self.limite_webconf is None or self.limite_webconf < datetime.now():
            number, password, limit = zoom.create_meeting('Atendimento #{}'.format(self.id))
            self.numero_webconf = number
            self.senha_webconf = password
            self.limite_webconf = limit
            self.save()

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset(
                "Dados Gerais",
                (
                    "unidade", "tipo", "area",
                ),
            )
            .fieldset(
                "Detalhamento",
                (
                    "paciente:cadastrarpessoafisica",
                    "assunto",
                    "duvida",
                    ("cid", "ciap"),
                ),
            )
            .fieldset(
                "Agendamento",
                (
                    "profissional:consultaragenda",
                    "especialista",
                    "horarios_profissional_saude",
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
            .actions('salavirtual', 'finalizaratendimento', 'enviarnotificacaoatendimento')
            .fieldset(
                "Dados Gerais",
                (
                    ("tipo", "unidade", "unidade__municipio"),
                    ("agendado_para", "finalizado_em", "duracao_webconf"),
                ) 
            )
            .fieldset("Web Conferência", (("numero_webconf", "senha_webconf", "limite_webconf"),), roles=('su',))
            .group().actions('anexararquivo', 'registrarecanminhamentoscondutas')
                .section('Detalhamento')
                    .fieldset(
                        "Dados do Paciente", (
                            ("nome", "cpf"),
                            ("data_nascimento", "sexo")
                        ), attr="paciente"
                    )
                    .fieldset(
                        "Dados do Responsável", (
                            ("pessoa_fisica__nome", "pessoa_fisica__cpf"),
                            ("registro_profissional", "especialidade", "registro_especialista"),
                        ), attr="profissional"
                    )
                    .fieldset(
                        "Dados do Especialista", (
                            ("pessoa_fisica__nome", "pessoa_fisica__cpf"),
                            ("especialidade", "registro_especialista"),
                        ), attr="especialista", condition='especialista'
                    )
                    .fieldset(
                        "Dados da Consulta", (
                            ("assunto", "area"),
                            "duvida",
                            ("cid", "ciap"),
                        )
                    )
                .parent()
                .queryset('Anexos', 'get_anexos')
                .queryset('Encaminhamentos', 'get_condutas_ecaminhamentos', roles=('ps',))
            .parent()
        )
    
    @meta('Número')
    def get_numero(self):
        return self.id
    
    @meta()
    def get_tags(self):
        tags = []
        if self.tipo_id == TipoAtendimento.TELETERCONSULTA:
            color = "#265890"
            icon = 'people-group'
        else:
            color = '#5ca05d'
            icon = 'people-arrows'
        tag = Badge(color, self.tipo, icon=icon)
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
    
    @meta('Anexos')
    def get_anexos(self):
        return self.anexoatendimento_set.fields('get_nome_arquivo', 'autor', 'get_arquivo')
    
    @meta('Anexos')
    def get_anexos_webconf(self):
        return self.get_anexos().reloadable()
    
    @meta('Encaminhamentos e Condutas')
    def get_condutas_ecaminhamentos(self):
        return self.encaminhamentoscondutas_set.fields(
            'data', 'subjetivo', 'objetivo', 'avaliacao', 'plano', 'comentario', 'encaminhamento', 'conduta'
        ).timeline()

    @meta('Duração')
    def duracao_webconf(self):
        if self.finalizado_em and self.agendado_para:
            return timesince(self.agendado_para, self.finalizado_em)
        return "-"
    
    @meta()
    def get_termo_consentimento(self):
        return TemplateContent('termo_consentimento.html', dict(atendimento=self))

    def get_agendado_para(self):
        return Badge("#5ca05d", self.agendado_para.strftime('%d/%m/%Y %H:%M'), icon='clock')

    def __str__(self):
        return "%s - %s" % (self.id, self.assunto)

    def save(self, *args, **kwargs):
        if not self.data:
            self.data = timezone.now()
        super(Atendimento, self).save(*args, **kwargs)

    def post_save(self):
        # tele-interconsulta marcada pelo regulador ou tele-interconsultor
        if self.especialista_id and not self.horarios_especialista.exists():
            for horario in self.horarios_profissional_saude.all():
                self.horarios_especialista.add(self.especialista.horarioprofissionalsaude_set.get(
                    data_hora=horario.data_hora
                ))
        # tele-interconsulta marcada pelo profissional de saúde
        if self.especialista_id and not self.horarios_profissional_saude.exists():
            for horario in self.horarios_especialista.all():
                horario_profissional = self.profissional.horarioprofissionalsaude_set.filter(data_hora=horario.data_hora).first()
                if horario_profissional is None:
                    horario_profissional = HorarioProfissionalSaude.objects.create(data_hora=horario.data_hora, profissional_saude=self.profissional)
                self.horarios_profissional_saude.add(horario_profissional)
        if not self.agendado_para and self.horarios_profissional_saude.exists():
            self.agendado_para = self.horarios_profissional_saude.order_by('data_hora').first().data_hora
            self.save()

class AnexoAtendimento(models.Model):
    atendimento = models.ForeignKey(
        Atendimento, on_delete=models.CASCADE
    )
    nome = models.CharField(verbose_name='Nome', default='')
    arquivo = models.FileField(max_length=200, upload_to="anexos_teleconsuta")
    autor = models.ForeignKey(PessoaFisica, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Anexo de Solicitação"
        verbose_name_plural = "Anexos de Solicitação"

    def __str__(self):
        return "%s" % self.atendimento

    @meta('Nome do Arquivo')
    def get_nome_arquivo(self):
        return self.nome
    
    def get_arquivo(self):
        return FileLink(self.arquivo, icon='file', modal=True)

class AvaliacaoAtendimento(models.Model):
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

    atendimento = models.ForeignKey(Atendimento, on_delete=models.PROTECT)

    satisfacao = models.IntegerField(verbose_name='Grau de Satisfação', choices=SATISFACAO)
    respondeu_duvida = models.IntegerField(verbose_name='Respondeu a Dúvida/Problema', choices=RESPONDEU_DUVIDA)
    evitou_encaminhamento = models.IntegerField(verbose_name='Evitou Encaminhamento', choices=EVITOU_ENCAMINHAMENTO)
    mudou_conduta = models.IntegerField(verbose_name='Mudou Conduta', choices=MUDOU_CONDUTA)
    recomendaria = models.BooleanField(verbose_name='Recomendaria', choices=SIM_NAO_CHOICES, default=None)
    data = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Avaliação de Solicitação"
        verbose_name_plural = "Avaliações de Solicitação"


class EncaminhamentosCondutas(models.Model):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE)
    responsavel = models.ForeignKey(ProfissionalSaude, on_delete=models.CASCADE)

    # Método SOAP - Subjetivo, Objetivo, Avaliação, Plano
    subjetivo = models.TextField(verbose_name='S - subjetivo', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro da parte subjetiva da anamnese da consulta, ou seja, os dados dos sentimentos e percepções do cidadão em relação à sua saúde.')
    objetivo = models.TextField(verbose_name='O - objetivo', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro do exame físico, como os sinais e sintomas detectados, além do registro de resultados de exames realizados.')
    avaliacao = models.TextField(verbose_name='A - avaliacao', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro da conclusão feita pelo profissional de saúde a partir dos dados observados nos itens anteriores, como os motivos para aquele encontro, a anamnese do cidadão e dos exames físico e complementares.')
    plano = models.TextField(verbose_name='P - Plano', blank=True, null=True, help_text='Conjunto de funcionalidades que permite registrar o plano de cuidado ao cidadão em relação ao(s) problema(s) avaliado(s).')

    data = models.DateTimeField(auto_now_add=True)

    comentario = models.TextField(blank=True)
    encaminhamento = models.TextField(blank=True, null=True)
    conduta = models.TextField(blank=True, null=True)

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
