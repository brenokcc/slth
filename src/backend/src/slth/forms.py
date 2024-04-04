
import json
from typing import Any
import datetime
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.db.models.fields.files import ImageFieldFile
from django.forms.models import ModelChoiceIterator, ModelMultipleChoiceField
from django.db.models import Model, QuerySet, Manager
from .models import Token
from django.db import transaction
from django.db.models import Manager
from .exceptions import JsonResponseException
from .utils import absolute_url
from .serializer import Serializer
from .components import Response


DjangoModelForm = ModelForm
DjangoForm = Form

MASKS = dict(
    cpf_cnpj='999.999.999-99|99.999.999/9999-99',
    cpf='999.999.999-99',
    cnpj='99.999.999/9999-99',
    telefone='(99) 99999-9999',
)
    

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
        return getattr(metaclass, name, default) if metaclass else default
    
    def on_change(self, field_name):
        self.controls['show'].clear()
        self.controls['hide'].clear()
        self.controls['set'].clear()
        values = {}
        for name2 in self.fields:
            value2 = self.getdata(name2, self.request.POST.get(name2))
            if value2:
                values[name2] = value2
        getattr(self, f'on_{field_name}_change')(values)
        return self.controls

    def serialize(self):
        try:
            return self.to_dict()
        except JsonResponseException as e:
            return e.data
        
    def display(self, serializable):
        self.display_data = serializable
        return self

    def to_dict(self, prefix=None):
        data = dict(
            type='form', title=self.get_metadata('title', type(self).__name__), icon=self.get_metadata('icon'),
            style=self.get_metadata('style'), url=absolute_url(self.request)
        )
        data.update(controls=self.controls, width=self.get_metadata('width', '100%'))
        if self.display_data:
            if isinstance(self.display_data, Serializer):
                # self.display_data.request = self.request
                data.update(display=self.display_data.serialize(forward_exception=True)['data'])
        choices_field_name = self.request.GET.get('choices')
        fieldsets = self.get_fieldsets()
        if fieldsets:
            fieldsetlist = []
            for title, names in fieldsets.items():
                fields = []
                if prefix:
                    value = self.instance.pk if isinstance(self, ModelForm) else ''
                    fields.append([dict(type='hidden', name=f'{prefix}__id', value=value, label='ID')])
                for name in names:
                    if isinstance(name, str):
                        field = self.serialize_field(name, self.fields[name], prefix, choices_field_name)
                        fields.append([field])
                    else:
                        fields.append(
                            [self.serialize_field(name, self.fields[name], prefix, choices_field_name) for name in name]
                        )
                fieldsetlist.append(dict(type='fieldset', title=title, fields=fields))
            data.update(fieldsets=fieldsetlist)
        else:
            fields = []
            if prefix:
                value = self.instance.pk if isinstance(self, ModelForm) else ''
                fields.append(dict(type='hidden', name=f'{prefix}__id', value=value, label='ID'))
            for name, field in self.fields.items():
                fields.append(self.serialize_field(name, field, prefix, choices_field_name))
            data.update(fields=fields)
        return data
    
    def serialize_field(self, name, field, prefix, choices_field_name):
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = []
            is_one_to_one = field.max == field.min == 1
            if isinstance(self, ModelForm) and self.instance.id and hasattr(self.instance, name):
                if isinstance(field, OneToOneField):
                    instances.append(getattr(self.instance, name))
                if isinstance(field, OneToManyField):
                    instances.extend(getattr(self.instance, name).all())
            for i, instance in enumerate(instances):
                prefix = name if is_one_to_one else f'{name}__{i}'
                kwargs = dict(instance=instance, request=self.request) if isinstance(field, InlineModelField) else dict(request=self.request)
                value.append(field.form(**kwargs).to_dict(prefix=prefix))
            if not is_one_to_one:
                value.append(field.form(request=self.request).to_dict(prefix=f'{name}__n'))
            required = getattr(field, 'required2', field.required)
            data = dict(type='inline', min=field.min, max=field.max, name=name, count=len(instances), label=field.label, required=required, value=value)
        else:
            ftype = FIELD_TYPES.get(type(field), 'text')
            value = field.initial or self.initial.get(name)
            if callable(value):
                value = value()
            if value and isinstance(field, ModelMultipleChoiceField):
                value = [dict(id=obj.id, label=str(obj)) for obj in value]
            elif value and isinstance(field, ModelChoiceField):
                obj = field.queryset.get(pk=value)
                value = dict(id=obj.id, label=str(obj))
            elif isinstance(value, ImageFieldFile):
                value = str(value)
            
            fname = name if prefix is None else f'{prefix}__{name}'
            data = dict(type=ftype, name=fname, label=field.label, required=field.required, value=value, help_text=field.help_text, mask=None)
            for word in MASKS:
                if word in name:
                    data.update(mask=MASKS[word])
            for word in ('password', 'senha'):
                if word in name:
                    data.update(type='password')
            if isinstance(field, CharField) or isinstance(field, IntegerField):
                mask = getattr(field, 'mask', None)
                if mask:
                    data.update(mask=mask)
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
                        if 'term' in self.request.GET:
                            qs = qs.apply_search(self.request.GET['term'])
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

        field_name = self.request.GET.get('on_change')
        if field_name:
            return self.on_change(field_name)

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
                    if pk:
                        pk = int(pk)
                        for name in inline_field.form.base_fields:
                            inline_form_field_name = f'{prefix}__{name}'
                            inline_form_data[name] = self.data.get(inline_form_field_name)
                        instance = inline_field.form._meta.model.objects.get(pk=abs(pk)) if pk else None
                        if pk < 0:
                            setattr(instance, 'deleting', True)
                        inline_form = inline_field.form(data=inline_form_data, instance=instance, request=self.request)
                        if inline_form.is_valid():
                            if isinstance(inline_form, DjangoModelForm):
                                data[inline_field_name].append(inline_form.instance)
                            else:
                                data[inline_field_name].append(inline_form.cleaned_data)
                        else:
                            errors.update({f'{prefix}__{name}': error for name, error in inline_form.errors.items()}) 
        if errors:
            return dict(type='error', text='Please correct the errors.', errors=errors)
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
                                if hasattr(obj, 'deleting'):
                                    setattr(self.instance, inline_field_name, None)
                                else:
                                    setattr(self.instance, inline_field_name, obj)
                    self.submit()
                    for inline_field_name in inline_fields:
                        for obj in self.cleaned_data[inline_field_name]:
                            if hasattr(obj, 'deleting'):
                                obj.delete()
                    response = Response(message='Action successfully performed.')
                else:
                    response = self.submit()
            return response
                
    def hide(self, *names):
        self.controls['hide'].extend(names)

    def show(self, *names):
        self.controls['show'].extend(names)

    def setdata(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, Model):
                v = dict(id=v.id, value=str(v))
            elif isinstance(v, QuerySet) or isinstance(v, Manager):
                v = [dict(id=v.id, value=str(v)) for v in v]
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
        self.fields = dict(self.fieldsets)
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
        if self.request:
            kwargs.update(files=self.request.FILES or None)
        super().__init__(*args, **kwargs)

    def submit(self):
        pass

    def get_fieldsets(self):
        return self.fieldsets


class ModelForm(DjangoModelForm, FormMixin):

    def __init__(self, instance=None, request=None, delete=False, **kwargs):
        self.fieldsets = {}
        self.display_data = []
        self.controls = dict(hide=[], show=[], set={})
        self.request = request
        self.delete = delete
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
        if self.request:
            kwargs.update(files=self.request.FILES or None)
        super().__init__(instance=instance, **kwargs)

    def submit(self):
        self.instance.delete() if self.delete else self.save()

    def get_fieldsets(self):
        return self.fieldsets


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

class InlineFormField(Field):
    def __init__(self, *args, form=None, min=1, max=3, **kwargs):
        self.form = form
        self.max = max
        self.min = min
        super().__init__(*args,  **kwargs)
        self.required = False


class InlineModelField(Field):
    def __init__(self, model, *args, fields='__all__', exclude=(), min=1, max=3, **kwargs):
        if fields == '__all__':
            self.form = modelform_factory(model, form=ModelForm, fields=fields, exclude=exclude)
        else:
            field_names = []
            for field_name in fields:
                if isinstance(field_name, str):
                    field_names.append(field_names)
                else:
                    field_names.extend(field_name)
            self.form = modelform_factory(model, form=ModelForm, fields=field_names, exclude=exclude)
            self.form.get_fieldsets = lambda _self: {None: fields}
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

class DecimalField(DecimalField):
    def to_python(self, value):
        if isinstance(value, str) and ',' in value:
            value = value.replace('.', '').replace(',', '.')
        return super().to_python(value)
    
class ColorField(CharField):
    pass


class LoginForm(Form):
    username = CharField(label=_('Username'))
    password = CharField(label=_('Password'))

    class Meta:
        title = 'Acesso ao Sistema'
        width = 300

    def __init__(self, *args, **kwargs):
        self.token = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        user = authenticate(self.request, username=cleaned_data.get('username'), password=cleaned_data.get('password'))
        if user is None:
            raise ValidationError(_('Username or password are incorect'))
        else:
            self.token = Token.objects.create(user=user)
            return cleaned_data
        
    def submit(self):
        return Response(message='Bem-vindo!', redirect='/api/dashboard/', store=dict(token=self.token.key, application=None))


FIELD_TYPES = {
    CharField: 'text',
    EmailField: 'email',
    DecimalField: 'decimal',
    BooleanField: 'boolean',
    DateTimeField: 'datetime',
    DateField: 'date',
    IntegerField: 'number',
    ChoiceField: 'choice',
    TypedChoiceField : 'choice',
    ModelChoiceField: 'choice',
    MultipleChoiceField: 'choice',
    ModelMultipleChoiceField: 'choice',
    ColorField: 'color',
    FileField: 'file',
    ImageField: 'file',
}