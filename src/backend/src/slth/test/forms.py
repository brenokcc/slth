from .. import forms
from django.contrib.auth.models import User, Group


class PhoneForm(forms.Form):
    ddd = forms.IntegerField(label='DDD')
    numero = forms.CharField(label='Número')


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ()


class UserForm(forms.ModelForm):
    groups = forms.InlineModelField(label='Grupos', model=Group)
    class Meta:
        model = User
        fields = 'username', 'email', 'is_superuser'


class RegisterForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    telefones = forms.InlineFormField(label='Telefones', form=PhoneForm)
    grupos = forms.InlineFormField(label='Grupos', form=GroupForm)

    def save(self):
        print(self.cleaned_data, 88888)