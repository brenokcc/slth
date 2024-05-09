from django.db import transaction
from project.comum.models import ProfissionalSaude, ProfissionalVinculo, Solicitacao
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            for solicitacao in Solicitacao.objects.all():
                solicitacao.solicitante = solicitacao.vinculo.profissional
                solicitacao.estabelecimento = solicitacao.vinculo.estabelecimento
                solicitacao.especialista = solicitacao.get_especialista()
                solicitacao.save()
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
