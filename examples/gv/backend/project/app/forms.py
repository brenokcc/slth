import datetime
from slth import forms
from .models import Consulta


class ConsultarIAForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = 'pergunta_ia',

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
