from slth import endpoints
from ..models import Email


class Emails(endpoints.ListEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class Add(endpoints.AddEndpoint[Email]):
    class Meta:
        modal = True
        icon = 'mail-bulk'
    
    def check_permission(self):
        return self.check_role()
    
    def get_verbose_name(self):
        return 'Enviar E-mail'


class Edit(endpoints.EditEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class Delete(endpoints.DeleteEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class View(endpoints.ViewEndpoint[Email]):
    def check_permission(self):
        return self.check_role()
