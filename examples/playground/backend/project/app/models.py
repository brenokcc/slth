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