import pytz
from django.utils import timezone


def to_gmt_format(tz_name):
    # Converts America/Recife to Etc/GMT-3, for example
    if not tz_name.startswith('Etc/GMT'):
        offset = int(timezone.now().astimezone(pytz.timezone(tz_name)).strftime('%z')[:3])
        return 'Etc/GMT{}'.format(offset)
    return tz_name

def get_timezone(tz_name):
    tz_name = to_gmt_format(tz_name)
    return pytz.timezone(tz_name) 

def get_current_timezone():
    tz_name = timezone.get_current_timezone().key
    return get_timezone(tz_name)

def get_default_timezone():
    tz_name = timezone.get_default_timezone().key
    return get_timezone(tz_name)

def activate(tz_name):
    timezone.activate(tz_name)

def deactivate():
    timezone.deactivate()

def system_datetime(tz_name, datetime=None):
    # Returns the datetime in the default timezone relative to a specific timezone
    # If default timezone is Etc/GMT-3 and datetime is 10:00 then 11:00 will be returned for tz_name=Etc/GMT-4
    return datetime.replace(tzinfo=get_default_timezone()).astimezone(get_timezone(tz_name)).replace(tzinfo=None) if datetime else None
