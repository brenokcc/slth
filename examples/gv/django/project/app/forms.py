import datetime
from slth import forms
from .models import Consulta, PerguntaFrequente, Arquivo


class ConsultarIAForm(forms.ModelForm):
    arquivos = forms.ModelMultipleChoiceField(Arquivo.objects, label='Arquivos', pick=True, required=False)
    class Meta:
        model = Consulta
        fields = 'pergunta_ia',
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pergunta_ia'].initial = self.instance.pergunta
        self.fields['arquivos'].queryset = self.instance.consultante.cliente.arquivocliente_set.all()
        self.info('''Abaixo serão listados os arquivos específicos do cliente. Para realizar a consulta com base neles
                  ao invés dos arquivos da base de conhecimento, selecione uma ou mais opção.''')

    def submit(self):
        self.instance.data_consulta = datetime.datetime.now()
        self.instance.resposta_ia = self.instance.topico.perguntar_inteligencia_artificial(
            self.cleaned_data['pergunta_ia'], self.cleaned_data['arquivos']
        )
        return super().submit()


class EnviarRespostaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = 'resposta',
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resposta'].initial = self.instance.resposta_ia

    def submit(self):
        self.instance.data_resposta = datetime.datetime.now()
        return super().submit()

class AdicionarABaseConhecimentoForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ()

    def submit(self):
        pergunta_frequente = PerguntaFrequente.objects.create(
            topico=self.instance.topico,
            pergunta=self.instance.pergunta_ia,
            resposta=self.instance.resposta
        )
        self.instance.pergunta_frequente = pergunta_frequente
        return super().submit()
