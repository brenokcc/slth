from slth.db import models, role, meta
from slth.components import Image, Banner, Map, Steps, QrCode,\
    Badge, Status, Progress, Boxes, Shell, FileLink, Image, FileViewer
from django.contrib.auth.models import Group, User

class Telefone(models.Model):
    ddd = models.IntegerField('DDD', mask="99")
    numero = models.CharField('Número', max_length=25, mask="99999-9999")

    def __str__(self):
        return '({}) {}'.format(self.ddd, self.numero)


class PessoaQuerySet(models.QuerySet):
    def com_telefone_pessoal(self):
        return self.filter(telefone_pessoal__isnull=False)

    def sem_telefone_pessoal(self):
        return self.filter(telefone_pessoal__isnull=False)

    def homens(self):
        return self.filter(sexo='M').fields('nome', 'data_nascimento').filters('casado')

    def mulheres(self):
        return self.filter(sexo='F').calendar('data_nascimento')

class Pessoa(models.Model):
    nome = models.CharField('Nome', max_length=255, help_text="Nome completo")
    sexo = models.CharField('Sexo', choices=[['M', 'Masculino'], ['F', 'Femino']], default='M')
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    salario = models.DecimalField('Salário', null=True, blank=True)
    casado = models.BooleanField('Casado?', blank=True, default=False)
    sexo = models.CharField('Sexo', choices=[['M', 'Masculino'], ['F', 'Feminino']], null=True, blank=True)
    cor_preferida = models.ColorField('Cor Preferida', null=True, blank=True)
    telefone_pessoal = models.OneToOneField(
        Telefone, verbose_name='Telefone Pessoal', related_name='p1', on_delete=models.CASCADE, null=True, blank=True,
        fields=[('ddd', 'numero')]
    )
    telefones_profissionais = models.OneToManyField(Telefone, verbose_name='Telefones Profissionais', fields=[('ddd', 'numero')])
    foto = models.ImageField(verbose_name='Foto', upload_to='fotos', null=True, blank=True)
    objects = PessoaQuerySet()

    def __str__(self):
        return self.nome

    @meta('Quantidade de Telefones Profissionais')
    def get_qtd_telefones_profissionais(self):
        return self.telefones_profissionais.count()

    @meta('Grupos')
    def get_grupos(self):
        return Group.objects.all()

    @meta('Usuários')
    def get_usuarios(self):
        return User.objects.all()
    
    @meta('Foto')
    def get_foto(self):
        # return FileViewer(self.foto)
        return Image(self.foto, width=100, round=True)
    
    def get_hello(self):
        return dict(type='hello-world', name=self.nome)

class Cidade(models.Model):
    nome = models.CharField('Nome', max_length=255)
    prefeito = models.ForeignKey(Pessoa, verbose_name='Prefeito', on_delete=models.CASCADE)
    vereadores = models.ManyToManyField(Pessoa, verbose_name='Vereadores', blank=True, related_name='r1')

    def __str__(self):
        return self.nome

    @meta('Imagem')
    def get_imagem(self):
        return Image('https://static.vecteezy.com/ti/vetor-gratis/t2/1591382-banner-vermelho-de-feliz-natal-e-feliz-ano-novo-vetor.jpg')

    @meta('Banner')
    def get_banner(self):
        return Banner('https://static.vecteezy.com/ti/vetor-gratis/t2/1591382-banner-vermelho-de-feliz-natal-e-feliz-ano-novo-vetor.jpg')

    @meta('Mapa')
    def get_mapa(self):
        return Map('-5.8496847', '-35.2038551')

    @meta('Steps')
    def get_steps(self):
        steps = Steps()
        steps.append('Passo 01', True)
        steps.append('Descrição do Passo 02', True)
        steps.append('Passo 03', False)
        steps.append('Passo 04', False)
        steps.append('Passo 03', False)
        steps.append('Passo 04', False)
        return steps

    @meta('QrCode')
    def get_qrcode(self):
        return QrCode('Teste')

    @meta('Badge')
    def get_badge(self):
        return Badge('green', 'Aprovado')

    @meta('Status')
    def get_status(self):
        return Status('warning', 'Pendente')


    @meta('Progresso')
    def get_progresso(self):
        return Progress(89)

    @meta('Boxes')
    def get_boxes(self):
        boxes = Boxes('Acesso Rápido')
        boxes.append('user', 'Pessoas', '#')
        boxes.append('check', 'Verificar', '#')
        return boxes

    @meta('Shell')
    def get_shell(self):
        return Shell("print('Hello World!')")

    @meta('Link')
    def get_link(self):
        return FileLink('http://localhost:8000/api/media/teste.pdf')


@role('Administrador', username='email', active='is_admin')
class Funcionario(models.Model):
    email = models.CharField('E-mail')
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return self.email

@role('Supervisor', username='supervisor__email', rede='pk')
class Rede(models.Model):
    nome = models.CharField('Nome')
    supervisor = models.ForeignKey(Funcionario)

    def __str__(self):
        return self.nome

@role('Gerente', username='gerente__email', loja='pk', rede='rede')
@role('Vendedor', username='vendedores__email', loja='pk', rede='rede')
class Loja(models.Model):
    rede = models.ForeignKey(Rede)
    nome = models.CharField('Nome')
    gerente = models.ForeignKey(Funcionario)
    vendedores = models.ManyToManyField(Funcionario, related_name='r1')

    def __str__(self):
        return self.nome

class Produto(models.Model):
    loja = models.ForeignKey(Loja)
    nome = models.CharField('Nome')

    def __str__(self):
        return self.nome
    

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


