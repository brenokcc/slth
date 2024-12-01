from .. import endpoints
from .. import forms
from ..models import Profile
from ..components import Response


class UserProfile(endpoints.Endpoint):
    photo = forms.ImageField(label='Foto', required=False)
    password1 = forms.CharField(label='Informe a Senha', widget=forms.PasswordInput(), required=False)
    password2 = forms.CharField(label='Confirme a Senha', widget=forms.PasswordInput(), required=False)
    
    class Meta:
        verbose_name = 'Editar Perfil'
    
    def get(self):
        return (
            self.formfactory(self.get_profile())
            .fieldset('Dados Gerais', ('photo',))
            .fieldset('Acesso ao Sistema', (('password1', 'password2'),))
        )
    
    def post(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 == password2:
            if password1 and password2:
                self.request.user.set_password(password1)
                self.request.user.save()
        else:
            raise forms.ValidationError('Repita a mesma senha.')
        return Response(message="Ação realizada com sucesso", store=dict(application=None), redirect='/api/dashboard/')
    
    def get_profile(self):
        return Profile.objects.get_or_create(user=self.request.user, defaults=dict(photo=None))[0]

    def check_permission(self):
        return self.request.user.is_authenticated
