import os
import json
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from slth.models import User
from slth.application import Application as ApplicationConfig

def authenticate(code):
    application = ApplicationConfig.get_instance()
    for provider in application.oauth:
        client_secret = provider['client_secret']
        if client_secret.startswith('$'):
            client_secret = os.environ[client_secret[1:]]
        redirect_uri = "{}{}".format(settings.SITE_URL, provider['redirect_uri'])
        access_token_request_data = dict(
            grant_type='authorization_code', code=code, redirect_uri=redirect_uri,
            client_id=provider['client_id'], client_secret=client_secret
        )
        response = requests.post(provider['access_token_url'], data=access_token_request_data, verify=False)
        # print(response.text)
        if response.status_code == 200:
            data = json.loads(response.text)
            headers = {
                'Authorization': 'Bearer {}'.format(data.get('access_token')),
                'x-api-key': client_secret
            }
            if provider.get('user_data_method', 'GET').upper() == 'POST':
                response = requests.post(provider['user_data_url'], data={'scope': data.get('scope')}, headers=headers, verify=False)
            else:
                response = requests.get(provider['user_data_url'], data={'scope': data.get('scope')}, headers=headers, verify=False)
            # print(response.text)
            if response.status_code == 200:
                data = json.loads(response.text)
                username = data[provider['user_username']]
                user = User.objects.filter(username=username).first()
                if user:
                    return user
                elif provider.get('user_create'):
                    user = User.objects.create(
                        username=username,
                        email=data[provider['user_email']] if provider['user_email'] else ''
                    )
                    return user
                else:
                    raise ValidationError(f'Usuário "{username}" não cadastrado.')
        else:
            raise ValidationError(response.text)
    return

def providers():
    oauth = []
    application = ApplicationConfig.get_instance()
    for provider in application.oauth:
        redirect_uri = "{}{}".format(settings.SITE_URL, provider['redirect_uri'])
        authorize_url = '{}?response_type=code&client_id={}&redirect_uri={}'.format(
            provider['authorize_url'], provider['client_id'], redirect_uri
        )
        if provider.get('scope'):
            authorize_url = '{}&scope={}'.format(authorize_url, provider.get('scope'))
        oauth.append(dict(label=f'Entrar com {provider["name"]}', url=authorize_url))
    return oauth
