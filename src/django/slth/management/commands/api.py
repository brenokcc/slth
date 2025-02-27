import os
from django.apps import apps
from django.utils.text import slugify
from django.core.management.commands.test import Command

TEMPLATE = """from slth import endpoints
from ..models import *


class {plural}(endpoints.ListEndpoint[{model}]):
    class Meta:
        verbose_name = '{verbose_name_plural}'

    def get(self):
        return (
            super().get()
            .actions('{lower}.cadastrar', '{lower}.editar', '{lower}.excluir')
        )


class Cadastrar(endpoints.AddEndpoint[{model}]):
    class Meta:
        verbose_name = 'Cadastrar {verbose_name}'

    def get(self):
        return (
            super().get()
        )
    

class Editar(endpoints.EditEndpoint[{model}]):
    class Meta:
        verbose_name = 'Editar {verbose_name}'

    def get(self):
        return (
            super().get()
        )


class Excluir(endpoints.DeleteEndpoint[{model}]):
    class Meta:
        verbose_name = 'Excluir {verbose_name}'

    def get(self):
        return (
            super().get()
        )

"""

class Command(Command):
    
    def handle(self, *args, **options):
        for model in apps.get_models():
            if model._meta.app_label == "api":
                content = TEMPLATE.format(
                    plural = slugify(model._meta.verbose_name_plural).replace('-de-', '-').replace('-', '').title(),
                    model = model.__name__,
                    lower = model.__name__.lower(),
                    verbose_name = model._meta.verbose_name,
                    verbose_name_plural = model._meta.verbose_name_plural,
                )
                file_path = f'api/endpoints/{model.__name__.lower()}.py'
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as file:
                        file.write(content)
