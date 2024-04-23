import datetime
from slth import forms
from .models import Consulta, PerguntaFrequente


class ConsultarIAForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = 'pergunta_ia',
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pergunta_ia'].initial = self.instance.pergunta

    def submit(self):
        self.instance.data_consulta = datetime.datetime.now()
        self.instance.resposta_ia = self.instance.topico.perguntar_inteligencia_artificial(self.instance.pergunta_ia)
        self.instance.save()


class EnviarRespostaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = 'resposta',
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resposta'].initial = self.instance.resposta_ia

    def submit(self):
        self.instance.data_resposta = datetime.datetime.now()
        self.instance.save()

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
