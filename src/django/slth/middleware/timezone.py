import pytz
from datetime import datetime
from django.utils import timezone

def now():
    return datetime.now().astimezone(timezone.get_current_timezone()).replace(tzinfo=None)

def today():
    return now().date()

def local(dt, tz):
    from_timezone = timezone.get_default_timezone()
    to_timezone = pytz.timezone(tz)
    from_timezone.localize(dt).astimezone(to_timezone).replace(tzinfo=None)


class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.path[0] == '/' and (request.META.get('HTTP_TZ') or request.META.get('TZ'))
        if tz:
            timezone.activate(pytz.timezone(tz))
        response = self.get_response(request)
        if tz:
            timezone.deactivate()
        return response
