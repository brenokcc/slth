from slth.db import models, role, meta
from slth.components import Image


class PessoaFisicaQuerySet(models.QuerySet):
    def all(self):
        return self

@role('pf', 'cpf')
class PessoaFisica(models.Model):
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='pessoas_fisicas')
    cpf = models.CharField(verbose_name='CPF')
    nome = models.CharField(verbose_name='Nome')
    telefone = models.CharField(verbose_name='Telefone')
    email = models.CharField(verbose_name='E-mail')

    class Meta:
        verbose_name = 'Pessoa Física'
        verbose_name_plural = 'Pessoas Físicas'

    objects = PessoaFisicaQuerySet()

    def __str__(self):
        return f'{self.nome}'
    
    @meta('Foto')
    def get_foto(self):
        return Image(self.foto, width=75, round=True)


class EstadoQuerySet(models.QuerySet):
    def all(self):
        return self


class Estado(models.Model):
    sigla = models.CharField(verbose_name='Sigla')
    nome = models.CharField(verbose_name='Nome')
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    objects = EstadoQuerySet()

    def __str__(self):
        return f'{self.sigla}'
    
    def get_cidades(self):
        return self.cidade_set.all()


class MunicipioQuerySet(models.QuerySet):
    def all(self):
        return self


class Municipio(models.Model):
    nome = models.CharField(verbose_name='Nome')
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Município'
        verbose_name_plural = 'Municípios'

    objects = MunicipioQuerySet()

    def __str__(self):
        return f'{self.nome} / {self.estado}'
    

class InstrumentoAvaliativoQuerySet(models.QuerySet):
    def all(self):
        return self


class InstrumentoAvaliativo(models.Model):
    nome = models.CharField(verbose_name='Nome')
    responsavel = models.ForeignKey(PessoaFisica, verbose_name='Responsável', on_delete=models.CASCADE)
    data_inicio = models.DateField(verbose_name='Início')
    data_termino = models.DateField(verbose_name='Término')
    instrucoes = models.TextField(verbose_name='Instruções', null=True, blank=True)

    class Meta:
        verbose_name = 'Instrumento Avaliativo'
        verbose_name_plural = 'Instrumentos Avaliativos'

    objects = InstrumentoAvaliativoQuerySet()

    def __str__(self):
        return f'Instrumento Avaliativo {self.id}'

class OpcaoResposta(models.Model):
    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        verbose_name = 'Opção de Resposta'
        verbose_name_plural = 'Opções de Resposta'

    def __str__(self):
        return self.descricao

class PerguntaQuerySet(models.QuerySet):
    def all(self):
        return self


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

    objects = PerguntaQuerySet()

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
    


class QuestionarioQuerySet(models.QuerySet):
    def all(self):
        return self


class Questionario(models.Model):
    instrumento_avaliativo = models.ForeignKey(InstrumentoAvaliativo, verbose_name='Instrumento Avaliativo', on_delete=models.CASCADE)
    respondente = models.ForeignKey(PessoaFisica, verbose_name='Respondente', on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'Questionário'
        verbose_name_plural = 'Questionários'

    objects = QuestionarioQuerySet()

    def __str__(self):
        return f'Questionário {self.id}'
    
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
        return f'Pergunta de Questionário {self.pk}'
    
    @meta('Respondente')
    def get_responente(self):
        return self.questionario.respondente


