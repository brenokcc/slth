from django.conf import settings
from .. import endpoints
from ..components import IconSet


class Icons(endpoints.PublicEndpoint):
    class Meta:
        modal = True
        verbose_name = "Ícones"

    def get(self):
        return IconSet()

    def check_permission(self):
        return settings.DEBUG
    
    def contribute(self, entrypoint):
        return self.request.user.is_authenticated
