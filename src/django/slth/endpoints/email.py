from slth import endpoints
from ..models import Email


class Emails(endpoints.ListEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class Add(endpoints.AddEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class Edit(endpoints.EditEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class Delete(endpoints.DeleteEndpoint[Email]):
    def check_permission(self):
        return self.check_role()


class View(endpoints.ViewEndpoint[Email]):
    def check_permission(self):
        return self.check_role()
