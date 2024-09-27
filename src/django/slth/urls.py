import os
import slth
from django.apps import apps
from django.conf import settings
from django.urls import path, re_path
from . import views

urlpatterns = [
    # re_path(r'^(?P<path>.*)/$', views.dispatcher),
]

for app_label in settings.INSTALLED_APPS:
    try:
        app = apps.get_app_config(app_label.split('.')[-1])
        fromlist = app.module.__package__.split('.')
        module = __import__('{}.{}'.format(app_label, 'endpoints'), fromlist=fromlist)
        if os.path.dirname(module.__file__).endswith('endpoints'):
            for name in [name for name in os.listdir(os.path.dirname(module.__file__)) if name.endswith('.py') and not name.startswith('__init__')]:
                __import__('{}.{}.{}'.format(app_label, 'endpoints', name[0:-3]), fromlist=fromlist)
    except ModuleNotFoundError as e:
        if not e.name.endswith('endpoints'):
            raise e
    except BaseException as e:
        raise e


for cls in slth.ENDPOINTS.values():
    pattern = cls.get_api_url_pattern()
    urlpatterns.append(path(pattern, views.dispatcher))
    #print(f'/api/{pattern}')
#print()
