from django.db.models import *


class CharField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 255)
        super().__init__(*args, **kwargs)


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

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.OneToManyField)
        return super().formfield(*args, model=self.related_model, **kwargs)


class OneToOneField(OneToOneField):

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.OneToOneField)
        return super().formfield(*args, model=self.related_model, **kwargs)


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
