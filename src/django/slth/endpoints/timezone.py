from slth import endpoints
from ..models import TimeZone


class Timezones(endpoints.ListEndpoint[TimeZone]):
    def check_permission(self):
        return self.check_role()


class Add(endpoints.AddEndpoint[TimeZone]):
    pass