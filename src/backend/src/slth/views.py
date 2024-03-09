from json import JSONEncoder
from typing import Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django import forms

ENDPOINTS = {}
FIELD_TYPES = {
    forms.CharField: 'text',
    forms.EmailField: 'email',
    forms.IntegerField: 'number'
}


class InlineField(forms.Field):
    def __init__(self, *args, form=None, min=1, max=3, **kwargs):
        self.form = form
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


@csrf_exempt
def dispatcher(request, name):
    try:
        cls = ENDPOINTS[name]
        return cls(request).to_response()
    except KeyError:
        return ApiResponse({}, status=404)
    

def serialize(obj, prefix=None):
    if isinstance(obj, forms.Form):
        data = dict(type='form', fields=[])
        if prefix:
            data['fields'].append(dict(type='hidden', name=prefix))
        for name, field in obj.fields.items():
            if isinstance(field, InlineField):
                value = []
                for i in range(1, field.max + 1):
                    value.append(serialize(field.form(data=obj.data), prefix=f'{name}__{i}'))
                data['fields'].append(dict(type='inline', min=field.min, max=field.max, name=name, label=field.label, value=value))
            else:
                ftype = FIELD_TYPES.get(type(field), 'text')
                value = field.initial or obj.initial.get(name)
                fname = name if prefix is None else f'{prefix}__{name}'
                data['fields'].append(dict(type=ftype, name=fname, label=field.label, value=value))
        return data
    return obj

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
        if name != 'Endpoint': ENDPOINTS[cls.__name__.lower()] = cls
        return cls


class Endpoint(metaclass=EnpointMetaclass):
    form = None

    def __init__(self, request):
        self.request = request

    def get_form(self, data):
        return self.form(data=data) if self.form else None
        
    def get(self):
        form = self.get_form(self.request.GET)
        if form:
            return serialize(form)
        return {}
    
    def post(self):
        data = {}
        errors = {}
        inline_data = {}
        form = self.get_form(self.request.POST)
        inline_fields = {name: field for name, field in form.fields.items() if isinstance(field, InlineField)}
        if form:
            if form.is_valid():
                for inline_field_name, inline_field in inline_fields.items():
                    inline_data[inline_field_name] = []
                    for i in range(1, inline_field.max + 1):
                        prefix = f'{inline_field_name}__{i}'
                        if form.data.get(prefix):
                            inline_form_data = {}
                            for name in inline_field.form.base_fields:
                                inline_form_field_name = f'{inline_field_name}__{i}__{name}'
                                inline_form_data[name] = form.data.get(inline_form_field_name)
                            inline_form = inline_field.form(data=inline_form_data)
                            if inline_form.is_valid():
                                inline_data[inline_field_name].append(inline_form.cleaned_data)
                            else:
                                errors.update({f'{inline_field_name}__{i}__{name}': error for name, error in inline_form.errors.items()})
                data.update({field_name: form.cleaned_data.get(field_name) for field_name in form.fields if field_name not in inline_fields}) 
            else:
                errors.update(form.errors)
        if errors:
            return dict(message='Error', errors=errors)
        else:
            self.save(data, inline_data=inline_data)
            return dict(message='Success')
    
    def save(self, data, inline_data=None):
        pass
    
    def check_permission(self):
        return True
    
    def to_response(self):
        method = self.request.method.lower()
        if method == 'get':
            data = self.get()
        elif method == 'post':
            data = self.post()
        else:
            data = {}
        return ApiResponse(data)
        

class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class PhoneForm(forms.Form):
    ddd = forms.IntegerField(label='DDD')
    numero = forms.CharField(label='Número')

class RegisterForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    telefones = InlineField(label='Telefones', form=PhoneForm, max=2)

class Register(Endpoint):
    form = RegisterForm

    def save(self, data, inline_data=None):
        print(data, inline_data)

print(ENDPOINTS)