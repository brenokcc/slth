from django.db.models import Model
from .serializer import Serializer


class FormFactory:
    def __init__(self, instance, method='POST'):
        self._instance = instance
        self._fieldsets = {}
        self._values = {}
        self._fieldlist = []
        self._display = {}
        self._title = None
        self._info = None
        self._actions = {}
        self._initial = {}
        self._choices = {}
        self._empty = False
        self._method = method
        self._hidden= []
        self._redirect = None
        self._message = None
        self._dispose = False
        self._image = None
        self._autosubmit = None

    def autosubmit(self, seconds):
        self._autosubmit = seconds
        return self

    def _append_field(self, field_name):
        if ':' in field_name:
            field_name, action_name = field_name.split(':')
            self._actions[field_name] = action_name
        self._fieldlist.append(field_name)
        return field_name
    
    def image(self, image) -> 'FormFactory':
        self._image = image
        return self

    def fields(self, *names, **values) -> 'FormFactory':
        names = names + tuple(values.keys())
        not_str = {name for name in names if not isinstance(name, str)}
        if not_str:
            self.fieldset('Dados Gerais', names)
        else:
            for field_name in names:
                self._append_field(field_name)
        for k in values:
            self._append_field(k)
            self.values(**values)
        self._empty = not self._fieldlist
        return self

    def fieldset(self, title, fields) -> 'FormFactory':
        self._fieldsets[title] = []
        for field in fields:
            if isinstance(field, str):
                self._fieldsets[title].append(self._append_field(field))
            else:
                names = []
                for field_name in field:
                    names.append(self._append_field(field_name))
                self._fieldsets[title].append(names)
        return self
    
    def display(self, title, fields) -> 'FormFactory':
        self._display[title] = fields
        return self
    
    def info(self, message) -> 'FormFactory':
        self._info = message
        return self
    
    def initial(self, **kwargs) -> 'FormFactory':
        self._initial.update(kwargs)
        return self
    
    def choices(self, **kwargs) -> 'FormFactory':
        self._choices.update(kwargs)
        return self
    
    def actions(self, **kwargs) -> 'FormFactory':
        self._actions.update(kwargs)
        return self
    
    def values(self, **kwargs) -> 'FormFactory':
        self._values.update(kwargs)
        return self
    
    def settitle(self, title) -> 'FormFactory':
        self._title = title
        return self
    
    def hidden(self, *names):
        self._hidden.extend(names)
        return self
    
    def onsuccess(self, message=None, redirect=None, dispose=False):
        if message:
            self._message = message
        if redirect:
            self._redirect = redirect
        if dispose:
            self._dispose = dispose
            self._redirect = '.'
        return self

    def build(self, endpoint):
        from .forms import ModelForm, Form
        
        if isinstance(self._instance, Model):
            fieldlist = [field.name for field in type(self._instance)._meta.get_fields() if field.name in self._fieldlist]
            class Form(ModelForm):
                class Meta:
                    model = type(self._instance)
                    fields = () if self._empty else (fieldlist if self._fieldlist else '__all__')
        
        form = endpoint.getform(Form(instance=self._instance, endpoint=endpoint, initial=self._initial))
        form._key = endpoint.get_api_name()
        form._title = self._title
        form._method = self._method
        form._info = self._info
        form._actions = self._actions
        form._message = self._message
        form._redirect = self._redirect
        form._dispose = self._dispose
        form._image = self._image
        form._autosubmit = self._autosubmit
        form._submit_label = endpoint.get_submit_label()
        form._submit_icon = endpoint.get_submit_icon()
        for name in self._fieldlist:
            if name not in form.fields:
                form.fields[name] = getattr(endpoint, name)
        for name, queryset in self._choices.items():
            form.fields[name].queryset = queryset
        form.fieldsets = self._fieldsets
        form.values(**self._values)
        if self._display:
            serializer = Serializer(self._instance, request=endpoint.request)
            for title, fields in self._display.items():
                serializer.fieldset(title, fields)
            form._display = serializer
        if self._hidden:
            form.controller.hide(*self._hidden)
        return form