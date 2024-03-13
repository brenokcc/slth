
from typing import Any
from django.forms import *
from .exceptions import JsonResponseException
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from .models import Token


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

class Form(DjangoForm):
    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.pop('endpoint', None)
        super().__init__(*args, **kwargs)

    def submit(self):
        pass


class ModelForm(DjangoModelForm):
    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.pop('endpoint', None)
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

def serialize(form, request, prefix=None):
    data = dict(type='form', fields=[])
    choices_field_name = request.GET.get('choices')
    if prefix:
        value = form.instance.pk if isinstance(form, ModelForm) else ''
        data['fields'].append(dict(type='hidden', name=prefix, value=value))
    for name, field in form.fields.items():
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = {}
            if isinstance(form, ModelForm) and form.instance.id and  hasattr(form.instance, name):
                instances = {i: instance for i, instance in enumerate(getattr(form.instance, name).all()[0:field.max])}
            for i in range(0, field.max):
                kwargs = dict(data=form.data, instance=instances.get(i)) if isinstance(form, ModelChoiceField) else dict(data=form.data)
                value.append(serialize(field.form(**kwargs), request, prefix=f'{name}__{i}'))
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


class LoginForm(Form):
    username = CharField(label=_('Username'))
    password = CharField(label=_('Password'))

    def __init__(self, *args, **kwargs):
        self.token = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        user = authenticate(self.endpoint.request, username=cleaned_data['username'], password=cleaned_data['password'])
        if user is None:
            raise ValidationError(_('Username or password are incorect'))
        else:
            self.token = Token.objects.create(user=user)
            return cleaned_data
        
    def submit(self):
        return dict(token=self.token.key)
