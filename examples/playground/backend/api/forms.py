from slth import forms
from .models import Cidade, Pessoa, Questionario, Pergunta, PerguntaQuestionario
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
    

class ResponderQuestionarioForm(forms.ModelForm):

    class Meta:
        model = Questionario
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for pergunta_questionario in self.instance.perguntaquestionario_set.all():
            label = pergunta_questionario.pergunta.enunciado
            tipo = pergunta_questionario.pergunta.tipo_resposta
            if tipo == Pergunta.TEXTO_CURTO:
                field = forms.CharField()
            elif tipo == Pergunta.TEXTO_LONGO:
                field = forms.CharField( widget=forms.Textarea())
            elif tipo == Pergunta.DATA:
                field = forms.DateField()
            elif tipo == Pergunta.DECIMAL:
                field = forms.DecimalField()
            elif tipo == Pergunta.INTEIRO:
                field = forms.IntegerField()
            elif tipo == Pergunta.ESCOLHA:
                field = forms.ChoiceField(
                    pick=True,
                    choices=[[x.descricao, x.descricao] for x in pergunta_questionario.pergunta.opcoes.all()]
                )
            elif tipo == Pergunta.MULTIPLA_ESCOLHA:
                field = forms.MultipleChoiceField(
                    pick=True,
                    choices=[[x.descricao, x.descricao] for x in pergunta_questionario.pergunta.opcoes.all()]
                )
            field.label = label
            if pergunta_questionario.resposta:
                if ' | ' in pergunta_questionario.resposta:
                    field.initial = pergunta_questionario.resposta.split(' | ')
                else:
                    field.initial = pergunta_questionario.resposta
            self.fields[f'{pergunta_questionario.id}'] = field

    def submit(self):
        for pk in self.fields:
            resposta = self.cleaned_data.get(pk)
            if isinstance(resposta, list):
                resposta = ' | '.join(resposta)
            PerguntaQuestionario.objects.filter(pk=pk).update(resposta=resposta)
        return super().submit()
            
    