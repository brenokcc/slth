from slth import endpoints
from ..models import Settings as SettingsModel


class Settings(endpoints.ListEndpoint[SettingsModel]):
    class Meta:
        modal = False
        verbose_name = 'Configurações'

    def get(self):
        return (
            super().get()
            .actions('settings.add', 'settings.view', 'settings.edit', 'settings.delete')
        )


class Add(endpoints.AddEndpoint[SettingsModel]):
    class Meta:
        icon = 'plus'
        verbose_name = 'Cadastrar Configuração'

    def get(self):
        return (
            super().get()
        )

        
class View(endpoints.ViewEndpoint[SettingsModel]):
    class Meta:
        modal = False
        icon = 'eye'
        verbose_name = 'Visualizar Configuração'

    def get(self):
        return (
            super().get()
        )
    

class Edit(endpoints.EditEndpoint[SettingsModel]):
    class Meta:
        icon = 'pen'
        verbose_name = 'Editar Configuração'

    def get(self):
        return (
            super().get()
        )


class Delete(endpoints.DeleteEndpoint[SettingsModel]):
    class Meta:
        icon = 'trash'
        verbose_name = 'Excluir Configuração'

    def get(self):
        return (
            super().get()
        )

