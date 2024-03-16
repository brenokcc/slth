
import json
import inspect
from django.apps import apps
from typing import Any
from django.conf import settings
from django.db import transaction, models
from django.forms import modelform_factory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import LoginForm, ModelForm
from .exceptions import JsonResponseException
from .serializer import serialize


import slth


class ApiResponse(JsonResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "*"
        self["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE, PATCH";
        self["Access-Control-Max-Age"] = "600"


class EnpointMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if name not in ('Endpoint', 'ChildEndpoint') and 'ChildEndpoint' not in [cls.__name__ for cls in bases]:
            slth.ENDPOINTS[cls.__name__.lower()] = cls
        return cls


class Endpoint(metaclass=EnpointMetaclass):

    def __init__(self, request, *args):
        self.form = None
        self.serializer = None
        self.request = request

    def objects(self, model):
        return apps.get_model(model).objects
        
    def get(self):
        if self.form:
            return self.form.serialize()
        elif self.serializer:
            return self.serializer.serialize()
        else:
            return {}
    
    def post(self):
        if self.form:
            return self.form.post()
        else:
            return {}
    
    def save(self, data):
        pass
    
    def check_permission(self):
        return True
    
    def to_response(self):
        if self.form and isinstance(self.form, FormFactory):
            self.form = self.form.build()
        method = self.request.method.lower()
        if method == 'get':
            data = self.get()
        elif method == 'post':
            data = self.post()
        else:
            data = {}
        return ApiResponse(serialize(data), safe=False)
    
    @classmethod
    def get_api_name(cls):
        name = []
        for c in cls.__name__:
            if name and c.isupper():
                name.append('-')
            name.append(c.lower())
        return ''.join(name)
    
    @classmethod
    def get_api_url(cls, *args):
        url = '/api/{}/'.format(cls.get_api_name())
        for arg in args:
            url = '{}{}/'.format(url, arg)
        return url
    
    @classmethod
    def get_api_url_pattern(cls):
        args = inspect.getfullargspec(cls.__init__).args[2:]
        pattern = '{}/'.format(cls.get_api_name())
        for arg in args:
            pattern = '{}{}/'.format(pattern, '<int:{}>'.format(arg))
        return pattern
        

class ChildEndpoint(Endpoint):
    def __init__(self, request, parent, *args):
        self.parent = parent
        super().__init__(request, *args)


class FormFactory:
    def __init__(self, instance, request):
        self.instance = instance
        self.request = request
        self.fieldsets = {}
        self.fields = []

    def fieldset(self, title, *fields):
        self.fieldsets['title'] = fields
        for names in fields:
            for name in names:
                if isinstance(name, str):
                    self.fields.append(name)
                else:
                    self.fields.extend(names)
        return self
    
    def build(self):
        class Form(ModelForm):
            class Meta:
                model = type(self.instance)
                fields = self.fields
        
        return Form(instance=self.instance, request=self.request)

class Login(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = LoginForm(request=request)

