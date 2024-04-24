
import json
from typing import Any
import datetime
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.forms.models import ModelChoiceIterator, ModelMultipleChoiceField
from django.db.models import Model, QuerySet, Manager
from .models import Token, Profile
from django.db import transaction
from django.db.models import Manager
from .exceptions import JsonResponseException
from .utils import absolute_url, build_url
from .serializer import Serializer
from .components import Response
from .notifications import send_push_web_notification
from slth import ENDPOINTS


DjangoModelForm = ModelForm
DjangoForm = Form
DjangoModelChoiceField = ModelChoiceField
DjangoMultipleChoiceField = MultipleChoiceField
DjangoModelMultipleChoiceField = ModelMultipleChoiceField
DjangoFileField = FileField
DjangoImageField = ImageField

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
        return self.to_dict()
        # try:
        #     return self.to_dict()
        # except JsonResponseException as e:
        #     return e.data
        
    def display(self, serializable):
        self.display_data = serializable
        return self

    def to_dict(self, prefix=None):
        data = dict(
            type='form', title=self.get_metadata('title', self._title), icon=self.get_metadata('icon'),
            style=self.get_metadata('style'), url=absolute_url(self.request), info=self._info
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
                if len(fields)==1 and isinstance(fields[0], list) and fields[0][0]['type'] == 'inline':
                    fieldsetlist.append(fields[0][0])
                else:
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
            if isinstance(self, ModelForm):
                if isinstance(field, OneToOneField):
                    instances.append(getattr(self.instance, name) if self.instance.id else None)
                elif isinstance(field, OneToManyField):
                    instances.extend(getattr(self.instance, name).all() if self.instance.id else ())
            for i, instance in enumerate(instances):
                prefix = name if is_one_to_one else f'{name}__{i}'
                kwargs = dict(instance=instance, request=self.request) if isinstance(field, InlineModelField) else dict(request=self.request)
                value.append(field.form(**kwargs).to_dict(prefix=prefix))
            if not is_one_to_one:
                value.append(field.form(request=self.request).to_dict(prefix=f'{name}__n'))
            required = getattr(field, 'required2', field.required)
            data = dict(type='inline', min=field.min, max=field.max, name=name, count=len(instances), label=field.label, required=required, value=value)
        else:
            extra = {}
            ftype = FIELD_TYPES.get(type(field).__name__, 'text')
            if name in self._values:
                ftype = 'hidden'
                value = self._values[name]
                value = value.pk if isinstance(value, Model) else value
            else:
                value = field.initial or self.initial.get(name)
                if callable(value):
                    value = value()
                
                if isinstance(field, ModelMultipleChoiceField) or isinstance(field, DjangoModelMultipleChoiceField):
                    value = [dict(id=obj.id, label=str(obj)) for obj in value] if value else []
                elif isinstance(field, MultipleChoiceField) or isinstance(field,DjangoMultipleChoiceField):
                    value = value if value else []
                elif value and (isinstance(field, ModelChoiceField) or isinstance(field, DjangoModelChoiceField)):
                    obj = field.queryset.get(pk=value)
                    value = dict(id=obj.id, label=str(obj))
                elif isinstance(value, ImageFieldFile):
                    value = build_url(self.request, value.url) if value else None
                    extra.update(extensions=field.extensions, width=field.width, height=field.height)
                elif isinstance(value, FieldFile):
                    value = build_url(self.request, value.url) if value else None
                    extra.update(extensions=field.extensions, max_size=field.max_size)
            
            if isinstance(field.widget, HiddenInput):
                ftype = 'hidden'
                value = value['id'] if isinstance(value, dict) else value

            fname = name if prefix is None else f'{prefix}__{name}'
            data = dict(type=ftype, name=fname, label=field.label, required=field.required, value=value, help_text=field.help_text, mask=None)
            data.update(**extra)
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
            if isinstance(field, CharField) and isinstance(field.widget, Textarea):
                data.update(type='textarea')
            if ftype == 'decimal':
                data.update(mask='decimal')
            elif ftype == 'choice':
                if name in self.request.GET:
                    data.update(type='hidden', value=self.request.GET[name])
                else:
                    if isinstance(field.choices, ModelChoiceIterator):
                        if choices_field_name == fname:
                            qs = field.choices.queryset
                            
                            method_attr = None
                            method_name = f'get_{fname}_queryset'
                            if hasattr(self, method_name):
                                method_attr = getattr(self, method_name)
                            elif hasattr(self, 'instance') and hasattr(self.instance, method_name):
                                method_attr = getattr(self.instance, method_name)

                            if method_attr:
                                values = dict(user=self.request.user)
                                values.update(**self._values)
                                for name2 in self.fields:
                                    value2 = self.getdata(name2, self.request.GET.get(name2))
                                    if value2:
                                        values[name2] = value2
                                qs = method_attr(qs, values)
                            
                            if 'term' in self.request.GET:
                                qs = qs.apply_search(self.request.GET['term'])
                            raise JsonResponseException([dict(id=obj.id, value=str(obj)) for obj in qs[0:10]])
                        else:
                            data['choices'] = absolute_url(self.request, f'choices={fname}')
                    else:
                        data['choices'] = [dict(id=k, value=v) for k, v in field.choices]
                    if getattr(field, 'pick', False):
                        data.update(pick=True)
                    
        attr_name = f'on_{name}_change'
        if hasattr(self, attr_name):
            data['onchange'] = absolute_url(self.request, f'on_change={name}')
        if name in self._actions:
            cls = ENDPOINTS[self._actions[name]]
            if cls.instantiate(self.request, self).check_permission():
                data.update(action=cls.get_api_metadata(self.request, absolute_url(self.request)))
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
                            if self.request.FILES and inline_form_field_name in self.request.FILES:
                                self.request.FILES._mutable = True
                                self.request.FILES[name] = self.request.FILES[inline_form_field_name]
                                self.request.FILES._mutable = False
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
                    response = self.submit()
                    for inline_field_name in inline_fields:
                        for obj in self.cleaned_data[inline_field_name]:
                            if hasattr(obj, 'deleting'):
                                obj.delete()
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

    def settitle(self, title):
        self._title = title 
        return self
    
    def setvalue(self, **kwargs):
        self._values.update(**kwargs)
    

class Form(DjangoForm, FormMixin):
    
    def __init__(self, *args, request=None, endpoint=None, **kwargs):
        self.fieldsets = {}
        self.fields = dict(self.fieldsets)
        self.display_data = []
        self.controls = dict(hide=[], show=[], set={})
        self.endpoint = endpoint
        self.request = request
        self._info = None
        self._values = {}
        self._title = type(self).__name__
        self._actions = {}
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
    
    def info(self, message):
        self._info = message
        return self
    
    def actions(self, **kwargs):
        self._actions.update(kwargs)
        return self


class ModelForm(DjangoModelForm, FormMixin):

    def __init__(self, instance=None, request=None, endpoint=None, delete=False, **kwargs):
        self.fieldsets = {}
        self.display_data = []
        self.controls = dict(hide=[], show=[], set={})
        self.request = request
        self.endpoint = endpoint
        self.endpoint = kwargs.pop('endpoint', None)
        self.delete = delete
        self._info = None
        self._values = {}
        self._title = type(self).__name__
        self._actions = {}
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
        return Response(message='Ação realizada com sucesso')

    def get_fieldsets(self):
        return self.fieldsets
    
    def info(self, message):
        self._info = message
        return self
    
    def actions(self, **kwargs):
        self._actions.update(kwargs)
        return self

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

class FileField(FileField):
    def __init__(self, *args, extensions=('pdf',), max_size=5, **kwargs):
        self.extensions = extensions
        self.max_size = max_size
        super().__init__(*args, **kwargs)

class ImageField(ImageField):
    def __init__(self, *args, extensions=('png', 'jpg', 'jpeg'), width=None, height=None, **kwargs):
        self.extensions = extensions
        if width or height:
            self.width = width or height
            self.height = height or width
        else:
            self.width = self.height = 500
        super().__init__(*args, **kwargs)

class ChoiceField(ChoiceField):
    
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        super().__init__(*args, **kwargs)
    
class MultipleChoiceField(MultipleChoiceField):
    
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        super().__init__(*args, **kwargs)

class ModelChoiceField(ModelChoiceField):
    
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        super().__init__(*args, **kwargs)

class ModelMultipleChoiceField(ModelMultipleChoiceField):
    
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        super().__init__(*args, **kwargs)

class LoginForm(Form):
    username = CharField(label=_('Username'))
    password = CharField(label=_('Password'))

    class Meta:
        title = 'Acesso ao Sistema'
        width = 350

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

class EditProfileForm(ModelForm):
    password = CharField(label=_('Senha'), required=False)
    password2 = CharField(label=_('Confirmação'), required=False)

    class Meta:
        title = 'Editar Perfil'
        model = Profile
        fields = 'photo',

    def get_fieldsets(self):
        return {
            'Dados Gerais': ('photo',),
            'Dados de Acesso': (('password', 'password2'),)
        }

    def clean_password(self):
        password = self.data.get('password')
        password2 = self.data.get('password2')
        if password and password != password2:
            raise ValidationError('As senhas devem ser iguais.')
        return password
        
    def submit(self):
        self.save()
        self.instance.user.set_password(self.cleaned_data.get('password'))
        self.instance.user.save()
        return Response(message='Ação realizada com sucesso.', redirect='/api/dashboard/', store=dict(application=None))

class SendPushNotificationForm(Form):
    message = CharField(label='Text', widget=Textarea())

    def submit(self):
        send_push_web_notification(self.endpoint.source, self.cleaned_data['message'])
        return Response(message='Notificação enviada com sucesso.')


FIELD_TYPES = {
    'CharField': 'text',
    'EmailField': 'email',
    'DecimalField': 'decimal',
    'BooleanField': 'boolean',
    'DateTimeField': 'datetime',
    'DateField': 'date',
    'IntegerField': 'number',
    'ChoiceField': 'choice',
    'TypedChoiceField' : 'choice',
    'ModelChoiceField': 'choice',
    'MultipleChoiceField': 'choice',
    'ModelMultipleChoiceField': 'choice',
    'ColorField': 'color',
    'FileField': 'file',
    'ImageField': 'file',
}