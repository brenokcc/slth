from django.db import transaction
from project.comum.models import ProfissionalSaude, ProfissionalVinculo, Atendimento
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            for atendimento in Atendimento.objects.all():
                atendimento.profissional = atendimento.vinculo.profissional
                atendimento.estabelecimento = atendimento.vinculo.estabelecimento
                atendimento.especialista = atendimento.get_especialista()
                atendimento.save()
            for vinculo in ProfissionalVinculo.objects.all():
                profissional = vinculo.profissional
                if profissional.estabelecimento_id:
                    profissional.id = None
                profissional.estabelecimento = vinculo.estabelecimento
                profissional.especialidade = vinculo.profissao
                profissional.residente = vinculo.residente
                profissional.perceptor = vinculo.perceptor
                profissional.ativo = vinculo.ativo
                profissional.save()
