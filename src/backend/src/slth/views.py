
import sys
import slth
import traceback
from .models import Token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .exceptions import JsonResponseException
from .serializer import serialize
from .utils import build_url


@csrf_exempt
def dispatcher(request, **kwargs):
    if request.method == 'OPTIONS':
        return ApiResponse({})
    else:
        if(0 and 'application' not in request.path and 'test' not in sys.argv): import time; time.sleep(0.5)
        if 'HTTP_AUTHORIZATION' in request.META:
            token = Token.objects.filter(key=request.META['HTTP_AUTHORIZATION'].split()[1]).first()
            if token:
                request.user = token.user
        if request.path == '/':
            cls = slth.ENDPOINTS.get(slth.APPLICATON['index'])
            url = build_url(request, cls.get_api_url())
            return ApiResponse(dict(type='redirect', url=url))
        else:
            cls = slth.ENDPOINTS.get(request.path.split('/')[2])
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
