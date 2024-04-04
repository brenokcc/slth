from django.db.models import *


class CharField(CharField):
    def __init__(self, *args, **kwargs):
        self.mask = kwargs.pop('mask', None)
        kwargs.setdefault('max_length', 255)
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        field = super().formfield(*args, **kwargs)
        field.mask = self.mask
        return field
    
class IntegerField(IntegerField):
    def __init__(self, *args, **kwargs):
        self.mask = kwargs.pop('mask', None)
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        field = super().formfield(*args, **kwargs)
        field.mask = self.mask
        return field

class ForeignKey(ForeignKey):
    def __init__(self, to, on_delete=None, **kwargs):
        self.pick = kwargs.pop('pick', False)
        self.addable = kwargs.pop('addable', False)
        super().__init__(to, on_delete or CASCADE, **kwargs)


class ManyToManyField(ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        self.addable = kwargs.pop('addable', False)
        super().__init__(*args, **kwargs)

class OneToManyField(ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields', '__all__')
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.OneToManyField, fields=self.fields)
        field = super().formfield(*args, model=self.related_model, **kwargs)
        field.label = self.verbose_name
        return field


class OneToOneField(OneToOneField):
    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields', '__all__')
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.OneToOneField, fields=self.fields)
        field = super().formfield(*args, model=self.related_model, **kwargs)
        field.label = self.verbose_name

        return field


class DecimalField(DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['decimal_places'] = kwargs.pop('decimal_places', 2)
        kwargs['max_digits'] = kwargs.pop('max_digits', 9)
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.DecimalField)
        return super().formfield(*args, **kwargs)
    
class ColorField(CharField):

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.ColorField)
        return super().formfield(*args, **kwargs)


class TextField(TextField):
    def __init__(self, *args, **kwargs):
        self.formatted= kwargs.pop('formatted', False)
        super().__init__(*args, **kwargs)
