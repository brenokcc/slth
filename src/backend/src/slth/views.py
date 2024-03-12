from json import JSONEncoder
from typing import Any
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group, Permission
from django import forms
from django.forms import modelform_factory

ENDPOINTS = {}
FIELD_TYPES = {
    forms.CharField: 'text',
    forms.EmailField: 'email',
    forms.BooleanField: 'boolean',
    forms.IntegerField: 'number',
    forms.ChoiceField: 'choice',
    forms.ModelChoiceField: 'choice',
    forms.MultipleChoiceField: 'choice',
    forms.ModelMultipleChoiceField: 'choice',
}


class JsonResponseException(Exception):

    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data


class InlineFormField(forms.Field):
    def __init__(self, *args, form=None, min=1, max=3, **kwargs):
        self.form = form
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


class InlineModelField(forms.Field):
    def __init__(self, *args, model=None, fields='__all__', exclude=(), min=1, max=3, **kwargs):
        self.form = modelform_factory(model, fields=fields, exclude=exclude)
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


@csrf_exempt
def dispatcher(request, path):
    tokens = path.split('/')
    cls = ENDPOINTS.get(tokens[0].replace('-', ''))
    if cls:
        return cls(request, *tokens[1:]).to_response()
    else:
        return ApiResponse({}, status=404)
    
def build_url(request, **params):
    url = "{}://{}{}".format(request.META.get('X-Forwarded-Proto', request.scheme), request.get_host(), request.path)
    for k, v in params.items():
        url = f'{url}&{k}={v}' if '?' in url else f'{url}?{k}={v}'
    return url

def serialize_form(form, request, prefix=None):
    data = dict(type='form', fields=[])
    choices_field_name = request.GET.get('choices')
    if prefix:
        value = form.instance.pk if isinstance(form, forms.ModelForm) else ''
        data['fields'].append(dict(type='hidden', name=prefix, value=value))
    for name, field in form.fields.items():
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = {}
            if isinstance(form, forms.ModelForm) and hasattr(form.instance, name):
                instances = {i: instance for i, instance in enumerate(getattr(form.instance, name).all()[0:field.max])}
            for i in range(0, field.max):
                kwargs = dict(data=form.data, instance=instances.get(i)) if isinstance(form, forms.ModelChoiceField) else dict(data=form.data)
                value.append(serialize_form(field.form(**kwargs), request, prefix=f'{name}__{i}'))
            data['fields'].append(dict(type='inline', min=field.min, max=field.max, name=name, label=field.label, required=field.required, value=value))
        else:
            ftype = FIELD_TYPES.get(type(field), 'text')
            value = field.initial or form.initial.get(name)
            fname = name if prefix is None else f'{prefix}__{name}'
            data['fields'].append(dict(type=ftype, name=fname, label=field.label, required=field.required, value=value))
            if ftype == 'choice':
                if getattr(field.choices, 'queryset') is None:
                    data['fields'][-1]['choices'] = [dict(id=k, value=v) for k, v in field.choices]
                else:
                    if choices_field_name == fname:
                        raise JsonResponseException([dict(id=obj.id, value=str(obj)) for obj in field.choices.queryset.all()])
                    else:
                        data['fields'][-1]['choices'] = build_url(request, choices=fname)
    return data

def serialize(obj):
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, models.Model):
        return dict(pk=obj.pk, str=str(obj))
    elif isinstance(obj, models.QuerySet):
        return [dict(pk=item.pk, str=str(item)) for item in obj]
    return str(obj)

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
    source = None
    form = None

    def __init__(self, request, *args):
        self.request = request
        self.args = args
        self.load()

    def load(self):
        pass

    def get_form(self, data):
        form = None
        if self.form:
            if issubclass(self.form, forms.ModelForm):
                form = self.form(data=data, instance=self.source)
            elif issubclass(self.form, forms.Form):
                form = self.form(data=data)
        return form
        
    def get(self):
        try:
            form = self.get_form(self.request.GET)
            return serialize_form(form, self.request) if form else serialize(self.source)
        except JsonResponseException as e:
            return e.data
    
    def post(self):
        data = {}
        errors = {}
        form = self.get_form(self.request.POST)
        inline_fields = {name: field for name, field in form.fields.items() if isinstance(field, InlineFormField) or isinstance(field, InlineModelField)}
        if form:
            form.is_valid()
            errors.update(form.errors)
            for inline_field_name, inline_field in inline_fields.items():
                data[inline_field_name] = []
                for i in range(0, inline_field.max):
                    prefix = f'{inline_field_name}__{i}'
                    if prefix in form.data:
                        inline_form_data = {}
                        pk = form.data.get(prefix)
                        for name in inline_field.form.base_fields:
                            inline_form_field_name = f'{inline_field_name}__{i}__{name}'
                            inline_form_data[name] = form.data.get(inline_form_field_name)
                        instance = inline_field.form._meta.model.objects.get(pk=pk) if pk else None
                        inline_form = inline_field.form(data=inline_form_data, instance=instance)
                        if inline_form.is_valid():
                            if isinstance(inline_form, forms.ModelForm):
                                data[inline_field_name].append(inline_form.instance)
                            else:
                                data[inline_field_name].append(inline_form.cleaned_data)
                        else:
                            errors.update({f'{inline_field_name}__{i}__{name}': error for name, error in inline_form.errors.items()})
            data.update({field_name: form.cleaned_data.get(field_name) for field_name in form.fields if field_name not in inline_fields}) 
        if errors:
            return dict(message='Please correct the errors.', errors=errors)
        else:
            with transaction.atomic():
                form.cleaned_data = data
                form.save()
                if isinstance(form, forms.ModelForm):
                    for inline_field_name in inline_fields:
                        relation = getattr(form.instance, inline_field_name)
                        for obj in form.cleaned_data[inline_field_name]:
                            obj.save()
                            relation.add(obj)
                return dict(message='Action successfully performed.')
    
    def save(self, data):
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
        return ApiResponse(serialize(data), safe=False)
        

class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class PhoneForm(forms.Form):
    ddd = forms.IntegerField(label='DDD')
    numero = forms.CharField(label='Número')


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ()

class UserForm(forms.ModelForm):
    groups = InlineModelField(label='Grupos', model=Group)
    class Meta:
        model = User
        fields = 'username', 'email', 'is_superuser'

class RegisterForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    telefones = InlineFormField(label='Telefones', form=PhoneForm)
    grupos = InlineFormField(label='Grupos', form=GroupForm)

    def save(self):
        print(self.cleaned_data, 88888)

class Register(Endpoint):
    form = RegisterForm


class AddUser(Endpoint):
    form = UserForm

class EditUser(Endpoint):
    form = UserForm

    def load(self):
        self.source = User.objects.get(pk=self.args[0])

class ListUsers(Endpoint):
    
    def load(self):
        self.source = User.objects.all()
    

class ViewUser(Endpoint):
    def load(self):
        self.source = User.objects.get(pk=self.args[0])


print(ENDPOINTS)