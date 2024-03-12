from ..views import Endpoint
from . import forms
from django.contrib.auth.models import User, Group


class HealthCheck(Endpoint):

    def get(self):
        return dict(version='1.0.0')


class Register(Endpoint):
    form = forms.RegisterForm


class AddUser(Endpoint):
    form = forms.UserForm

class EditUser(Endpoint):
    form = forms.UserForm

    def load(self):
        self.source = User.objects.get(pk=self.args[0])

class ListUsers(Endpoint):
    
    def load(self):
        self.source = User.objects.all()
    

class ViewUser(Endpoint):
    def load(self):
        self.source = User.objects.get(pk=self.args[0])
