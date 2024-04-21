class FormFactory:
    def __init__(self, instance, delete=False):
        self._instance = instance
        self._fieldsets = {}
        self._values = {}
        self._fieldlist = []
        self._serializer = None
        self._title = None
        self._info = None
        self._actions = {}
        self._delete = delete

    def fields(self, *names) -> 'FormFactory':
        self._fieldlist.extend(names)
        return self

    def fieldset(self, title, fields) -> 'FormFactory':
        self._fieldsets[title] = fields
        for field in fields:
            if isinstance(field, str):
                self._fieldlist.append(field)
            else:
                self._fieldlist.extend(field)
        return self
    
    def display(self, serializer) -> 'FormFactory':
        self._serializer = serializer
        return self
    
    def info(self, message) -> 'FormFactory':
        self._info = message
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

    def form(self, request):
        from .forms import ModelForm, HiddenInput
        class Form(ModelForm):
            class Meta:
                title = self._title or '{} {}'.format(
                    'Excluir' if self._delete else ('Editar' if self._instance.pk else 'Cadastrar'),
                    type(self._instance)._meta.verbose_name
                )
                model = type(self._instance)
                fields = () if self._delete else (self._fieldlist or '__all__')
    
        form = Form(instance=self._instance, request=request, delete=self._delete)
        form.fieldsets = self._fieldsets
        if self._serializer:
            form.display(self._serializer)
        if self._info:
            form.info(self._info)
        if self._actions:
            form.actions(**self._actions)
        for name, value in self._values.items():
            field = form.fields[name]
            field.initial = value.id if hasattr(value, 'id') else value
            field.widget = HiddenInput()
        return form