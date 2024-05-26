import os
import time
import datetime
from slth.db import models, meta, role
from slth.components import Badge, Steps, FileLink, Progress
from slth.models import PushSubscription
from .services import OpenAIService
from difflib import SequenceMatcher

@role('administrador', 'cpf')
class Administrador(models.Model):
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')

    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administrador'

    def __str__(self):
     return '{}'.format(self.nome)

class Estado(models.Model):
    sigla = models.CharField('Sigla')
    nome = models.CharField('Nome')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.sigla


class Prioridade(models.Model):
    descricao = models.CharField('Descrição')
    cor = models.ColorField('Cor')
    prazo_resposta = models.IntegerField('Prazo para Resposta', help_text='Em horas')

    class Meta:
        verbose_name = 'Prioridade'
        verbose_name_plural = 'Prioridades'

    def __str__(self):
        return self.descricao

    @meta('Prazo para Resposta')
    def get_prazo_resposta(self):
        if self.prazo_resposta > 1:
            return '{} horas'.format(self.prazo_resposta)
        return '{} hora'.format(self.prazo_resposta)


class AssuntoQuerySet(models.QuerySet):

    def all(self):
        return self.search('descricao')

class Assunto(models.Model):
    descricao = models.CharField('Descrição')

    class Meta:
        verbose_name = 'Assunto'
        verbose_name_plural = 'Assuntos'

    objects = AssuntoQuerySet()

    def __str__(self):
        return self.descricao
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', ['descricao'])
            .queryset('Tópicos', 'get_topicos')
        )
    
    @meta('Tópicos')
    def get_topicos(self):
        return self.topico_set.fields('descricao', 'get_qtd_arquivos').actions('edit', 'delete', 'add', 'visualizartopico').related_values(assunto=self)
    
    def get_qtd_topicos(self):
        return self.topicos.count()

class Topico(models.Model):
    assunto = models.ForeignKey(Assunto, verbose_name='Assunto')
    descricao = models.CharField('Descrição')
    codigo_openai = models.CharField('Código', null=True, blank=True)

    class Meta:
        verbose_name = 'Tópico'
        verbose_name_plural = 'Tópicos'
        search_fields = 'assunto__descricao', 'descricao'

    def __str__(self):
        return '{} - {}'.format(self.assunto, self.descricao)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.codigo_openai is None:
            Topico.objects.filter(pk=self.pk).update(
                codigo_openai=OpenAIService().create_assistant(
                    'AnalisaRN {} - {}'.format(self.assunto, self.descricao)
                )
            )

    def perguntar_inteligencia_artificial(self, pergunta, arquivos=None):
        if arquivos is None:
            arquivos = self.arquivo_set
        file_ids = arquivos.filter(codigo_openai__isnull=False).values_list('codigo_openai', flat=True)
        return OpenAIService().ask_question(pergunta, self.codigo_openai, file_ids)
    
    def formfactory(self):
        return super().formfactory().fields('assunto', 'descricao')
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', [('assunto', 'descricao'), 'codigo_openai'])
            .queryset('Arquivos', 'get_arquivos')
        )
    
    def get_arquivos(self):
        return self.arquivo_set.fields('nome', 'get_arquivo', 'codigo_openai').actions('edit', 'delete', 'add').related_values(topico=self)

    @meta('Quantidade de Arquivos')
    def get_qtd_arquivos(self):
        return self.arquivo_set.count()

class Arquivo(models.Model):
    topico = models.ForeignKey(Topico, verbose_name='Tópico', null=True)
    nome = models.CharField('Nome')
    arquivo = models.FileField('Arquivo', upload_to='arquivos', null=True, extensions=('txt',))
    codigo_openai = models.CharField('Código', null=True, blank=True)
    ativo = models.BooleanField(verbose_name='Ativo', default=True)

    class Meta:
        verbose_name = 'Arquivo'
        verbose_name_plural = 'Arquivos'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.codigo_openai is None:
            Arquivo.objects.filter(pk=self.pk).update(
                codigo_openai=OpenAIService().create_file(
                    "{} - {}".format(self.topico, self.nome),
                    self.topico.codigo_openai, self.arquivo.path
                )
            )

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.codigo_openai:
            OpenAIService().delte_file(
                self.topico.codigo_openai, self.codigo_openai
            )

    def get_arquivo(self):
        return FileLink(self.arquivo, icon='file', modal=True)

    def formfactory(self):
        return super().formfactory().fields('topico', 'nome', 'arquivo')
    
    def __str__(self):
        return self.nome

class PerguntaFrequenteQuerySet(models.QuerySet):

    def all(self):
        return self.search('pergunta').filters('topico__assunto', 'topico').rows()

class PerguntaFrequente(models.Model):
    topico = models.ForeignKey(Topico, verbose_name='Tópico', related_name='perguntas_frequentes')
    pergunta = models.TextField('Pergunta')
    resposta = models.TextField('Resposta', blank=True)

    class Meta:
        verbose_name = 'Pergunta Frequente'
        verbose_name_plural = 'Perguntas Frequentes'

    objects = PerguntaFrequenteQuerySet()

    def __str__(self):
        return self.pergunta
    
    def save(self, *args, **kwargs):
        if not self.resposta and self.topico.arquivo_set.exists():
            self.resposta = self.topico.perguntar_inteligencia_artificial(self.pergunta)
        super().save(*args, **kwargs)

    def formfactory(self):
        if self.pk:
            return super().formfactory().fields('resposta',)
        else:
            return super().formfactory().fields('topico', 'pergunta')


class EspecialistaQuerySet(models.QuerySet):

    def all(self):
        return self.fields('cpf', 'nome', 'estados', 'assuntos').search('nome').filters('estados', 'assuntos')

@role('especialista', 'cpf')
class Especialista(models.Model):
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')
    registro = models.CharField('Nº do Registro Profissional', null=True, blank=True)
    minicurriculo = models.TextField('Minicurrículo', null=True, blank=True) 
    endereco = models.CharField('Endereço', null=True, blank=True)
    telefone = models.CharField('Telefone', null=True, blank=True)
    email = models.CharField('E-mail', null=True, blank=True)
    estados = models.ManyToManyField(Estado, verbose_name='Estados')
    assuntos = models.ManyToManyField(Assunto, verbose_name='Assuntos')
    

    class Meta:
        verbose_name = 'Especialista'
        verbose_name_plural = 'Especialistas'

    objects = EspecialistaQuerySet()

    def __str__(self):
     return self.nome
    
    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('nome', ('cpf', 'registro'), 'minicurriculo'))
            .fieldset('Dados de Contato', ('endereco', ('telefone', 'email')))
            .fieldset('Atuação', ('estados', 'assuntos'))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', ('nome', ('cpf', 'registro'), 'minicurriculo'))
            .fieldset('Dados de Contato', ('endereco', ('telefone', 'email')))
            .fieldset('Atuação', ('estados', 'assuntos'))
        )
    
class ClienteQuerySet(models.QuerySet):
    def all(self):
        return self.fields('cpf_cnpj', 'nome', 'estado', 'assuntos').filters('estado', 'assunto').search('nome', 'cpf_cnpj')

@role('cliente', 'cpf_cnpj')
class Cliente(models.Model):
    cpf_cnpj = models.CharField('CPF/CNPJ')
    nome = models.CharField('Nome')
    endereco = models.CharField('Endereço', null=True, blank=True)
    telefone = models.CharField('Telefone')

    cpf_responsavel = models.CharField('CPF do Responsável')
    nome_responsavel = models.CharField('Nome do Responsável')
    cargo_responsavel = models.CharField('Cargo do Responsável')
    email_responsavel = models.EmailField('E-mail', null=True)

    estado = models.ForeignKey(Estado, verbose_name='Estado', null=True)
    assuntos = models.ManyToManyField(Assunto, verbose_name='Assuntos', blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    objects = ClienteQuerySet()

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        consultante = Consultante.objects.filter(cpf=self.cpf_responsavel).first()
        if consultante is None:
            consultante = Consultante()
            consultante.cliente = self
            consultante.cpf = self.cpf_responsavel
            consultante.nome = self.nome_responsavel
            consultante.save()

    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('nome', ('cpf_cnpj', 'telefone'), 'endereco'))
            .fieldset('Responsável', ('nome_responsavel', ('cpf_responsavel', 'cargo_responsavel'), 'email_responsavel'))
            .fieldset('Atuação', ('estado', 'assuntos'))
            .fieldset('Controle', ('ativo',))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', ('nome', ('cpf_cnpj', 'telefone'), 'endereco'))
            .group('Detalhamento')
                .section('Dados Cadastrais')
                    .fieldset('Responsável', ('nome_responsavel', ('cpf_responsavel', 'cargo_responsavel'), 'email_responsavel'))
                    .fieldset('Atuação', ('estado', 'assuntos'))
                    .fieldset('Controle', ('ativo',))
                    .parent()
                .queryset('Consultantes', 'get_consultantes')
                .queryset('Arquivos', 'get_arquivos')
                .queryset('Consultas', 'get_consultas')
                .fieldset('Estatística', (('get_consultas_por_prioridade', 'get_consultas_por_topico', 'get_consultas_por_consultante'),))
                .parent()
        )
    
    def get_arquivos(self):
        return self.arquivocliente_set.fields('nome', 'get_arquivo', 'codigo_openai').actions('edit', 'delete', 'add').related_values(cliente=self)
    
    def get_consultantes(self):
        return self.consultante_set.actions('edit', 'delete', 'add').related_values(cliente=self)
    
    def get_consultas(self):
        return Consulta.objects.filter(consultante__cliente=self).fields('get_prioridade', 'topico', 'pergunta')
    
    @meta('Consultas por Prioridade')
    def get_consultas_por_prioridade(self):
        return self.get_consultas().counter('prioridade', chart='donut')
    
    @meta('Consultas por Tópico')
    def get_consultas_por_topico(self):
        return self.get_consultas().counter('topico', chart='pizza')
    
    @meta('Consultas por Consultante')
    def get_consultas_por_consultante(self):
        return self.get_consultas().counter('consultante', chart='bar')

class ArquivoCliente(Arquivo):
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente')

    class Meta:
        verbose_name = 'Arquivo de Cliente'
        verbose_name_plural = 'Arquivos de Cliente'

    def formfactory(self):
        return super().formfactory().fields('cliente', ('topico', 'nome'), 'arquivo', 'ativo')
    
    def get_topico_queryset(self, queryset, values):
        if 'cliente' in values:
            queryset = queryset.filter(
                assunto__in=values['cliente'].assuntos.values_list('pk', flat=True)
            )
        return queryset

@role('consultante', 'cpf', cliente='cliente')
class Consultante(models.Model):
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente')
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')

    class Meta:
        verbose_name = 'Consultante'
        verbose_name_plural = 'Consultantes'

    def __str__(self):
     return '{}'.format(self.nome)


class Anexo(models.Model):
    nome = models.CharField('Nome')
    data_hora = models.DateTimeField(auto_now_add=True)
    arquivo = models.FileField('Arquivo', upload_to='anexos', null=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'

    def get_arquivo(self):
        return FileLink(self.arquivo, modal=True, icon='file')

class ConsultaQuerySet(models.QuerySet):

    def all(self):
        return self.fields(
            ('consultante', 'get_prioridade', 'topico', 'get_situacao'), 'pergunta', 'data_pergunta'
        ).filters('topico', 'data_pergunta').subsets(
            'aguardando_especialista', 'aguardando_resposta', 'aguardando_envio', 'respondidas'
        ).rows()

    @meta('Aguardando Especialista')
    def aguardando_especialista(self):
        return self.filter(especialista__isnull=True)

    @meta('Aguardando Resposta')
    def aguardando_resposta(self):
        return self.filter(especialista__isnull=False, resposta__isnull=True)

    @meta('Aguardando Envio')
    def aguardando_envio(self):
        return self.filter(resposta__isnull=False, data_resposta__isnull=True)

    @meta('Não-Respondidas')
    def nao_respondidas(self):
        return self.filter(data_resposta__isnull=True)

    @meta('Respondidas')
    def respondidas(self):
        return self.filter(data_resposta__isnull=False)

    @meta('Total por Prioridade')
    def total_por_prioridade(self):
        return self.counter('prioridade', chart='donut')
    
    @meta('Total por Tópico')
    def total_por_topico(self):
        return self.counter('topico')
    
    @meta('Total por Assunto')
    def total_por_assunto(self):
        return self.counter('topico__assunto')
    
    @meta('Total por Cliente')
    def total_por_cliente(self):
        return self.counter('consultante__cliente', chart='bar')
    
    @meta('Total por Mês')
    def total_por_mes(self):
        return self.counter('data_pergunta__month', chart='line')
    
    @meta('Total de Consultas')
    def quantidade_geral(self):
        return self.count()
    
    @meta('Clientes Atendidos')
    def total_clientes(self):
        return self.values_list('consultante__cliente').distinct().count()
    
    @meta('Consultantes Atendidos')
    def total_consultantes(self):
        return self.values_list('consultante').distinct().count()
    
    @meta('Especialistas Envolvidos')
    def total_especialistas(self):
        return self.values_list('especialista').distinct().count()

    @meta('Total por Especialista')
    def total_por_especialista(self):
        return self.counter('especialista')
    
    @meta('Total por Estado')
    def total_por_estado(self):
        return self.counter('consultante__cliente__estado', chart='pizza')
    

class Consulta(models.Model):

    consultante = models.ForeignKey(Consultante, verbose_name='Consultante')
    prioridade = models.ForeignKey(Prioridade, verbose_name='Prioridade')
    topico = models.ForeignKey(Topico, verbose_name='Tópico')
    pergunta = models.TextField(verbose_name='Pergunta')
    observacao = models.TextField(verbose_name='Observação', null=True, blank=True)
    data_pergunta = models.DateTimeField('Data da Pergunta', auto_now_add=True)

    especialista = models.ForeignKey(Especialista, verbose_name='Especialista', null=True, blank=True)

    data_consulta = models.DateTimeField('Data da Consulta', null=True, blank=True)
    pergunta_ia = models.TextField(verbose_name='Pergunta I.A.', null=True, blank=True)
    resposta_ia = models.TextField(verbose_name='Resposta I.A.', null=True, blank=True)

    resposta = models.TextField(verbose_name='Resposta Final', null=True, blank=True)
    data_resposta = models.DateTimeField('Data da Resposta', null=True, blank=True)

    anexos = models.OneToManyField(Anexo, verbose_name='Anexos')
    pergunta_frequente = models.ForeignKey(PerguntaFrequente, verbose_name='Pergunta Frequente', null=True, blank=True)

    percentual_similaridade_resposta = models.IntegerField('Percentual de Simiralidade da Resposta', null=True)

    objects = ConsultaQuerySet()

    class Meta:
        icon = 'file-signature'
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return 'Consulta {} ({})'.format(self.pk, self.topico.assunto)
    
    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('consultante', ('prioridade', 'topico'), 'pergunta', 'observacao'))
            .fieldset('Anexos', ('anexos',))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .actions('adicionarabaseconhecimento', 'videochamada')
            .field('get_passos')
            .fieldset('Dados Gerais', ('consultante', ('get_prioridade', 'topico'), 'pergunta', 'observacao'))
            .fieldset('Datas', (('data_pergunta', 'data_consulta', 'data_resposta'),), reload=False)
            .queryset('Anexos', 'get_anexos')
            .queryset('Interações', 'get_interacoes')
            .fieldset('Resposta', ('especialista', 'pergunta_ia', 'resposta_ia', 'resposta', 'get_percentual_similaridade_resposta'), actions=('assumirconsulta', 'liberarconsulta', 'consultaria','enviarresposta'))
        )
    
    @meta('Anexos')
    def get_anexos(self):
        return self.anexos.fields('nome', 'get_arquivo')

    @meta('Prioridade')
    def get_prioridade(self):
        return Badge(self.prioridade.cor, self.prioridade.descricao)
    
    @meta('Interações')
    def get_interacoes(self):
        return self.interacao_set.fields('data_hora', 'arquivo').actions('add').related_values(consulta=self).timeline()

    @meta(None)
    def get_passos(self):
        steps = Steps()
        steps.append('Pergunta', self.data_pergunta)
        steps.append('Consulta', self.data_consulta)
        steps.append('Resposta', self.data_resposta)
        return steps
    
    @meta('Situação')
    def get_situacao(self):
        if self.especialista_id is None:
            return 'Aguardando Especialista'
        elif self.data_resposta:
            return 'Finalizada'
        elif self.get_minutos_resposta() >= 0:
            return 'Em Atendimento'
        elif self.get_minutos_resposta() < 0:
            return 'Em Atraso'

    def save(self, *args, **kwargs):
        pk = self.pk
        super().save(*args, **kwargs)
        if pk is None and pk:
            cpfs = Especialista.objects.filter(assuntos=self.topico.assunto).values_list('cpf', flat=True)
            texto = 'Nova pergunta sobre "{}" cadastrada pelo cliente "{}".'.format(self.topico, self.consultante.cliente)
            for subscription in PushSubscription.objects.filter(user__username__in=cpfs):
                subscription.notify(texto)
        if self.percentual_similaridade_resposta is None and self.resposta_ia and self.resposta:
            self.percentual_similaridade_resposta = int(SequenceMatcher(None, self.resposta_ia, self.resposta).ratio()*100)
            super().save(*args, **kwargs)

    @meta('Percentual de Similaridade da Resposta')
    def get_percentual_similaridade_resposta(self):
        return Progress(self.percentual_similaridade_resposta) if self.percentual_similaridade_resposta else None
    
    def get_minutos_resposta(self):
        limite = self.data_pergunta + datetime.timedelta(seconds=3600 * self.prioridade.prazo_resposta)
        print(self.data_pergunta, str(self.prioridade.prazo_resposta)+'h', limite)
        return int((limite - datetime.datetime.now()).total_seconds() / 60)

    @meta('Limite para Resposta')
    def get_limite_resposta(self):
        minutos = self.get_minutos_resposta()
        if abs(minutos) > 60:
            if abs(minutos/60) > 24:
                return '{} dias e {} horas'.format(int(minutos/60/24), int(minutos/60%24)) 
            return '{} horas e {} minutos'.format(int(minutos/60), int(minutos%60))
        return '{} minutos'.format(minutos)
    
    def get_topico_queryset(self, queryset, values):
        consultante = values.get('consultante')
        if consultante:
            queryset = queryset.filter(assunto__in=consultante.cliente.assuntos.values_list('pk', flat=True))
        return queryset
    
    def __str__(self):
        return self.pergunta

class Interacao(models.Model):
    consulta = models.ForeignKey(Consulta, verbose_name='Consulta')
    mensagem = models.TextField('Mensagem')
    data_hora = models.DateTimeField(auto_now_add=True)
    arquivo = models.FileField('Arquivo', upload_to='interacoes', extensions=['pdf'], max_size=1, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Interação'
        verbose_name_plural = 'Interações'

    def get_arquivo(self):
        return FileLink(self.arquivo, modal=True, icon='file')
    
    def __str__(self):
        return self.mensagem

class Mensalidade(models.Model):
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente', related_name='mensalidades')
    valor = models.DecimalField(verbose_name='Valor')
    data_vencimento = models.DateField(verbose_name='Data do Vencimento')
    data_pagamento = models.DateField(verbose_name='Data do Pagamento', null=True, blank=True)


    class Meta:
        verbose_name = 'Mensalidade'
        verbose_name_plural = 'Mensalidades'

    def __str__(self):
     return '{} ({}/{})'.format(self.cliente, self.data_vencimento.month, self.data_vencimento.year)

