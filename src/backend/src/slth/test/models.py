from slth.db import models, role, meta
from django.contrib.auth.models import Group, User

class Telefone(models.Model):
    ddd = models.IntegerField('DDD')
    numero = models.CharField('Número', max_length=25)

    def __str__(self):
        return '({}) {}'.format(self.ddd, self.numero)


class PessoaQuerySet(models.QuerySet):
    def com_telefone_pessoal(self):
        return self.filter(telefone_pessoal__isnull=False)
    
    def sem_telefone_pessoal(self):
        return self.filter(telefone_pessoal__isnull=False)

class Pessoa(models.Model):
    nome = models.CharField('Nome', max_length=255)
    sexo = models.CharField('Sexo', choices=[['M', 'Masculino'], ['F', 'Femino']], default='M')
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    telefone_pessoal = models.OneToOneField(Telefone, verbose_name='Telefone Pessoal', related_name='p1', on_delete=models.CASCADE, null=True, blank=True)
    telefones_profissionais = models.OneToManyField(Telefone, verbose_name='Telefones Profissionais')

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
    
class Cidade(models.Model):
    nome = models.CharField('Nome', max_length=255)
    prefeito = models.ForeignKey(Pessoa, verbose_name='Prefeito', on_delete=models.CASCADE)
    vereadores = models.ManyToManyField(Pessoa, verbose_name='Vereadores', blank=True, related_name='r1')

    def __str__(self):
        return self.nome
    
@role('Administrador', username='email', active='is_admin')
class Funcionario(models.Model):
    email = models.CharField('E-mail')
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nome

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
