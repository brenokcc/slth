from slth import endpoints
from ..models import Job


class Jobs(endpoints.ListEndpoint[Job]):
    def check_permission(self):
        return self.check_role()


class Delete(endpoints.DeleteEndpoint[Job]):
    def check_permission(self):
        return self.check_role()


class View(endpoints.ViewEndpoint[Job]):
    def check_permission(self):
        return self.check_role()


class Progress(endpoints.InstanceEndpoint[Job]):
    def get(self):
        return self.instance.get_progress()
