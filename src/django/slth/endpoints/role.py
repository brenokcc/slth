from . import ListEndpoint, DeleteEndpoint
from ..models import Role


class Roles(ListEndpoint[Role]):
    def get(self):
        return super().get().actions('role.delete')
    

class Delete(DeleteEndpoint[Role]):
    class Meta:
        icon = 'x'
        verbose_name = 'Excluir Papel'

    def get(self):
        return (
            super().get()
        )
