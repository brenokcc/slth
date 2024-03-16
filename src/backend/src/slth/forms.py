
import json
from typing import Any
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.forms.models import ModelChoiceIterator
from django.db.models import Model
from .models import Token
from django.db import transaction


DjangoModelForm = ModelForm
DjangoForm = Form

FIELD_TYPES = {
    CharField: 'text',
    EmailField: 'email',
    BooleanField: 'boolean',
    IntegerField: 'number',
    ChoiceField: 'choice',
    ModelChoiceField: 'choice',
    MultipleChoiceField: 'choice',
    ModelMultipleChoiceField: 'choice',
}

class FormMixin:

    def fieldset(self, title, fields):
        self.fieldsets[title] = fields
        return self

    def parse_json(self):
        content_type = self.request.META.get('CONTENT_TYPE')
        method = self.request.method.lower()
        if content_type and content_type.lower() == 'application/json':
            if method == 'get' or method == 'post':
                d1 = json.loads(self.request.body.decode()) if self.request.body else {}
                d2 = self.request.GET if method == 'get' else self.request.POST
                d2._mutable = True
                d2.clear()
                for k, v in d1.items():
                    if isinstance(v, list):
                        for i, item in enumerate(v):
                            prefix = f'{k}__{i}'
                            d2[prefix] = item.get('id')
                            for k1, v1 in item.items():
                                d2[f'{prefix}__{k1}'] = v1
                    else:
                        d2[k] = v
                d2._mutable = False

    def serialize(self, prefix=None):
        data = dict(type='form')
        choices_field_name = self.request.GET.get('choices')
        if self.fieldsets:
            fieldsets = []
            for title, names in self.fieldsets.items():
                fields = []
                for name in names:
                    if isinstance(name, str):
                        fields.append(self.serialize_field(name, self.fields[name], prefix, choices_field_name))
                    else:
                        width = int(100/len(name))
                        for name in name:
                            fields.append(
                                self.serialize_field(name, self.fields[name], prefix, choices_field_name, width=width)
                            )
                fieldsets.append(dict(type='fieldset', title=title, fields=fields))
            data.update(fieldsets=fieldsets)
        else:
            fields = []
            for name, field in self.fields.items():
                fields.append(self.serialize_field(name, field, prefix, choices_field_name))
                if prefix:
                    value = self.instance.pk if isinstance(self, ModelForm) else ''
                    fields.append(dict(type='hidden', name=prefix, value=value))
            data.update(fields=fields)
        return data
    
    def serialize_field(self, name, field, prefix, choices_field_name, width=100):
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = {}
            if isinstance(self, ModelForm) and self.instance.id and  hasattr(self.instance, name):
                instances = {i: instance for i, instance in enumerate(getattr(self.instance, name).all()[0:field.max])}
            for i in range(0, field.max):
                kwargs = dict(instance=instances.get(i), request=self.request) if isinstance(self, ModelChoiceField) else dict(request=self.request)
                value.append(field.form(**kwargs).serialize(prefix=f'{name}__{i}'))
            data = dict(type='inline', min=field.min, max=field.max, name=name, label=field.label, required=field.required, value=value, width=width)
        else:
            ftype = FIELD_TYPES.get(type(field), 'text')
            value = field.initial or self.initial.get(name)
            if callable(value):
                value = value()
            if isinstance(value, list):
                value = [obj.pk if isinstance(obj, Model) else obj for obj in value]
            fname = name if prefix is None else f'{prefix}__{name}'
            data = dict(type=ftype, name=fname, label=field.label, required=field.required, value=value, width=width)
            if ftype == 'choice':
                if isinstance(field.choices, ModelChoiceIterator):
                    if choices_field_name == fname:
                        return [dict(id=obj.id, value=str(obj)) for obj in field.choices]
                    else:
                        data['choices'] = build_url(self.request, choices=fname)
                else:
                    data['choices'] = [dict(id=k, value=v) for k, v in field.choices]
        return data
    
    def post(self):
        data = {}
        errors = {}
        inline_fields = {name: field for name, field in self.fields.items() if isinstance(field, InlineFormField) or isinstance(field, InlineModelField)}
        self.is_valid()
        errors.update(self.errors)
        for inline_field_name, inline_field in inline_fields.items():
            data[inline_field_name] = []
            for i in range(0, inline_field.max):
                prefix = f'{inline_field_name}__{i}'
                if prefix in self.data:
                    inline_form_data = {}
                    pk = self.data.get(prefix)
                    for name in inline_field.form.base_fields:
                        inline_form_field_name = f'{inline_field_name}__{i}__{name}'
                        inline_form_data[name] = self.data.get(inline_form_field_name)
                    instance = inline_field.form._meta.model.objects.get(pk=pk) if pk else None
                    inline_form = inline_field.form(data=inline_form_data, instance=instance, request=self.request)
                    if inline_form.is_valid():
                        if isinstance(inline_form, DjangoModelForm):
                            data[inline_field_name].append(inline_form.instance)
                        else:
                            data[inline_field_name].append(inline_form.cleaned_data)
                    else:
                        errors.update({f'{inline_field_name}__{i}__{name}': error for name, error in inline_form.errors.items()})
        data.update({field_name: self.cleaned_data.get(field_name) for field_name in self.fields if field_name not in inline_fields}) 
        if errors:
            return dict(message='Please correct the errors.', errors=errors)
        else:
            with transaction.atomic():
                self.cleaned_data = data
                if isinstance(self, DjangoModelForm):
                    self.save()
                    for inline_field_name in inline_fields:
                        relation = getattr(self.instance, inline_field_name)
                        for obj in self.cleaned_data[inline_field_name]:
                            obj.save()
                            relation.add(obj)
                    dict(message='Action successfully performed.')
                else:
                    return self.submit()

class Form(DjangoForm, FormMixin):
    def __init__(self, *args, **kwargs):
        self.fieldsets = {}
        self.request = kwargs.pop('request', None)
        self.parse_json()
        if 'data' not in kwargs:
            if self.request.method.upper() == 'GET':
                data = self.request.GET or None
            elif self.request.method.upper() == 'POST':
                data = self.request.POST or None
        else:
            data = kwargs['data']
        kwargs.update(data=data)
        super().__init__(*args, **kwargs)

    def submit(self):
        pass


class ModelForm(DjangoModelForm, FormMixin):
    def __init__(self, *args, **kwargs):
        self.fieldsets = {}
        self.request = kwargs.pop('request', None)
        self.parse_json()
        if 'data' not in kwargs:
            if self.request.method.upper() == 'GET':
                data = self.request.GET or None
            elif self.request.method.upper() == 'POST':
                data = self.request.POST or None
        else:
            data = kwargs['data']
        kwargs.update(data=data)
        super().__init__(*args, **kwargs)

    def submit(self):
        pass

class InlineFormField(Field):
    def __init__(self, *args, form=None, min=1, max=3, **kwargs):
        self.form = form
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


class InlineModelField(Field):
    def __init__(self, model, *args, fields='__all__', exclude=(), min=1, max=3, **kwargs):
        self.form = modelform_factory(model, form=ModelForm, fields=fields, exclude=exclude)
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


class OneToManyField(InlineModelField):
    def __init__(self, model, fields='__all__', exclude=(), min=1, max=3, **kwargs):
        super().__init__(model, fields=fields, exclude=exclude, min=min, max=max)

class OneToOneField(InlineModelField):
    def __init__(self, model, fields='__all__', exclude=(), **kwargs):
        super().__init__(model, fields=fields, exclude=exclude, min=1, max=1)



def build_url(request, **params):
    url = "{}://{}{}".format(request.META.get('X-Forwarded-Proto', request.scheme), request.get_host(), request.path)
    for k, v in params.items():
        url = f'{url}&{k}={v}' if '?' in url else f'{url}?{k}={v}'
    return url

class LoginForm(Form):
    username = CharField(label=_('Username'))
    password = CharField(label=_('Password'))

    def __init__(self, *args, **kwargs):
        self.token = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        user = authenticate(self.request, username=cleaned_data['username'], password=cleaned_data['password'])
        if user is None:
            raise ValidationError(_('Username or password are incorect'))
        else:
            self.token = Token.objects.create(user=user)
            return cleaned_data
        
    def submit(self):
        return dict(token=self.token.key)
