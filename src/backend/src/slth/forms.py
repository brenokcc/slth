
import json
from typing import Any
import datetime
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.db.models import Model, QuerySet, Manager
from .models import Token
from django.db import transaction
from django.db.models import Manager
from .exceptions import JsonResponseException
from .utils import absolute_url
from .serializer import serialize, Serializer


DjangoModelForm = ModelForm
DjangoForm = Form

FIELD_TYPES = {
    CharField: 'text',
    EmailField: 'email',
    DecimalField: 'decimal',
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
        # 'application/x-www-form-urlencoded'
        if content_type and content_type.lower() in 'application/json':
            if method == 'get' or method == 'post':
                d1 = json.loads(self.request.body.decode()) if self.request.body else {}
                d2 = self.request.GET if method == 'get' else self.request.POST
                d2._mutable = True
                d2.clear()
                for k, v in d1.items():
                    if isinstance(v, list):
                        for i, item in enumerate(v):
                            prefix = f'{k}__{i}'
                            d2[f'{prefix}__id'] = item.get('id')
                            for k1, v1 in item.items():
                                d2[f'{prefix}__{k1}'] = v1
                    elif isinstance(v, dict):
                        prefix = k
                        d2[f'{prefix}__id'] = v.get('id')
                        for k1, v1 in v.items():
                            d2[f'{prefix}__{k1}'] = v1
                    else:
                        d2[k] = v
                d2._mutable = False

    @classmethod
    def get_metadata(cls, name, default=None):
        metaclass = getattr(cls, 'Meta', None)
        if metaclass:
            return getattr(metaclass, name, default)
        return default
    
    def on_change(self, field_name):
        self.controls['show'].clear()
        self.controls['hide'].clear()
        self.controls['set'].clear()
        values = {}
        for name2 in self.fields:
            value2 = self.getdata(name2, self.request.GET.get(name2))
            if value2:
                values[name2] = value2
        getattr(self, f'on_{field_name}_change')(values)
        return self.controls

    def serialize(self):
        try:
            field_name = self.request.GET.get('on_change')
            return self.on_change(field_name) if field_name else self.to_dict()
        except JsonResponseException as e:
            return e.data
        
    def display(self, serializable):
        self.display_data.append(serializable)
        return self

    def to_dict(self, prefix=None):
        data = dict(
            type='form', title=self.get_metadata('title'), icon=self.get_metadata('icon'),
            style=self.get_metadata('style'), url=absolute_url(self.request)
        )
        data.update(controls=self.controls)
        display = []
        if self.display_data:
            for serializable in self.display_data:
                if isinstance(serializable, Serializer):
                    serializable.request = self.request
                    serialized = serializable.serialize(forward_exception=True)['data']
                elif hasattr(serializable, 'serialize'):
                    serialized = serializable.serialize()
                else:
                    serialized = serialize(serializable)
                display.append(serialized)
            data.update(display=display)
        choices_field_name = self.request.GET.get('choices')
        if self.fieldsets:
            fieldsets = []
            for title, names in self.fieldsets.items():
                fields = []
                for name in names:
                    if isinstance(name, str):
                        field = self.serialize_field(name, self.fields[name], prefix, choices_field_name)
                        fields.append([field])
                    else:
                        fields.append(
                            [self.serialize_field(name, self.fields[name], prefix, choices_field_name) for name in name]
                        )
                fieldsets.append(dict(type='fieldset', title=title, fields=fields))
            data.update(fieldsets=fieldsets)
        else:
            fields = []
            if prefix:
                value = self.instance.pk if isinstance(self, ModelForm) else ''
                fields.append(dict(type='hidden', name=prefix, value=value))
            for name, field in self.fields.items():
                fields.append(self.serialize_field(name, field, prefix, choices_field_name))
            data.update(fields=fields)
        return data
    
    def serialize_field(self, name, field, prefix, choices_field_name):
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = {}
            if isinstance(field, OneToManyField) and isinstance(self, ModelForm) and self.instance.id and hasattr(self.instance, name):
                instances = {i: instance for i, instance in enumerate(getattr(self.instance, name).all()[0:field.max])}
            for i in range(0, field.max):
                kwargs = dict(instance=instances.get(i), request=self.request) if isinstance(self, ModelChoiceField) else dict(request=self.request)
                value.append(field.form(**kwargs).to_dict(prefix=f'{name}__{i}'))
            data = dict(type='inline', min=field.min, max=field.max, name=name, label=field.label, required=field.required, value=value)
        else:
            ftype = FIELD_TYPES.get(type(field), 'text')
            value = field.initial or self.initial.get(name)
            if callable(value):
                value = value()
            if isinstance(value, list):
                value = [obj.pk if isinstance(obj, Model) else obj for obj in value]
            if value and isinstance(field, ModelChoiceField):
                obj = field.queryset.get(pk=value)
                value = dict(id=obj.id, label=str(obj))
            fname = name if prefix is None else f'{prefix}__{name}'
            data = dict(type=ftype, name=fname, label=field.label, required=field.required, value=value, mask=None)
            if ftype == 'decimal':
                data.update(mask='decimal')
            elif ftype == 'choice':
                if isinstance(field.choices, ModelChoiceIterator):
                    if choices_field_name == fname:
                        method_name = f'get_{fname}_queryset'
                        qs = field.choices.queryset
                        if hasattr(self, method_name):
                            values = {}
                            for name2 in self.fields:
                                value2 = self.getdata(name2, self.request.GET.get(name2))
                                if value2:
                                    values[name2] = value2
                            qs = getattr(self, method_name)(qs, values)
                        if 'q' in self.request.GET:
                            qs = qs.apply_search(self.request.GET['q'])
                        raise JsonResponseException([dict(id=obj.id, value=str(obj)) for obj in qs[0:10]])
                    else:
                        data['choices'] = absolute_url(self.request, f'choices={fname}')
                else:
                    data['choices'] = [dict(id=k, value=v) for k, v in field.choices]
        attr_name = f'on_{name}_change'
        if hasattr(self, attr_name):
            data['onchange'] = absolute_url(self.request, f'on_change={name}')
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
                is_one_to_one = inline_field.max == inline_field.min == 1
                prefix = inline_field_name if is_one_to_one else f'{inline_field_name}__{i}'
                inline_form_field_name = f'{prefix}__id'
                if inline_form_field_name in self.data:
                    inline_form_data = {}
                    pk = self.data.get(inline_form_field_name)
                    for name in inline_field.form.base_fields:
                        inline_form_field_name = f'{prefix}__{name}'
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
        if errors:
            return dict(message='Please correct the errors.', errors=errors)
        else:
            data.update({field_name: self.cleaned_data.get(field_name) for field_name in self.fields if field_name not in inline_fields})
            with transaction.atomic():
                self.cleaned_data = data
                if isinstance(self, DjangoModelForm):
                    for inline_field_name in inline_fields:
                        for obj in self.cleaned_data[inline_field_name]:
                            obj.save()
                            # set one-to-one
                            if hasattr(self.instance, f'{inline_field_name}_id'):
                                setattr(self.instance, inline_field_name, obj)
                    self.save()
                    for inline_field_name in inline_fields:
                        relation = getattr(self.instance, inline_field_name)
                        for obj in self.cleaned_data[inline_field_name]:
                            # set one-to-many
                            if isinstance(relation, Manager):
                                relation.add(obj)
                    return dict(message='Action successfully performed.')
                else:
                    return self.submit()
                
    def hide(self, *names):
        self.controls['hide'].extend(names)

    def show(self, *names):
        self.controls['show'].extend(names)

    def setdata(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, Model):
                v = dict(id=v.id, text=str(v))
            elif isinstance(v, QuerySet) or isinstance(v, Manager):
                v = [dict(id=v.id, text=str(v)) for v in v]
            elif isinstance(v, bool):
                v = str(v).lower()
            elif isinstance(v, datetime.datetime):
                v = v.strftime('%Y-%m-%d %H:%M')
            elif isinstance(v, datetime.date):
                v = v.strftime('%Y-%m-%d')
            self.controls['set'][k] = v

    def getdata(self, name, value, default=None):
        if value is None:
            return default
        else:
            try:
                value = self.fields[name].to_python(value)
            except KeyError:
                pass
            except ValidationError:
                pass
            return default if value is None else value

class Form(DjangoForm, FormMixin):
    def __init__(self, *args, **kwargs):
        self.fieldsets = {}
        self.display_data = []
        self.controls = dict(hide=[], show=[], set={})
        self.request = kwargs.pop('request', None)
        self.parse_json()
        if 'data' not in kwargs:
            if self.request.method.upper() == 'GET':
                data = self.request.GET or None
            elif self.request.method.upper() == 'POST':
                data = self.request.POST or {}
        else:
            data = kwargs['data']
        kwargs.update(data=data)
        super().__init__(*args, **kwargs)

    def submit(self):
        pass


class ModelForm(DjangoModelForm, FormMixin):
    def __init__(self, instance=None, request=None, **kwargs):
        self.fieldsets = {}
        self.display_data = []
        self.controls = dict(hide=[], show=[], set={})
        self.request = request
        self.parse_json()
        if 'data' not in kwargs:
            if self.request.method.upper() == 'GET':
                data = self.request.GET or None
            elif self.request.method.upper() == 'POST':
                data = self.request.POST or {}
            else:
                data = None
        else:
            data = kwargs['data']
        kwargs.update(data=data)
        super().__init__(instance=instance, **kwargs)

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
