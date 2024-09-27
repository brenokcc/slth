
import json
import sys
import slth
import socket
import traceback

from .models import Token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .exceptions import JsonResponseException, ReadyResponseException
from .serializer import serialize
from .utils import build_url
from slth import APPLICATON
from django.shortcuts import render
from django.views.decorators.cache import never_cache, cache_control


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def index(request, path=None):
    vite = not socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(('127.0.0.1',5173))
    return render(request, 'index.html', dict(vite=vite, application=APPLICATON))

def service_worker(request):
    return render(request, 'service-worker.js', content_type='text/javascript')

@csrf_exempt
def dispatcher(request, **kwargs):
    if request.method == 'OPTIONS':
        return ApiResponse({})
    else:
        if(1 and 'application' not in request.path and 'test' not in sys.argv): import time; time.sleep(0)
        if 'HTTP_AUTHORIZATION' in request.META:
            token = Token.objects.filter(key=request.META['HTTP_AUTHORIZATION'].split()[1]).first()
            if token:
                request.user = token.user
        elif 'token' in request.COOKIES:
            token = Token.objects.filter(key=request.COOKIES.get('token')).first()
            if token:
                request.user = token.user
        if request.path == '/':
            cls = slth.ENDPOINTS.get(slth.APPLICATON['index'])
            url = build_url(request, cls.get_api_url())
            return ApiResponse(dict(type='redirect', url=url))
        else:
            tokens = [token for token in request.path.split('/')[2:] if token and not token.isdigit()]
            cls = slth.ENDPOINTS.get('.'.join(tokens))
            if cls:
                endpoint = None
                try:
                    endpoint = cls(*kwargs.values()).contextualize(request)
                    if endpoint.check_permission():
                        endpoint.start_audit_trail()
                        return endpoint.to_response()
                    else:
                        url = '/api/auth/login/'
                        if request.path != '/api/dashboard/':
                            url = '{}?next={}'.format(url, request.get_full_path())
                        return ApiResponse(dict(type="redirect", url=url), status=403)
                except JsonResponseException as e:
                    return ApiResponse(e.data, safe=False)
                except ReadyResponseException as e:
                    return e.response
                except Exception as e:
                    traceback.print_exc() 
                    return ApiResponse(data=dict(error=str(e)), safe=False, status=500)
                finally:
                    if endpoint:
                        endpoint.finish_audit_trail()
            else:
                return ApiResponse({}, status=404)

class ApiResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "*"
        self["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH";
        self["Access-Control-Max-Age"] = "600"
