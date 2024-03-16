from slth.db import models

class Telefone(models.Model):
    ddd = models.IntegerField('DDD')
    numero = models.CharField('Número', max_length=25)

    def __str__(self):
        return '({}) {}'.format(self.ddd, self.numero)

class Pessoa(models.Model):
    nome = models.CharField('Nome', max_length=255)
    telefone_pessoal = models.OneToOneField(Telefone, verbose_name='Telefone Pessoal', related_name='p1', on_delete=models.CASCADE, null=True, blank=True)
    telefones_profissionais = models.OneToManyField(Telefone, verbose_name='Telefones Profissionais')

    def __str__(self):
        return self.nome
    
class Cidade(models.Model):
    nome = models.CharField('Nome', max_length=255)
    prefeito = models.ForeignKey(Pessoa, verbose_name='Prefeito', on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
    