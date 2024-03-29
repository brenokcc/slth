
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
            slth.ENDPOINTS[cls.get_qualified_name()] = cls
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
            if isinstance(self.serializer, dict):
                return self.serializer
            else:
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
    
    def serialize(self):
        method = self.request.method.lower()
        if method == 'get':
            data = self.get()
        elif method == 'post':
            data = self.post()
        else:
            data = {}
        return serialize(data)
    
    def to_response(self):
        return ApiResponse(self.serialize(), safe=False)
    
    @classmethod
    def get_api_name(cls):
        return cls.__name__.lower()
        name = []
        for c in cls.__name__:
            if name and c.isupper():
                name.append('-')
            name.append(c.lower())
        return ''.join(name)
    
    @classmethod
    def get_pretty_name(cls):
        name = []
        for c in cls.__name__:
            if name and c.isupper():
                name.append(' ')
            name.append(c)
        return ''.join(name)
    
    @classmethod
    def get_qualified_name(cls):
        return '{}.{}'.format(cls.__module__, cls.__name__).lower()
    
    @classmethod
    def get_api_url(cls, *args):
        url = '/api/{}/'.format(cls.get_api_name())
        for arg in args:
            url = '{}{}/'.format(url, arg)
        return url
    
    @classmethod
    def has_args(cls):
        return len(inspect.getfullargspec(cls.__init__).args) > 2
    
    @classmethod
    def get_api_url_pattern(cls):
        args = inspect.getfullargspec(cls.__init__).args[2:]
        pattern = '{}/'.format(cls.get_api_name())
        for arg in args:
            pattern = '{}{}/'.format(pattern, '<int:{}>'.format(arg))
        return pattern
    
    @classmethod
    def get_api_metadata(cls, url):
        action_name = cls.get_metadata('verbose_name')
        return dict(type='action', name=action_name, url=url, key=cls.get_api_name())
    
    @classmethod
    def get_metadata(cls, key):
        value = None
        metaclass = getattr(cls, 'Meta', None)
        if metaclass:
            value = getattr(metaclass, key, None)
        if value is None and key == 'verbose_name':
            value = cls.get_pretty_name()
        return value
        

class ChildEndpoint(Endpoint):
    def __init__(self, request, parent, *args):
        self.parent = parent
        super().__init__(request, *args)


class FormFactory:
    def __init__(self, request, instance):
        self.request = request
        self.instance = instance
        self.fieldsets = {}
        self.fieldlist = []

    def fields(self, *names):
        self.fieldlist.extend(names)
        return self

    def fieldset(self, title, *fields):
        self.fieldsets['title'] = title
        for names in fields:
            for name in names:
                if isinstance(name, str):
                    self.fieldlist.append(name)
                else:
                    self.fieldlist.extend(names)
        return self
    
    def form(self):
        class Form(ModelForm):
            class Meta:
                model = type(self.instance)
                fields = self.fieldlist or '__all__'
        
        return Form(instance=self.instance, request=self.request)

class Login(Endpoint):
    def __init__(self, request):
        super().__init__(request)
        self.form = LoginForm(request=request)

