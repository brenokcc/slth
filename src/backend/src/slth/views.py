
import sys
import slth
import traceback
from .models import Token
from typing import Any
from django.conf import settings
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import forms
from .exceptions import JsonResponseException
from .serializer import serialize


@csrf_exempt
def dispatcher(request, **kwargs):
    if request.method == 'OPTIONS':
        return ApiResponse({})
    else:
        if('application' not in request.path and 'test' not in sys.argv): import time; time.sleep(0.5)
        if 'HTTP_AUTHORIZATION' in request.META:
            token = Token.objects.filter(key=request.META['HTTP_AUTHORIZATION'].split()[1]).first()
            if token:
                request.user = token.user
        tokens = request.path.split('/')
        cls = slth.ENDPOINTS.get(tokens[2])
        if cls:
            try:
                return cls(*kwargs.values()).contextualize(request).to_response()
            except JsonResponseException as e:
                return ApiResponse(e.data)
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
