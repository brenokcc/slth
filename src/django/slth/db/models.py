from uuid import uuid1
from django.db.models import Model as DjangoModel
from django.db.models import *
from django.utils.translation import gettext_lazy as _
from .. import ModelMixin

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
    
    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.ModelChoiceField, pick=self.pick)
        field = super().formfield(*args, **kwargs)
        return field

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
        field.required2 = not self.blank
        return field


class ManyToManyField(ManyToManyField):
    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop('pick', False)
        self.addable = kwargs.pop('addable', False)
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(form_class=forms.ModelMultipleChoiceField, pick=self.pick)
        field = super().formfield(*args, **kwargs)
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

class FileField(FileField):
    def __init__(self, *args, extensions=('pdf',), max_size=5, **kwargs):
        self.extensions= extensions
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(extensions=self.extensions, max_size=self.max_size)
        kwargs.update(form_class=forms.FileField)
        return super().formfield(*args, **kwargs)
    
    def generate_filename(self, instance, filename):
        filename = '{}.{}'.format(uuid1().hex, filename.split('.')[-1].lower())
        print(filename)
        return super().generate_filename(instance, filename)
    
class ImageField(ImageField):
    def __init__(self, *args, extensions=('png', 'jpg', 'jpeg'), width=None, height=None, **kwargs):
        self.extensions= extensions
        self.width = width
        self.height = height
        super().__init__(*args, **kwargs)

    def formfield(self, *args, **kwargs):
        from .. import forms
        kwargs.update(extensions=self.extensions, width=self.width, height=self.height)
        kwargs.update(form_class=forms.ImageField)
        return super().formfield(*args, **kwargs)
    
    def generate_filename(self, instance, filename):
        filename = '{}.{}'.format(uuid1().hex, filename.split('.')[-1].lower())
        print(filename)
        return super().generate_filename(instance, filename)

class Model(DjangoModel, ModelMixin):
    class Meta:
        abstract = True
