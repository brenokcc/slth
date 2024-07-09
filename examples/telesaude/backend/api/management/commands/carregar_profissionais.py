from django.db import transaction
from ...models import ConselhoClasse, Area, Especialidade, PessoaFisica, Unidade, Municipio, Estado, ProfissionalSaude
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            estado = Estado.objects.get_or_create(codigo=50, defaults=dict(sigla='MS', nome='Mato Grosso do Sul'))[0]
            municipio = Municipio.objects.get_or_create(codigo=5003702, nome='Dourados', estado=estado)[0]
            with open('profissionais.csv') as file:
                line = file.readline()
                while line:
                    tokens = line.strip().split(';')
                    nome, cpf, email, registro, sigla, conselho, unidade, especialidade = tokens
                    print(cpf, nome)
                    line = file.readline()
                    conselho = ConselhoClasse.objects.get_or_create(sigla=conselho, estado=estado)[0]
                    area = Area.objects.get_or_create(nome=especialidade)[0]
                    especialidade = Especialidade.objects.get_or_create(nome=especialidade, area=area)[0]
                    pessoa_fisica = PessoaFisica.objects.get_or_create(cpf=cpf, defaults=dict(nome=nome, email=email))[0]
                    unidade = Unidade.objects.get_or_create(nome=unidade, defaults=dict(municipio=municipio))[0]
                    ProfissionalSaude.objects.get_or_create(
                        pessoa_fisica=pessoa_fisica, unidade=unidade, especialidade=especialidade,
                        defaults=dict(registro_profissional=registro, conselho_profissional=conselho)
                    )
