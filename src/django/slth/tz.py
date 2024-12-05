import pytz
from datetime import datetime
from django.utils import timezone


def now():
    return datetime.now().astimezone(timezone.get_current_timezone()).replace(tzinfo=None)

def today():
    return now().date()

def localtime(tz, _datetime=None):
    return (_datetime or datetime.now()).replace(tzinfo=timezone.get_default_timezone()).astimezone(pytz.timezone(tz)).replace(tzinfo=None)
