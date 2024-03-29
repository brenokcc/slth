
import json
import inspect
from django.apps import apps
from typing import Any
from django.conf import settings
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import LoginForm, ModelForm, Form
from . import serializer


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

    def __init__(self, *args):
        self.request = None

    def contextualize(self, request):
        self.request = request
        return self

    def objects(self, model):
        return apps.get_model(model).objects
        
    def get(self):
        return {}
    
    def post(self):
        data = self.get()
        if isinstance(data, FormFactory):
            data = data.form(self.request).post()
        if isinstance(data, Form) or isinstance(data, ModelForm):
            data = data.post()
        return data
    
    def save(self, data):
        pass
    
    def check_permission(self):
        return True
    
    def serialize(self):
        if self.request.method == 'GET':
            data = self.get()
        elif self.request.method == 'POST':
            data = self.post()
        else:
            data = {}
       
        if isinstance(data, models.QuerySet):
            data = data.contextualize(self.request)
        elif isinstance(data, serializer.Serializer):
            data = data.contextualize(self.request)
        elif isinstance(data, FormFactory):
            data = data.form(self.request)
        
        return serializer.serialize(data)
    
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
        return len(inspect.getfullargspec(cls.__init__).args) > 1
    
    @classmethod
    def get_api_url_pattern(cls):
        args = inspect.getfullargspec(cls.__init__).args[1:]
        pattern = '{}/'.format(cls.get_api_name())
        for arg in args:
            pattern = '{}{}/'.format(pattern, '<int:{}>'.format(arg))
        return pattern
    
    @classmethod
    def get_api_metadata(cls, url):
        action_name = cls.get_metadata('verbose_name')
        return dict(type='action', title=action_name, name=action_name, url=url, key=cls.get_api_name())
    
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
    pass


class FormFactory:
    def __init__(self, instance, delete=False):
        self.instance = instance
        self.fieldsets = {}
        self.fieldlist = []
        self.serializer = None
        self.delete = delete

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
    
    def display(self, serializer):
        self.serializer = serializer
        return self

    def form(self, request):
        class Form(ModelForm):
            class Meta:
                title = '{} {}'.format(
                    'Excluir' if self.delete else ('Editar' if self.instance.pk else 'Cadastrar'),
                    type(self.instance)._meta.verbose_name
                )
                model = type(self.instance)
                fields = () if self.delete else (self.fieldlist or '__all__')
        
        form = Form(instance=self.instance, request=request, delete=self.delete)
        if self.serializer:
            form.display(self.serializer)
        return form

class Login(Endpoint):
    def get(self):
        return LoginForm(request=self.request)

