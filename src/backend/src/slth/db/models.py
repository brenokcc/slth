
from django.db.models import *
from django.utils.translation import gettext_lazy as _
from .. import forms


class OneToManyField(ManyToManyField):

    def formfield(self, *args, **kwargs):
        kwargs.update(form_class=forms.OneToManyField)
        return super().formfield(*args, model=self.related_model, **kwargs)


class OneToOneField(OneToOneField):

    def formfield(self, *args, **kwargs):
        kwargs.update(form_class=forms.OneToOneField)
        return super().formfield(*args, model=self.related_model, **kwargs)