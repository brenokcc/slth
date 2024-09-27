from .. import endpoints
from ..models import Log


class Logs(endpoints.ListEndpoint[Log]):
    class Meta:
        modal = False
