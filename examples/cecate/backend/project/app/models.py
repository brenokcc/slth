from slth.db import models, role, meta
from slth.components import Image, Map, Progress


class NivelEnsino(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Nível de Ensino'
        verbose_name_plural = 'Níveis de Ensino'

    def __str__(self):
        return self.nome
    
class SituacaoEscolaridade(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Situação de Escolaridade'
        verbose_name_plural = 'Situações de Escolaridade'

    def __str__(self):
        return self.nome

class Poder(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Poder'
        verbose_name_plural = 'Poderes'

    def __str__(self):
        return self.nome


class Esfera(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Esfera'
        verbose_name_plural = 'Esferas'

    def __str__(self):
        return self.nome
    
class TipoOrgao(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Tipo de Orgão'
        verbose_name_plural = 'Tipos de Orgãos'

    def __str__(self):
        return self.nome


class Orgao(models.Model):
    sigla = models.CharField(verbose_name='Sigla')
    nome = models.CharField(verbose_name='Nome')
    cnpj = models.CharField(verbose_name='CNPJ')
    tipo = models.ForeignKey(TipoOrgao, verbose_name='Tipo', on_delete=models.CASCADE)
    esfera = models.ForeignKey(Esfera, verbose_name='Esfera', on_delete=models.CASCADE)
    poder = models.ForeignKey(Poder, verbose_name='Poder', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Orgão'
        verbose_name_plural = 'Orgãos'

    def __str__(self):
        return f'Orgão {self.id}'
    
    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', (('sigla', 'nome'),))
            .fieldset('Classificação', (('tipo', 'esfera', 'poder'),))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', (('sigla', 'nome'),))
            .fieldset('Classificação', (('tipo', 'esfera', 'poder'),))
        )

class PessoaFisicaQueryset(models.QuerySet):
    def all(self):
        return self.search('nome', 'cpf')

@role('pf', 'cpf')
class PessoaFisica(models.Model):
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='pessoas_fisicas')
    cpf = models.CharField(verbose_name='CPF')
    nome = models.CharField(verbose_name='Nome')
    nome_social = models.CharField(verbose_name='Nome Social', null=True, blank=True)
    telefone = models.CharField(verbose_name='Telefone')
    email = models.CharField(verbose_name='E-mail')
    class Meta:
        verbose_name = 'Pessoa Física'
        verbose_name_plural = 'Pessoas Físicas'

    objects = PessoaFisicaQueryset()

    def __str__(self):
        return f'{self.nome}'
    
    @meta('Foto')
    def get_foto(self):
        return Image(self.foto, width=75, round=True)
    
    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('foto', ('cpf', 'nome')))
            .fieldset('Dados de Contato', (('telefone', 'email'),))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', ('foto', ('cpf', 'nome')))
            .fieldset('Dados para Contato', (('telefone', 'email'),))
            .queryset('Redes Sociais', 'redesocial_set', actions=('edit', 'delete', 'add'), related_field='pessoa_fisica')
            .queryset('Escolaridades', 'escolaridade_set', actions=('edit', 'delete', 'add'), related_field='pessoa_fisica')
        )

class Escolaridade(models.Model):
    pessoa_fisica = models.ForeignKey(PessoaFisica, verbose_name='Pessoa Física', on_delete=models.CASCADE)
    nivel_ensino = models.ForeignKey(NivelEnsino, verbose_name='Nível de Ensino', on_delete=models.CASCADE)
    situacao = models.ForeignKey(SituacaoEscolaridade, verbose_name='Situação', on_delete=models.CASCADE)
    instituicao = models.CharField(verbose_name='Instituição', null=True, blank=True)
    curso = models.CharField(verbose_name='Curso', null=True, blank=True)

    class Meta:
        verbose_name = 'Escolaridade'
        verbose_name_plural = 'Escolaridades'


    def __str__(self):
        return f'{self.nivel_ensino} ({self.situacao})'

    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('pessoa_fisica', ('nivel_ensino', 'situacao')))
            .fieldset('Detalhamento', ('instituicao', 'curso'))
        )

class TipoRedeSocial(models.Model):
    nome = models.CharField(verbose_name='Nome')

    class Meta:
        verbose_name = 'Tipo de Rede Social'
        verbose_name_plural = 'Tipos de Rede Social'

    def __str__(self):
        return self.nome

class RedeSocial(models.Model):
    pessoa_fisica = models.ForeignKey(PessoaFisica, verbose_name='Pessoa Física', on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoRedeSocial, verbose_name='Tipo', on_delete=models.CASCADE)
    informacao = models.CharField(verbose_name='Informação')

    class Meta:
        verbose_name = 'Rede Social'
        verbose_name_plural = 'Redes Sociais'

    def __str__(self):
        return f'{self.tipo}: {self.informacao}'

class Estado(models.Model):
    sigla = models.CharField(verbose_name='Sigla')
    nome = models.CharField(verbose_name='Nome')
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return f'{self.sigla}'
    
    def get_cidades(self):
        return self.cidade_set.all()
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', [('sigla', 'nome')])
            .queryset('Municípios', 'municipio_set', actions=('edit', 'delete', 'add'), related_field='estado')
        )

class Municipio(models.Model):
    nome = models.CharField(verbose_name='Nome')
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)
    latitude = models.CharField(verbose_name='Latitude', null=True, blank=True)
    longitude = models.CharField(verbose_name='Longitude', null=True, blank=True)

    view_fieldsets = {
        'Dados Gerais': ('nome', 'estado'),
        'Localização': (('latitude', 'longitude'), 'get_mapa')
    }
    class Meta:
        verbose_name = 'Município'
        verbose_name_plural = 'Municípios'

    def __str__(self):
        return f'{self.nome} / {self.estado}'
    
    @meta('Mapa')
    def get_mapa(self):
        return dict(type='xxx', a=1, b=2)
        if self.latitude and self.longitude:
            return Map(self.latitude, self.longitude)
        return 'Defina a latitude e longitude'
    

class InstrumentoAvaliativo(models.Model):
    nome = models.CharField(verbose_name='Nome')
    responsavel = models.ForeignKey(PessoaFisica, verbose_name='Responsável', on_delete=models.CASCADE)
    data_inicio = models.DateField(verbose_name='Início')
    data_termino = models.DateField(verbose_name='Término')
    instrucoes = models.TextField(verbose_name='Instruções', null=True, blank=True)

    class Meta:
        verbose_name = 'Instrumento Avaliativo'
        verbose_name_plural = 'Instrumentos Avaliativos'

    def __str__(self):
        return f'Instrumento Avaliativo {self.id}'
    
    @meta('Questionários')
    def get_questionarios(self):
        return self.questionario_set.fields('respondente', 'get_progresso')
    
    def formfactory(self):
        return (
            super().formfactory()
            .fieldset('Dados Gerais', ('nome', 'responsavel'))
            .fieldset('Período de Realização', ((('data_inicio', 'data_termino')),))
            .fieldset('Outras Informações', ('instrucoes',))
        )
    
    def serializer(self):
        return (
            super().serializer()
            .fieldset('Dados Gerais', ['responsavel', ('data_inicio', 'data_termino'), 'instrucoes'])
            .queryset('Perguntas', 'pergunta_set', actions=('edit', 'delete', 'add', 'visualizarpergunta'), related_field='instrumento_avaliativo')
            .queryset('Questionários', 'get_questionarios', actions=('add', 'responderquestionario', 'visualizarrespostasquestionario'), related_field='instrumento_avaliativo')
        )

class OpcaoResposta(models.Model):
    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        verbose_name = 'Opção de Resposta'
        verbose_name_plural = 'Opções de Resposta'

    def __str__(self):
        return self.descricao

class Pergunta(models.Model):
    TEXTO_CURTO = 1
    TEXTO_LONGO = 2
    DATA = 3
    DECIMAL = 4
    INTEIRO = 5
    ESCOLHA = 6
    MULTIPLA_ESCOLHA = 7
    TIPO_RESPOSTA_CHOICES = [
        (TEXTO_CURTO, 'Texto curso'),
        (TEXTO_LONGO, 'Texto longo'),
        (DATA, 'Data'),
        (DECIMAL, 'Decimal'),
        (INTEIRO, 'Inteiro'),
        (ESCOLHA, 'Escolha'),
        (MULTIPLA_ESCOLHA, 'Múltipla Escolha'),
    ]
    instrumento_avaliativo = models.ForeignKey(InstrumentoAvaliativo, verbose_name='Instrumento Avaliativo', on_delete=models.CASCADE)
    enunciado = models.TextField(verbose_name='Enunciado')
    tipo_resposta = models.IntegerField(verbose_name='Tipo da Resposta', choices=TIPO_RESPOSTA_CHOICES)
    resposta_obrigatoria = models.BooleanField(verbose_name='Resposta Obrigatória', blank=True)
    opcoes = models.OneToManyField(OpcaoResposta, verbose_name='Opções de Resposta')

    class Meta:
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'

    def __str__(self):
        return self.enunciado
    
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for questionario in Questionario.objects.filter(instrumento_avaliativo=self.instrumento_avaliativo):
            questionario.gerar_perguntas()

    @meta('Respostas')
    def get_respostas(self):
        return self.perguntaquestionario_set.fields('get_responente', 'resposta')

    @meta('Estatística')
    def get_estatistica(self):
        return self.perguntaquestionario_set.counter('resposta', chart='donut')


class Questionario(models.Model):
    instrumento_avaliativo = models.ForeignKey(InstrumentoAvaliativo, verbose_name='Instrumento Avaliativo', on_delete=models.CASCADE)
    respondente = models.ForeignKey(PessoaFisica, verbose_name='Respondente', on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Questionário'
        verbose_name_plural = 'Questionários'

    def __str__(self):
        return f'Questionário - {self.respondente}'
    
    def gerar_perguntas(self):
        for pergunta in self.instrumento_avaliativo.pergunta_set.all():
            kwargs = dict(pergunta=pergunta, questionario=self)
            if not PerguntaQuestionario.objects.filter(**kwargs).exists():
                PerguntaQuestionario.objects.create(**kwargs)
    
    def save(self, *args, **kwargs):
        pk = self.pk
        super().save(*args, **kwargs)
        if pk is None:
            self.gerar_perguntas()

    def get_perguntas(self):
        return self.perguntaquestionario_set.fields('pergunta', 'resposta')
    
    @meta('Progresso')
    def get_progresso(self):
        respondido = self.perguntaquestionario_set.filter(resposta__isnull=False).exists()
        return Progress(100 if respondido else 0)

class PerguntaQuestionarioQuerySet(models.QuerySet):
    def all(self):
        return self

class PerguntaQuestionario(models.Model):
    questionario = models.ForeignKey(Questionario, verbose_name='Questionário', on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, verbose_name='Pergunta', on_delete=models.CASCADE)
    resposta = models.CharField(verbose_name='Resposta', null=True, blank=True)

    class Meta:
        verbose_name = 'Pergunta de Questionário'
        verbose_name_plural = 'Perguntas de Questionário'

    objects = PerguntaQuestionarioQuerySet()

    def __str__(self):
        return f'{self.pergunta} \nR: {self.resposta or "-"}'
    
    @meta('Respondente')
    def get_responente(self):
        return self.questionario.respondente
