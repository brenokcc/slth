from slth import forms
from .models import Cidade, Pessoa
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
        fields = 'username', 'first_name', 'last_name', 'email', 'is_superuser'



class RegisterForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    telefones = forms.InlineFormField(label='Telefones', form=PhoneForm)
    grupos = forms.InlineFormField(label='Grupos', form=GroupForm)

    def save(self):
        print(self.cleaned_data)

class CadastrarCidadeForm(forms.ModelForm):
    class Meta:
        title = 'Cadastrar Cidade'
        model = Cidade
        fields = 'nome', 'prefeito', 'vereadores'

    def get_prefeito_queryset(self, queryset, values):
        print(queryset, values)
        return queryset

    def _on_prefeito_change(self, values):
        print(values)
        self.hide('vereadores')
        self.setdata(nome='XXXXX')

    def on_nome_change(self, values):
        self.setdata(prefeito=Pessoa.objects.last(), vereadores=Pessoa.objects.all()[0:3])

    def clean(self):
        raise forms.ValidationError('xxxxx')