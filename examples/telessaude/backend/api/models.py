import os
import hashlib
import base64
from uuid import uuid1
from PIL import Image as PILImage
import requests
from django.conf import settings
from slth.factory import FormFactory
from slth.serializer import Serializer
from . import signer
from random import randint
from datetime import date, datetime, timedelta, time
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from slth import printer
from django.core.files.base import ContentFile
from django.core.signing import Signer
from slth.db import models, meta, role
from slth.models import User, RoleFilter
from slth.components import Scheduler, FileLink, WebConf, Image, Map, Text, Badge, TemplateContent
from time import sleep
from slth.printer import qrcode_base64


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
    TELE_INTERCONSULTA = 2
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


class ConselhoClasse(models.Model):
    sigla = models.CharField(verbose_name='Sigla', max_length=20, unique=True)
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Conselho de Classe"
        verbose_name_plural = "Conselhos de Classe"
        ordering = ["sigla"]

    def __str__(self):
        return f'{self.sigla}/{self.estado.sigla}'


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
        return "%s/%s" % (self.nome, self.estado.sigla)


class UnidadeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search("cnes", "nome")
            .fields("foto", "get_qtd_profissionais_saude")
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
        return self.profissionalsaude_set.all().actions('cadastrarprofissionalsaudeunidade', 'editarprofissionalsaude', 'visualizarprofissionalsaude')
    
    @meta('Quantidade de Profissionais')
    def get_qtd_profissionais_saude(self):
        return self.profissionalsaude_set.count()
    

class EspecialidadeQuerySet(models.QuerySet):
    def all(self):
        return (
            self.search('nome')
            .fields('cbo', 'nome', 'area', 'get_qtd_profissonais_saude')
            .filters('categoria', 'area')
            .actions('profissionaissaudeespecialidade')
        )
    

class Especialidade(models.Model):

    cbo = models.CharField(verbose_name="Código", max_length=6, null=True, blank=True)
    nome = models.CharField(max_length=150)

    area = models.ForeignKey(Area, verbose_name='Área', on_delete=models.CASCADE, null=True, blank=True)

    objects = EspecialidadeQuerySet()

    def get_profissonais_saude(self):
        return self.profissionalsaude_set.fields('pessoa_fisica', 'nucleo', 'get_tags')
    
    @meta('Qtd. de Profissionais')
    def get_qtd_profissonais_saude(self):
        return self.profissionalsaude_set.count()

    def __str__(self):
        return self.nome


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

    sexo = models.ForeignKey(Sexo, verbose_name='Sexo', null=True, on_delete=models.PROTECT, blank=True, pick=True)

    nome_responsavel = models.CharField(verbose_name='Nome do Responsável', max_length=80, null=True, blank=True)
    cpf_responsavel = models.CharField(verbose_name='CPF do Responsável', max_length=14, null=True, blank=True)

    email = models.CharField(verbose_name='E-mail', null=True, blank=True)
    telefone = models.CharField(verbose_name='Telefone', null=True, blank=True)

    objects = PessoaFisicaQueryset()

    class Meta:
        icon = "users"
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("cpf", "nome"), ("data_nascimento", "nome_social"), "sexo",))
            .fieldset("Dados de Contato", (("email", "telefone"),))
            .fieldset("Dados do Responsável", (("cpf_responsavel", "nome_responsavel"),),)
            .fieldset("Endereço", (("cep", "bairro"), "endereco", ("numero", "municipio")))
        )

    def serializer(self):
        return (
            super()
            .serializer()
            .fieldset("Dados Gerais", (("nome", "nome_social"), ("cpf", "data_nascimento"), ("sexo", "telefone"),),)
            .fieldset("Dados de Contato", (("email", "telefone"),))
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

    def get_idade(self):
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
        
    def get_endereco(self):
        if self.endereco:
            endereco = [self.endereco]
            if self.numero: endereco.append(self.numero)
            if self.bairro: endereco.append(self.bairro)
            if self.cep: endereco.append(self.cep)
            if self.municipio: endereco.append(str(self.municipio))
            if self.complemento: endereco.append(self.complemento)
            return ', '.join(endereco)
        return None


class NucleoQuerySet(models.QuerySet):
    def all(self):
        return self.fields('nome', 'gestores', 'operadores', 'get_qtd_profissonais_saude').actions('agendanucleo').cards()


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
        scheduler = Scheduler(start_day=start_day, chucks=3, readonly=True)
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
        return self.unidades.all().actions('visualizarunidade', 'editarunidade')
    
    def __str__(self):
        return self.nome  

class ProfissionalSaudeQueryset(models.QuerySet):
    def all(self):
        return (
            self.search("pessoa_fisica__nome", "pessoa_fisica__cpf")
            .filters("nucleo", "unidade", "especialidade",)
            .fields("get_estabelecimento", "especialidade")
            .actions('definirhorarioprofissionalsaude')
        ).cards()

@role('ps', username='pessoa_fisica__cpf')
class ProfissionalSaude(models.Model):
    pessoa_fisica = models.ForeignKey(
        PessoaFisica,
        on_delete=models.PROTECT,
        verbose_name="Pessoa Física",
    )
    registro_profissional = models.CharField(
        "Nº do Registro Profissional", max_length=30, blank=False
    )
    conselho_profissional = models.ForeignKey(
       ConselhoClasse, verbose_name="Conselho Profissional", blank=False, null=True
    )
    especialidade = models.ForeignKey(
        Especialidade, null=True, on_delete=models.CASCADE
    )
    registro_especialista = models.CharField(
        "Nº do Registro de Especialista", max_length=30, blank=True, null=True
    )
    conselho_especialista = models.ForeignKey(
       ConselhoClasse, verbose_name="Conselho de Especialista", blank=True, null=True, related_name='r3'
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

    # Zoom token
    zoom_token = models.TextField(verbose_name='Zoom Token', null=True, blank=True)

    objects = ProfissionalSaudeQueryset()

    class Meta:
        icon = "stethoscope"
        verbose_name = "Profissional de Saúde"
        verbose_name_plural = "Profissionais de Saúde"
        search_fields = 'pessoa_fisica__cpf', 'pessoa_fisica__nome'

    def assinar_arquivo_pdf(self, caminho_arquivo, token):
        url = 'https://certificado.vidaas.com.br/valid/api/v1/trusted-services/signatures'
        filename = caminho_arquivo.split('/')[-1]
        filecontent = open(caminho_arquivo, 'r+b').read()
        base64_content = base64.b64encode(filecontent).decode()
        sha256 = hashlib.sha256()
        sha256.update(filecontent)
        hash=sha256.hexdigest()
        headers = {'Content-type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
        data = {"hashes": [{"id": filename, "alias": filename, "hash": hash, "hash_algorithm": "2.16.840.1.101.3.4.2.1", "signature_format": "CAdES_AD_RB", "base64_content": base64_content,}]}
        response = requests.post(url, json=data, headers=headers).json()
        file_content=base64.b64decode(response['signatures'][0]['file_base64_signed'].replace('\r\n', ''))
        open(caminho_arquivo, 'w+b').write(file_content)

    def assinar_arquivo_imagem(self, caminho_arquivo):
        caminho_arquivo_pdf = f'{caminho_arquivo}.pdf'
        PILImage.open(caminho_arquivo).save(caminho_arquivo_pdf, "PDF")
        self.assinar_arquivo_pdf(caminho_arquivo_pdf)

    def configurar_zoom(self, authorization_code, redirect_url):
        url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri={}'.format(authorization_code, redirect_url)
        auth = base64.b64encode('{}:{}'.format(os.environ.get('ZOOM_API_KEY'), os.environ.get('ZOOM_API_SEC')).encode()).decode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic {}".format(auth)}
        response = requests.post(url, headers=headers).json()
        self.zoom_token = response['refresh_token']
        self.save()

    def criar_sala_virtual(self, nome):
        if self.zoom_token:
            url = 'https://zoom.us/oauth/token?grant_type=refresh_token&refresh_token={}'.format(self.zoom_token)
            auth = base64.b64encode('{}:{}'.format(os.environ.get('ZOOM_API_KEY'), os.environ.get('ZOOM_API_SEC')).encode()).decode()
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic {}".format(auth)}
            response = requests.post(url, headers=headers).json()
            print(response)
            self.zoom_token = response['refresh_token']
            self.save()
            data = {"topic": nome, "settings": {"join_before_host": True}}
            url = 'https://api.zoom.us/v2/users/me/meetings'
            headers = {'authorization': 'Bearer ' + response['access_token'], 'content-type': 'application/json'}
            print(url, data)
            response = requests.post(url, json=data, headers=headers).json()
            print(response)
            number = response.get('id')
            password = response.get('encrypted_password')
            limit = datetime.now() + timedelta(minutes=40)
        return number, password, limit

    def formfactory(self):
        return (
            super()
            .formfactory()
            .fieldset("Dados Gerais", (("pessoa_fisica:cadastrarpessoafisica",),))
            .fieldset("Dados Profissionais", ("especialidade", ("conselho_profissional", "registro_profissional"), ("conselho_especialista", "registro_especialista",),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
        ) if self.pk is None else (
            super()
            .formfactory()
            .fieldset("Dados Profissionais", ("especialidade", ("conselho_profissional", "registro_profissional"), ("conselho_especialista", "registro_especialista"),),)
            .fieldset("Informações Adicionais", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
        )


    def serializer(self):
        return (
            super()
            .serializer()
            .actions("agendaprofissionalsaude", "alteraragendaprofissionalsaude", "definirhorarioprofissionalsaude", "editarprofissionalsaude")
            .fieldset("Dados Gerais", (("pessoa_fisica"),))
            .fieldset("Dados Profissionais", (("especialidade", "get_estabelecimento"), ("conselho_profissional", "registro_profissional"), ("conselho_especialista", "registro_especialista"),),)
            .group()
                .fieldset("Outras Informações", (("programa_provab", "programa_mais_medico"), ("residente", "perceptor"),),)
                .fieldset("Horário de Atendimento", ("get_horarios_atendimento",))
                .fieldset("Agenda", ("get_agenda",))
            .parent()
            #.fieldset("Configuração", ("zoom_token",))
        )

    def __str__(self):
        return "%s (CPF: %s / CRM: %s)" % (
            self.pessoa_fisica.nome,
            self.pessoa_fisica.cpf,
            self.get_registro_profissional(),
        )

    def get_registro_profissional(self):
        return f'{self.conselho_profissional} {self.registro_profissional}'
    
    def get_registro_especialista(self):
        return f'{self.conselho_especialista} {self.registro_especialista}' if self.conselho_especialista else None
    
    def pode_realizar_atendimento(self, data_hora, duracao):
        disponivel = self.horarioprofissionalsaude_set.filter(data_hora=data_hora).disponiveis().exists()
        if disponivel and duracao >= 40:
            disponivel = self.horarioprofissionalsaude_set.filter(data_hora=data_hora + timedelta(minutes=20)).disponiveis().exists()
            if disponivel and duracao == 60:
                disponivel = self.horarioprofissionalsaude_set.filter(data_hora=data_hora + timedelta(minutes=40)).disponiveis().exists()
        return disponivel

    @meta(None)
    def get_agenda(self, readonly=True, single_selection=False, available=True):
        scheduler = Scheduler(readonly=readonly, chucks=3, single_selection=single_selection)
        qs = self.horarioprofissionalsaude_set.filter(data_hora__gte=date.today()).order_by('data_hora')
        for data_hora, atendimento, especialista_id in qs.values_list("data_hora", "atendimentos_profissional_saude", "atendimentos_profissional_saude__especialista_id"):
            descricao, icon = ('Teleinterconsulta', 'people-group') if especialista_id else ('Teleconsulta', 'people-arrows')
            if atendimento or available:
                scheduler.append(data_hora, f'{descricao} {atendimento}' if atendimento else None, icon=icon)
        for data_hora, atendimento, especialista_id in qs.values_list("data_hora", "atendimentos_especialista", "atendimentos_especialista__especialista_id"):
            if atendimento:
                descricao, icon = ('Teleinterconsulta', 'people-group') if especialista_id else ('Teleconsulta', 'people-arrows')
                if available:
                    scheduler.append(data_hora, f'{descricao} #{atendimento}' if atendimento else None, icon=icon)
        qs2 = HorarioProfissionalSaude.objects.filter(data_hora__gte=date.today(),profissional_saude__pessoa_fisica__cpf=self.pessoa_fisica.cpf
        ).exclude(profissional_saude=self.pk)
        for data_hora, nucleo in qs2.values_list("data_hora", "profissional_saude__nucleo__nome"):
            scheduler.append(data_hora, nucleo, icon='x')
        return scheduler
    
    def get_horarios_atendimento(self, readonly=True):
        scheduler=Scheduler(weekly=True, chucks=3, readonly=readonly)
        for ha in self.horarioatendimento_set.all():
           scheduler.append_weekday(ha.dia, ha.hora, ha.minuto)
        return scheduler
    
    def atualizar_horarios_atendimento(self, adicionar_datas, remover_datas, reiniciar=False):
        if reiniciar:
            HorarioAtendimento.objects.filter(profissional_saude=self).delete()
        for data in adicionar_datas:
            HorarioAtendimento.objects.get_or_create(profissional_saude=self, dia=data.weekday(), hora=data.hour, minuto=data.minute)
        for data in remover_datas:
            HorarioAtendimento.objects.filter(profissional_saude=self, dia=data.weekday(), hora=data.hour, minuto=data.minute).delete()
        dias_semana = {}
        for ha in self.horarioatendimento_set.all():
            if int(ha.dia)not in dias_semana:
                dias_semana[int(ha.dia)] = []
            dias_semana[int(ha.dia)].append(ha)
        inicial = datetime.today()
        final = inicial + timedelta(days=15)
        ids = []
        while inicial < final:
            for ha in dias_semana.get(inicial.weekday(), ()):
                hps = HorarioProfissionalSaude.objects.get_or_create(
                    profissional_saude=self, data_hora=datetime(inicial.year, inicial.month, inicial.day, ha.hora, ha.minuto)
                )[0]
                ids.append(hps.id)
            inicial += timedelta(days=1)
        HorarioProfissionalSaude.objects.filter(profissional_saude=self, data_hora__gte=datetime.now(), atendimentos_profissional_saude__isnull=True, atendimentos_especialista__isnull=True).exclude(id__in=ids).delete()

    @meta('Estabelecimento')
    def get_estabelecimento(self):
        return self.nucleo if self.nucleo_id else self.unidade
    
    def save(self, *args, **kwargs):
        if self.zoom_token is None:
           self.zoom_token = os.environ.get('ZOOM_TOKEN') 
        super().save(*args, **kwargs)


class HorarioAtendimento(models.Model):
    DIA_SEMANA_CHOICES = [[i, j] for i, j in enumerate(('SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'))]
    
    profissional_saude = models.ForeignKey(ProfissionalSaude, verbose_name='Profissional de Saúde', on_delete=models.CASCADE)
    dia = models.CharField(verbose_name='Dia da Semana', choices=DIA_SEMANA_CHOICES)
    hora = models.IntegerField(verbose_name='Hora')
    minuto = models.IntegerField(verbose_name='Minuto')

    class Meta:
        verbose_name = 'Horário de Atendimento'
        verbose_name_plural = 'Horários de Atendimento'

    def __str__(self):
        return f'{self.id} - {self.get_dia_display()} ({self.dia}, {self.hora})'
  

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
            self.filters("especialidade", "unidade", "paciente", "profissional", "especialista")
            .fields(
                ("especialidade", "agendado_para", "tipo"),
                ("unidade", "profissional", "paciente"),
                ("especialista", "get_duracao"), "get_tags"
            ).limit(5).order_by('-id')
        )
    
    def proximos(self):
        return self.filter(agendado_para__gte=datetime.now(), finalizado_em__isnull=True)
    
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
        return self.counter('especialidade__area', chart='donut')
    
    @meta('Total por Mês')
    def get_total_por_mes(self):
        return self.counter('agendado_para__month', chart='line')
    
    @meta('Atendimentos por Unidade e Especialidade')
    def get_total_por_area_e_unidade(self):
        return self.counter('especialidade__area', 'unidade')
    
    def agenda(self, profissional=None, especialista=None, is_teleconsulta=False, is_proprio_profissional=False):
        selectable = []
        scheduled = {}
        midnight = datetime.combine(datetime.now().date(), time())
        if profissional:
            # agenda ocupada do profissional de saúde
            for data_hora, pk in HorarioProfissionalSaude.objects.filter(data_hora__gte=midnight, profissional_saude__pessoa_fisica=profissional.pessoa_fisica, atendimentos_profissional_saude__isnull=False).values_list('data_hora', 'atendimentos_profissional_saude').order_by('-data_hora'):
                scheduled[data_hora] = pk
            for data_hora, pk in HorarioProfissionalSaude.objects.filter(data_hora__gte=midnight, profissional_saude__pessoa_fisica=profissional.pessoa_fisica, atendimentos_especialista__isnull=False).values_list('data_hora', 'atendimentos_especialista').order_by('-data_hora'):
                scheduled[data_hora] = pk
            # agenda ocupada do especialista
            if especialista:
                for data_hora, pk in HorarioProfissionalSaude.objects.filter(data_hora__gte=midnight, profissional_saude__pessoa_fisica=especialista.pessoa_fisica, atendimentos_profissional_saude__isnull=False).values_list('data_hora', 'atendimentos_profissional_saude').order_by('-data_hora'):
                    scheduled[data_hora] = pk
                for data_hora, pk in HorarioProfissionalSaude.objects.filter(data_hora__gte=midnight, profissional_saude__pessoa_fisica=especialista.pessoa_fisica, atendimentos_especialista__isnull=False).values_list('data_hora', 'atendimentos_especialista').order_by('-data_hora'):
                    scheduled[data_hora] = pk
            qs = profissional.horarioprofissionalsaude_set
            for horario in qs.filter(data_hora__gte=datetime.now()):
              if horario.data_hora not in scheduled:
                selectable.append(horario.data_hora)
            if especialista:
                selectable = HorarioProfissionalSaude.objects.filter(data_hora__gte=midnight, profissional_saude=especialista, data_hora__in=selectable).values_list('data_hora', flat=True)

        scheduler = Scheduler(
            chucks=3,
            watch=['profissional', 'especialista'],
            url='/api/consultarhorariosdisponiveis/',
            single_selection=True,
            selectable=None if is_teleconsulta and is_proprio_profissional else selectable,
            readonly=not selectable
        )
        for dt, pk in scheduled.items():
            scheduler.append(dt, 'Atendimento {}'.format(pk), 'stethoscope')
        return scheduler

@role('p', username='paciente__cpf')
class Atendimento(models.Model):
    profissional = models.ForeignKey(
        ProfissionalSaude,
        verbose_name='Profissional Responsável',
        related_name="atendimentos_profissional",
        on_delete=models.CASCADE,
        null=True
    )
    unidade = models.ForeignKey(
        Unidade, null=True, on_delete=models.CASCADE
    )
    especialista = models.ForeignKey(
        ProfissionalSaude,
        related_name="atendimentos_especialista",
        on_delete=models.CASCADE,
        null=True, blank=True, pick = True
    )

    especialidade = models.ForeignKey(
        Especialidade, verbose_name='Especialidade', on_delete=models.CASCADE, pick=True
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
    duracao = models.IntegerField(verbose_name='Duração', null=True, choices=[(20, '20min'), (40, '40min'), (60, '1h')], pick=True, default=20)

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

    token = models.CharField(verbose_name='Token', null=True, blank=True)

    objects = AtendimentoQuerySet()

    class Meta:
        icon = "laptop-file"
        verbose_name = "Teleconsulta"
        verbose_name_plural = "Teleconsultas"

    def check_webconf(self):
        from . import zoom
        if self.limite_webconf is None or self.limite_webconf < datetime.now():
            number, password, limit = self.profissional.criar_sala_virtual('Atendimento #{}'.format(self.id))
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
                    "unidade", "tipo", "especialidade",
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
                "Agendamento", ("profissional", "especialista", "duracao", "agendado_para",),
            )
        )
    
    def serializer(self):
        return (
            super()
            .serializer()
            .fields('get_tags')
            .actions('enviarnotificacaoatendimento', 'imprimiratendimento', 'imprimirtermoconsentimento', 'anexartermoconsentimento', 'anexararquivo', 'salavirtual', 'registrarecanminhamentoscondutas', 'emitiratestado', 'solicitarexames', 'prescrevermedicamento', 'finalizaratendimento')
            .fieldset(
                "Dados Gerais",
                (
                    ("tipo", "unidade", "unidade__municipio"),
                    ("agendado_para", "finalizado_em", "duracao_webconf"),
                    "get_url_externa"
                ) 
            )
            .fieldset("Web Conferência", (("numero_webconf", "senha_webconf", "limite_webconf"),), roles=('su',))
            .group()
                .section('Detalhamento')
                    .fieldset(
                        "Dados do Paciente", (
                            ("cpf", "nome"),
                            ("sexo", "nome_social"),
                            ("data_nascimento", "get_idade"),
                            ("telefone", "email")
                        ), attr="paciente", actions=('atualizarpaciente',)
                    )
                    .fieldset(
                        "Profissional Responsável", (
                            ("pessoa_fisica__nome", "pessoa_fisica__cpf"),
                            ("get_registro_profissional", "get_registro_especialista"),
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
                            ("assunto", "especialidade"),
                            "duvida",
                            ("cid", "ciap"),
                        )
                    )
                    .queryset('Anexos', 'get_anexos')
                .parent()
                .queryset('Encaminhamentos', 'get_condutas_ecaminhamentos', roles=('ps',))
            .parent()
        )
    
    @meta('Número')
    def get_numero(self):
        return Badge('#2670e8', self.id)
    
    @meta('Duração')
    def get_duracao(self):
        return f'{self.duracao} minutos'
    
    @meta()
    def get_tags(self):
        tags = []
        if self.tipo_id == TipoAtendimento.TELE_INTERCONSULTA:
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
        return self.anexoatendimento_set.fields('get_nome_arquivo', 'autor', 'assinaturas', 'get_arquivo')
    
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
    
    @meta(None)
    def get_termo_consentimento_digital(self):
        return TemplateContent('termoconsentimento.html', dict(atendimento=self))

    def is_termo_consentimento_assinado(self):
        return True
        termo_consentimento = self.get_termo_consentimento()
        if termo_consentimento:
            qtd_assinaturas = termo_consentimento.assinaturas.count()
            return qtd_assinaturas == (2 if self.especialista_id else 1)
        return False

    @meta('Termo de Consentimento')
    def get_termo_consentimento(self):
        return self.anexoatendimento_set.filter(nome='Termo de Consentimento').order_by('id').last()

    def get_agendado_para(self):
        return Badge("#5ca05d", self.agendado_para.strftime('%d/%m/%Y %H:%M'), icon='clock')

    @meta('URL Externa')
    def get_url_externa(self):
        return '{}/app/teleatendimento/?token={}'.format(settings.SITE_URL, self.token)
    
    def get_qrcode_link_webconf(self):
        return qrcode_base64(self.get_url_externa())

    def __str__(self):
        return "%s - %s" % (self.id, self.assunto)

    def save(self, *args, **kwargs):
        if self.token is None:
            self.token = uuid1().hex
        if self.data is None:
            self.data = timezone.now()
        super(Atendimento, self).save(*args, **kwargs)

    def post_save(self):
        minutos = [0]
        if self.duracao >= 40: minutos.append(20)
        if self.duracao == 60: minutos.append(40)
        # atendimentos marcados pelo próprio profissional não requer que o horário esteva previamente marcado em sua agenda
        for minuto in minutos:
            data_hora = self.agendado_para + timedelta(minutes=minuto)
            if not self.profissional.horarioprofissionalsaude_set.filter(data_hora=data_hora).exists():
                HorarioProfissionalSaude.objects.create(data_hora=data_hora, profissional_saude=self.profissional)
        
        for minuto in minutos:
            self.horarios_profissional_saude.add(self.profissional.horarioprofissionalsaude_set.get(data_hora=self.agendado_para + timedelta(minutes=minuto)))
            if self.especialista_id:
                self.horarios_especialista.add(self.especialista.horarioprofissionalsaude_set.get(data_hora=self.agendado_para + timedelta(minutes=minuto)))
  
    def criar_anexo(self, nome, template, cpf, dados):
        signature = printer.Signature(date=datetime.now(), validation_url='https://validar.iti.gov.br/')
        signature.add_signer('{} - {}'.format(self.profissional.pessoa_fisica.nome, self.profissional.get_registro_profissional()), None)
        autor = PessoaFisica.objects.get(cpf=cpf)
        anexo = AnexoAtendimento(atendimento=self, autor=autor, nome=nome)
        dados.update(data_hora=date.today())
        content = printer.to_pdf(dict(atendimento=self, impressao=False, **dados), template, signature=signature)
        anexo.arquivo.save('{}.pdf'.format(uuid1().hex), ContentFile(content.getvalue()))
        anexo.save()

class AnexoAtendimento(models.Model):
    atendimento = models.ForeignKey(
        Atendimento, on_delete=models.CASCADE
    )
    nome = models.CharField(verbose_name='Nome', default='')
    arquivo = models.FileField(max_length=200, upload_to="anexos_teleconsuta")
    autor = models.ForeignKey(PessoaFisica, null=True, on_delete=models.CASCADE)
    assinaturas = models.ManyToManyField(PessoaFisica, verbose_name='Assinaturas', blank=True, related_name='anexos_assinados')

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

    def possui_assinatura(self, cpf):
        if os.path.exists(self.arquivo.path):
            data = self.arquivo.read()
            def index_of(n=1):
                if n == 1:
                    return data.find(b'/ByteRange')
                else:
                    return data.find(b'/ByteRange', index_of(n - 1) + 1)

            for i in range(1, data.count(b'/ByteRange') + 1):
                n = index_of(i)
                start = data.find(b'[', n)
                stop = data.find(b']', start)
                assert n != -1 and start != -1 and stop != -1
                br = [int(i, 10) for i in data[start + 1: stop].split()]
                contents = data[br[0] + br[1] + 1: br[2] - 1]
                datas = bytes.fromhex(contents.decode('utf8'))
                try:
                    cpf = cpf.replace('.', '').replace('-', '')
                    datas.index(cpf.encode())
                    return True
                except ValueError:
                    return False
        return False
            
    def checar_assinaturas(self):
        if self.possui_assinatura('047.704.024-14'):
            self.assinaturas.add(PessoaFisica.objects.get(cpf='047.704.024-14'))
        if self.possui_assinatura(self.atendimento.profissional.pessoa_fisica.cpf):
            self.assinaturas.add(self.atendimento.profissional.pessoa_fisica)
        if self.atendimento.especialista:
            if self.possui_assinatura(self.atendimento.especialista.pessoa_fisica.cpf):
                self.assinaturas.add(self.atendimento.especialista.pessoa_fisica)
    

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
    avaliacao = models.TextField(verbose_name='A - avaliação', blank=True, null=True, help_text='Conjunto de campos que possibilita o registro da conclusão feita pelo profissional de saúde a partir dos dados observados nos itens anteriores, como os motivos para aquele encontro, a anamnese do cidadão e dos exames físico e complementares.')
    plano = models.TextField(verbose_name='P - Plano', blank=True, null=True, help_text='Conjunto de funcionalidades que permite registrar o plano de cuidado ao cidadão em relação ao(s) problema(s) avaliado(s).')

    data = models.DateTimeField(auto_now_add=True)

    comentario = models.TextField(verbose_name='Comentário', blank=True)
    encaminhamento = models.TextField(verbose_name='Encaminhamento', blank=True, null=True)
    conduta = models.TextField(verbose_name='Conduta', blank=True, null=True)

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


class DocumentoQuerySet(models.QuerySet):
    def all(self):
        return self
    
    def gerar(self, nome, conteudo):
        Documento.objects.create()


class Documento(models.Model):
    uuid = models.CharField(verbose_name='UUID')
    nome = models.CharField(verbose_name='Nome')
    data = models.DateTimeField(verbose_name='Data')
    arquivo = models.FileField(verbose_name='Arquivo', upload_to='documentos')

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    objects = DocumentoQuerySet()

    def __str__(self):
        return f'Documento {self.id}'
    
    def get_codigo_verificador(self):
        return str(self.id).rjust(6, '0')
    
    def get_codigo_autenticacao(self):
        return self.uuid[0:6]


class TipoExameQuerySet(models.QuerySet):
    def all(self):
        return self


class TipoExame(models.Model):
    nome = models.CharField(verbose_name='Nome')
    detalhe = models.CharField(verbose_name='Detalhe', blank=True, null=True)
    tuss = models.CharField(verbose_name='TUSS', null=True)

    class Meta:
        verbose_name = 'Tipo de Exame'
        verbose_name_plural = 'Tipos de Exames'

    objects = TipoExameQuerySet()

    def __str__(self):
        return self.nome


class MedicamentoQuerySet(models.QuerySet):
    def all(self):
        return self


class Medicamento(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'

    objects = MedicamentoQuerySet()

    def __str__(self):
        return self.nome

    

