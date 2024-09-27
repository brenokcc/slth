from . import ListEndpoint, InstanceEndpoint
from ..models import Deletion


class Deletions(ListEndpoint[Deletion]):
    pass


class Restore(InstanceEndpoint[Deletion]):
    class Meta:
        verbose_name = 'Restaurar'

    def get(self):
        return super().formfactory().fields()
    
    def post(self):
        self.instance.restore()
        return super().post()
    
    def check_permission(self):
        return super().check_permission() and not self.instance.restored
