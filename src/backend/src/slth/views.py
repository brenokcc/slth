
import slth
import traceback
from django.apps import apps
from typing import Any
from django.conf import settings
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import forms
from .exceptions import JsonResponseException
from .serializer import serialize


@csrf_exempt
def dispatcher(request, path):
    tokens = path.split('/')
    cls = slth.ENDPOINTS.get(tokens[0].replace('-', ''))
    if cls:
        try:
            return cls(request, *tokens[1:]).to_response()
        except Exception as e:
            traceback.print_exc() 
            return ApiResponse(data=dict(error=str(e)), safe=False, status=500)
    else:
        return ApiResponse({}, status=404)
    

class ApiResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "*"
        self["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH";
        self["Access-Control-Max-Age"] = "600"


for app_label in settings.INSTALLED_APPS:
    try:
        app = apps.get_app_config(app_label.split('.')[-1])
        fromlist = app.module.__package__.split('.')
        if app_label != 'slth':
            __import__('{}.{}'.format(app_label, 'endpoints'), fromlist=fromlist)
    except ImportError as e:
        if not e.name.endswith('endpoints'):
            raise e
    except BaseException as e:
        raise e


for cls in slth.ENDPOINTS.values():
    print(cls.get_api_url())