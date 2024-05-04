from django.db.models import Model
from .serializer import Serializer
class FormFactory:
    def __init__(self, instance, endpoint=None, method='POST'):
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

    def fields(self, *names, **values) -> 'FormFactory':
        not_str = {name for name in names if not isinstance(name, str)}
        if not_str:
            self.fieldset('Dados Gerais', names)
        else:
            self._fieldlist.extend(names)
        for k in values:
            self._fieldlist.append(k)
            self.setvalue(**values)
        self._empty = not self._fieldlist
        return self

    def fieldset(self, title, fields) -> 'FormFactory':
        self._fieldsets[title] = fields
        for field in fields:
            if isinstance(field, str):
                self._fieldlist.append(field)
            else:
                self._fieldlist.extend(field)
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
    
    def setvalue(self, **kwargs) -> 'FormFactory':
        self._values.update(kwargs)
        return self
    
    def settitle(self, title) -> 'FormFactory':
        self._title = title
        return self

    def form(self, endpoint):
        from .forms import ModelForm, Form
        
        if isinstance(self._instance, Model):
            fieldlist = [field.name for field in type(self._instance)._meta.get_fields() if field.name in self._fieldlist]
            class Form(ModelForm):
                class Meta:
                    model = type(self._instance)
                    fields = () if self._empty else (fieldlist if self._fieldlist else '__all__')
                
        form = Form(instance=self._instance, endpoint=endpoint, initial=self._initial)
        form._title = self._title
        form._method = self._method
        form._info = self._info
        form._actions = self._actions
        for name in self._fieldlist:
            if name not in form.fields:
                form.fields[name] = getattr(endpoint, name)
        for name, queryset in self._choices.items():
            form.fields[name].queryset = queryset
        form.fieldsets = self._fieldsets
        form.setvalue(**self._values)
        if self._display:
            serializer = Serializer(self._instance, request=endpoint.request)
            for title, fields in self._display.items():
                serializer.fieldset(title, fields)
            form._display = serializer
        return form