class FormFactory:
    def __init__(self, instance, delete=False):
        self._instance = instance
        self._fieldsets = {}
        self._fieldlist = []
        self._serializer = None
        self._info = None
        self._actions = {}
        self._delete = delete

    def fields(self, *names):
        self._fieldlist.extend(names)
        return self

    def fieldset(self, title, fields):
        self._fieldsets[title] = fields
        for field in fields:
            if isinstance(field, str):
                self._fieldlist.append(field)
            else:
                self._fieldlist.extend(field)
        return self
    
    def display(self, serializer):
        self._serializer = serializer
        return self
    
    def info(self, message):
        self._info = message
        return self
    
    def actions(self, **kwargs):
        self._actions.update(kwargs)
        return self

    def form(self, request):
        from .forms import ModelForm
        class Form(ModelForm):
            class Meta:
                title = '{} {}'.format(
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
        return form