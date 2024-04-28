import os
import sys
import time
import datetime
from openai import OpenAI
from slth.db import models, meta, role
from slth.components import Badge, Steps, FileLink
from slth.models import PushSubscription

OPENAI_KEY = os.getenv('OPENAI_KEY') if 'integration_test' not in sys.argv else None

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
        if OPENAI_KEY and self.codigo_openai is None:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            assistant = client.beta.assistants.create(
                name='AnalisaRN {} - {}'.format(self.assunto, self.descricao),
                instructions="",
                #tools=[{'type': 'file_search'}],
                model="gpt-4-1106-preview"
            )
            Topico.objects.filter(pk=self.pk).update(codigo_openai=assistant.id)

    def perguntar_inteligencia_artificial(self, pergunta):
        if OPENAI_KEY:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            attachments = []
            for arquivo in self.arquivo_set.filter(codigo_openai__isnull=False):
                attachments.append({ "file_id": arquivo.codigo_openai, "tools": [{"type": "file_search"}] })
            thread = client.beta.threads.create(messages=[{"role": "user", "content": pergunta, "attachments": attachments,}])
            run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=self.codigo_openai)
            for i in range(1, 5):
                print('Waiting for the response...')
                time.sleep(2)
                if client.beta.threads.runs.retrieve(run.id, thread_id=thread.id).status == 'completed':
                    break
            messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            message_content = messages[0].content[0].text.value
        else:
            message_content = 'Resposta teste.'
        return message_content
    
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

    class Meta:
        verbose_name = 'Arquivo'
        verbose_name_plural = 'Arquivos'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if OPENAI_KEY and self.codigo_openai is None:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            with open(self.arquivo.path, 'rb') as file:
                vector_store = client.beta.vector_stores.create(name="{} - {}".format(self.topico, self.nome))
                file_paths = [self.arquivo.path]
                file_streams = [open(path, "rb") for path in file_paths]
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(vector_store_id=vector_store.id, files=file_streams)
                print(file_batch.status)
                print(file_batch.file_counts)
                time.sleep(5)
                client.beta.assistants.update(self.topico.codigo_openai, tools=[{'type': 'file_search'}], tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}})
                Arquivo.objects.filter(pk=self.pk).update(codigo_openai=client.beta.vector_stores.files.list(vector_store.id).data[0].id)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if OPENAI_KEY and self.codigo_openai:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            client.beta.assistants.files.delete(
                file_id=self.codigo_openai, assistant_id=self.topico.codigo_openai
            )
            client.files.delete(self.codigo_openai)

    def get_arquivo(self):
        return FileLink(self.arquivo, icon='file', modal=True)

    def formfactory(self):
        return super().formfactory().fields('topico', 'nome', 'arquivo')

class PerguntaFrequenteQuerySet(models.QuerySet):

    def all(self):
        return self.search('pergunta').filters('topico__assunto', 'topico')

class PerguntaFrequente(models.Model):
    topico = models.ForeignKey(Topico, verbose_name='Tópico', related_name='perguntas_frequentes')
    pergunta = models.CharField('Pergunta')
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
    estados = models.ManyToManyField(Estado, verbose_name='Estados', pick=True)
    assuntos = models.ManyToManyField(Assunto, verbose_name='Assuntos', pick=True)
    

    class Meta:
        verbose_name = 'Especialista'
        verbose_name_plural = 'Especialistas'

    objects = EspecialistaQuerySet()

    def __str__(self):
     return '{} ({})'.format(self.nome, self.cpf)
    
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
        return '{} ({})'.format(self.nome, self.cpf_cnpj)
    
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
                .queryset('Consultas', 'get_consultas')
                .fieldset('Estatística', (('get_consultas_por_prioridade', 'get_consultas_por_topico', 'get_consultas_por_consultante'),))
                .parent()
        )
    
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
            'consultante', 'get_prioridade', 'topico', 'pergunta', 'get_situacao'
        ).filters('topico', 'data_pergunta').subsets(
            'aguardando_especialista', 'aguardando_resposta', 'aguardando_envio', 'respondidas'
        )

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
    
    @meta('Total por Cliente')
    def total_por_cliente(self):
        return self.counter('consultante__cliente', chart='bar')
    
    @meta('Total por Mês')
    def total_por_mes(self):
        return self.counter('data_pergunta__month', chart='line')
    
    @meta('Total de Consultas')
    def quantidade_geral(self):
        return self.count()
    

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

    objects = ConsultaQuerySet()

    class Meta:
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
            .actions('adicionarabaseconhecimento')
            .field('get_passos')
            .fieldset('Dados Gerais', ('consultante', ('get_prioridade', 'topico'), 'pergunta', 'observacao'))
            .fieldset('Datas', (('data_pergunta', 'data_consulta', 'data_resposta'),), reload=False)
            .queryset('Anexos', 'get_anexos')
            .queryset('Interações', 'get_interacoes')
            .fieldset('Resposta', ('especialista', 'pergunta_ia', 'resposta_ia', 'resposta'), actions=('assumirconsulta', 'liberarconsulta', 'consultaria','enviarresposta'))
        )
    
    @meta('Anexos')
    def get_anexos(self):
        return self.anexos.fields('nome', 'get_arquivo').actions('add').related_values(consulta=self)

    @meta('Prioridade')
    def get_prioridade(self):
        return Badge(self.prioridade.cor, self.prioridade.descricao)
    
    @meta('Interações')
    def get_interacoes(self):
        return self.interacao_set.fields('mensagem', 'data_hora', 'arquivo').actions('add').related_values(consulta=self)

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
