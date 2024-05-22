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


class AreaQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'get_qtd_profissonais_saude').actions('profissionaissaudearea', 'agendaarea')


class Area(models.Model):
    nome = models.CharField(max_length=60, unique=True)

    objects = AreaQuerySet()

    class Meta:
        ordering = ("nome",)
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def get_profissonais_saude(self):
        return ProfissionalSaude.objects.filter(especialidade__area=self).fields('pessoa_fisica', 'uo', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.get_profissonais_saude().count()
    
    @meta()
    def get_agenda(self, readonly=True):
        qs = HorarioProfissionalSaude.objects.filter(
            profissional_saude__especialidade__area=self
        ).order_by('data_hora')
        start_day = qs.values_list('data_hora', flat=True).first()
        scheduler = Scheduler(start_day=start_day, readonly=True)
        qs = qs.filter(data_hora__lt=scheduler.end_day)
        campos = ("data_hora", "profissional_saude__pessoa_fisica__nome", "profissional_saude__especialidade__area__nome")
        qs1 = qs.filter(atendimento__isnull=True)
        qs2 = qs.filter(atendimento__isnull=False)
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
    codigo = models.CharField(max_length=2, unique=True)
    sigla = models.CharField(max_length=2, unique=True)
    nome = models.CharField(max_length=60, unique=True)

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
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=7, unique=True)
    nome = models.CharField(max_length=60)

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
            .filters("municipio").actions('agendaunidade', 'equipeunidade').cards()
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

    logradouro = models.CharField(max_length=120, null=True)
    numero = models.CharField(max_length=10, null=True)
    bairro = models.CharField(max_length=40, null=True)
    cep = models.CharField(max_length=10, null=True)

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
            .fieldset("Dados Gerais", ("nome", ("cnes", "municipio")))
            .fieldset("Endereço", ("logradouro", ("numero", "bairro", "cep")))
            .fieldset("Geolocalização", (("latitude", "longitude"), 'get_mapa'))
        )

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", ("foto", "nome", ("cnes", "municipio")))
            .fieldset("Endereço", ("logradouro", ("numero", "bairro", "cep")))
            .fieldset("Geolocalização", (("latitude", "longitude"),))
        )

    def __str__(self):
        return self.nome
    
    @meta()
    def get_foto(self):
        return Image(self.foto, placeholder='/static/images/sus.png', width='auto', height='auto')
    
    def get_mapa(self):
        return Map(self.latitude, self.longitude)


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
        return self.profissionalsaude_set.fields('pessoa_fisica', 'uo', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    def __str__(self):
        return "%s - %s" % (self.cbo, self.nome)


class PessoaFisicaQueryset(models.QuerySet):
    def all(self):
        return self.search("nome", "cpf").fields("nome", "cpf")

@role('pf', username='cpf')
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

    objects = PessoaFisicaQueryset()

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


class UnidadeOrganizacionalQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'gestores', 'operadores', 'get_qtd_profissonais_saude')


@role('g', username='gestores__cpf', uo='pk')
@role('o', username='operadores__cpf', uo='pk')
class UnidadeOrganizacional(models.Model):
    nome = models.CharField(verbose_name='Nome')
    gestores = models.ManyToManyField(PessoaFisica, verbose_name="Gestores", blank=True)
    operadores = models.ManyToManyField(PessoaFisica, verbose_name="Operadores", blank=True, related_name='r2')

    # Atuação
    estados = models.ManyToManyField(Estado, verbose_name='Estados', blank=True)
    municipios = models.ManyToManyField(Municipio, verbose_name='Municípios', blank=True)
    unidades = models.ManyToManyField(Unidade, verbose_name='Unidades', blank=True)

    objects = UnidadeOrganizacionalQuerySet()

    class Meta:
        icon = "building-user"
        verbose_name = "Unidade Organizacional"
        verbose_name_plural = "Unidades Organizacionais"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", ("nome", 'gestores:cadastrarpessoafisica', 'operadores:cadastrarpessoafisica'))
            .fieldset("Atuação", ("estados", "municipios", "unidades",),)
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", ("nome", 'gestores'))
            .fieldset("Atuação", ("estados", "municipios", "unidades",),)
            .queryset('Profissionais de Saúde', 'get_profissionais_saude')
        )
    
    @meta('Profissionais de Saúde')
    def get_profissionais_saude(self):
        return self.profissionalsaude_set.all().filters('especialidade', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    @meta('Gestores')
    def get_gestores(self):
        return self.gestores.all()
    
    @meta('Operadores')
    def get_operadores(self):
        return self.operadores.all()

    @meta()
    def get_agenda(self, readonly=True):
        qs = HorarioProfissionalSaude.objects.filter(
            profissional_saude__unidade_organizacional=self
        )
        start_day = qs.values_list('data_hora', flat=True).first()
        scheduler = Scheduler(start_day=start_day, readonly=True)
        campos = ("data_hora", "profissional_saude__pessoa_fisica__nome", "profissional_saude__especialidade__area__nome")
        qs1 = qs.filter(atendimento__isnull=True)
        qs2 = qs.filter(atendimento__isnull=False)
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
    
    def __str__(self):
        return self.nome

class ProfissionalSaudeQueryset(models.QuerySet):
    def all(self):
        return (
            self.search("pessoa_fisica__nome", "pessoa_fisica__cpf")
            .filters(
                "uo",
                "especialidade",
            )
            .fields(
                ("uo", "especialidade"), 'get_tags',
            )
            .actions("agendaprofissionalsaude", "definirhorarioprofissionalsaude")
        ).cards()
@role('ps', username='pessoa_fisica__cpf', uo='uo')
class ProfissionalSaude(models.Model):
    pessoa_fisica = models.ForeignKey(
        PessoaFisica,
        on_delete=models.PROTECT,
        verbose_name="Profissional",
    )
    uo = models.ForeignKey(
        UnidadeOrganizacional,
        verbose_name='Unidade Organizacional',
        null=True,
        on_delete=models.CASCADE,
    )
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

    teleconsultor = models.BooleanField(verbose_name='Teleconsultor', default=True)
    teleinterconsultor = models.BooleanField(verbose_name='Teleinterconsultor', default=True)

    objects = ProfissionalSaudeQueryset()

    class Meta:
        icon = "stethoscope"
        verbose_name = "Vínculo Profissional"
        verbose_name_plural = "Vínculos Profissionais"
        search_fields = 'pessoa_fisica__cpf', 'pessoa_fisica__nome'

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("uo", "pessoa_fisica:cadastrarpessoafisica"),))
            .fieldset(
                "Dados Profissionais",
                (("registro_profissional", "especialidade", "registro_especialista"),),
            )
            .fieldset(
                "Informações Adicionais",
                (
                    ("programa_provab", "programa_mais_medico"),
                    ("residente", "perceptor"),
                ),
            )
            .fieldset("Atuação", (("teleconsultor", "teleinterconsultor"),))
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", (("uo", "pessoa_fisica"),))
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
            .fieldset("Atuação", (("teleconsultor", "teleinterconsultor"),))
            .fieldset("Agenda dos Próximos Dias", ("get_agenda",))
        )

    def __str__(self):
        return "%s (CPF: %s / CRM: %s)" % (
            self.pessoa_fisica.nome,
            self.pessoa_fisica.cpf,
            self.registro_profissional,
        )
    
    @meta()
    def get_tags(self):
        tags = []
        if self.teleconsultor:
            tags.append(Badge('#265890', 'Teleconsultor', 'people-group'))
        if self.teleinterconsultor:
            tags.append(Badge('#5ca05d', 'Teleinterconsultor', 'people-arrows'))
        return tags

    @meta(None)
    def get_agenda(self, readonly=True):
        qs = self.horarioprofissionalsaude_set.filter(data_hora__gte=date.today()).order_by('data_hora')
        scheduler = Scheduler(
            readonly=readonly,
        )
        for data_hora, atendimento in qs.values_list("data_hora", "atendimento"):
            scheduler.append(data_hora, f'Solicitação #{atendimento}' if atendimento else None, icon='stethoscope')
        qs2 = HorarioProfissionalSaude.objects.filter(
            data_hora__gte=date.today(),
            profissional_saude__pessoa_fisica__cpf=self.pessoa_fisica.cpf
        ).exclude(profissional_saude=self.pk)
        for data_hora, uo in qs2.values_list("data_hora", "profissional_saude__uo__nome"):
            scheduler.append(data_hora, uo, icon='x')
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
        return "{}".format(
            self.data_hora.strftime("%d/%m/%Y %H:%M")
        )



class AtendimentoQuerySet(models.QuerySet):
    def all(self):
        return (
            self.filters("area", "unidade", "paciente", "profissional", "especialista")
            .calendar("agendado_para")
            .fields(
                ("area", "agendado_para", "tipo"),
                ("unidade", "profissional", "paciente"),
                "especialista", "get_tags"
            ).limit(5).order_by('-id')
        )
    
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
    def get_total_por_area_(self):
        return self.counter('area', chart='donut')
    
    @meta('Total por Mês')
    def get_total_por_mes(self):
        return self.counter('agendado_para__month', chart='line')
    
    @meta('Atendimentos por Especialidade e Unidade')
    def get_total_por_area_e_unidade(self):
        return self.counter('area', 'unidade')


class Atendimento(models.Model):
    profissional = models.ForeignKey(
        ProfissionalSaude,
        verbose_name='Responsável',
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
        null=True,
        blank=True,
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
    assunto = models.CharField(verbose_name='Assunto',max_length=200)
    duvida = models.TextField(verbose_name='Dúvida/Queixa', max_length=2000)
    paciente = models.ForeignKey(
        "PessoaFisica", verbose_name='Paciente', related_name="atendimentos_paciente", on_delete=models.PROTECT
    )
    duracao = models.IntegerField(verbose_name='Duração', null=True)

    horario_profissional_saude = models.ForeignKey(
        HorarioProfissionalSaude,
        verbose_name="Horário",
        on_delete=models.SET_NULL,
        null=True, pick=True
    )
    horario_especialista = models.ForeignKey(
        HorarioProfissionalSaude,
        verbose_name="Horário",
        on_delete=models.SET_NULL,
        null=True, related_name='r2'
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

    motivo_cancelamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)
    motivo_reagendamento = models.TextField(verbose_name='Motivo do Cancelamento', null=True)

    numero_webconf = models.CharField(verbose_name='Número da WebConf', null=True)
    senha_webconf = models.CharField(verbose_name='Senha da WebConf', null=True)
    limite_webconf = models.DateTimeField(verbose_name='Limite da WebConf', null=True)

    objects = AtendimentoQuerySet()

    class Meta:
        icon = "laptop-file"
        verbose_name = "Teleconsulta"
        verbose_name_plural = "Teleconsultas"

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
            .actions('salavirtual')
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
                .queryset('Encaminhamentos/Condutas', 'get_condutas_ecaminhamentos', roles=('ps',))
            .parent()
        )
    
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
        return self.encaminhamentoscondutas_set.fields('data', 'subjetivo', 'objetivo', 'plano').timeline()

    @meta('Duração')
    def duracao_webconf(self):
        if self.finalizado_em and self.agendado_para:
            return timesince(self.agendado_para, self.finalizado_em)
        return "-"


    def __str__(self):
        return "%s - %s" % (self.id, self.assunto)

    def save(self, *args, **kwargs):
        if not self.agendado_para and self.horario_profissional_saude_id:
            self.agendado_para = self.horario_profissional_saude.data_hora
        if not self.data:
            self.data = timezone.now()

        super(Atendimento, self).save(*args, **kwargs)


class AnexoAtendimento(models.Model):
    atendimento = models.ForeignKey(
        Atendimento, on_delete=models.CASCADE
    )
    arquivo = models.FileField(max_length=200, upload_to="anexos_teleconsuta")
    autor = models.ForeignKey(PessoaFisica, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Anexo de Solicitação"
        verbose_name_plural = "Anexos de Solicitação"

    def __str__(self):
        return "%s" % self.atendimento

    @meta('Nome do Arquivo')
    def get_nome_arquivo(self):
        return self.arquivo.name.split("/")[-1]
    
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
