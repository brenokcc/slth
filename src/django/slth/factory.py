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
        self._empty = False

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
                fields = () if self._delete or self._empty else (self._fieldlist or '__all__')
    
        form = Form(instance=self._instance, request=request, delete=self._delete)
        form.fieldsets = self._fieldsets
        if self._serializer:
            form.display(self._serializer)
        if self._info:
            form.info(self._info)
        if self._actions:
            form.actions(**self._actions)
        if self._values:
            form.setvalue(**self._values)
        return form