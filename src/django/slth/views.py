
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
from django.shortcuts import render
from django.views.decorators.cache import never_cache, cache_control
import os
from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from .endpoints import ApiResponse
from slth.application import Application


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def index(request, path=None):
    vite = bool(os.environ.get('VITE'))
    application = Application.get_instance()
    return render(request, 'index.html', dict(vite=vite, application=application))

def service_worker(request):
    return render(request, 'service-worker.js', content_type='text/javascript')

def media(request, file_path):
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(full_path):
        return FileResponse(open(full_path, 'rb'))
    return HttpResponseNotFound()

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
            application = Application.get_instance()
            cls = slth.ENDPOINTS.get(application.dashboard.index)
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
                        if request.path not in ('/api/dashboard/', '/api/auth/logout/'):
                            url = '{}?next={}'.format(url, request.get_full_path())
                        return ApiResponse(dict(type="redirect", url=url), status=403)
                except JsonResponseException as e:
                    return ApiResponse(e.data, safe=False)
                except ReadyResponseException as e:
                    return e.response
                except Exception as e:
                    traceback.print_exc() 
                    return ApiResponse(dict(error=str(e)), safe=False, status=500)
                finally:
                    if endpoint:
                        endpoint.finish_audit_trail()
            else:
                return ApiResponse({}, status=404)
