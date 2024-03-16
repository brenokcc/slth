from django.db import models

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
    telefone_pessoal = models.OneToOneField(Telefone, verbose_name='Telefone Pessoal', related_name='p1', on_delete=models.CASCADE, null=True, blank=True)
    telefones_profissionais = models.OneToManyField(Telefone, verbose_name='Telefones Profissionais')

    objects = PessoaQuerySet()

    def __str__(self):
        return self.nome
    
class Cidade(models.Model):
    nome = models.CharField('Nome', max_length=255)
    prefeito = models.ForeignKey(Pessoa, verbose_name='Prefeito', on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
    