import os
import json
import requests
from django.conf import settings
from slth.models import User
from slth import APPLICATON


def authenticate(code):
    for provider in APPLICATON.get('oauth', {}).values():
        client_secret = provider['client_secret']
        if client_secret.startswith('$'):
            client_secret = os.environ[client_secret[1:]]
        print(client_secret)
        redirect_uri = "{}{}".format(settings.SITE_URL, provider['redirect_uri'])
        access_token_request_data = dict(
            grant_type='authorization_code', code=code, redirect_uri=redirect_uri,
            client_id=provider['client_id'], client_secret=client_secret
        )
        response = requests.post(provider['access_token_url'], data=access_token_request_data, verify=False)
        if response.status_code == 200:
            data = json.loads(response.text)
            headers = {
                'Authorization': 'Bearer {}'.format(data.get('access_token')),
                'x-api-key': client_secret
            }
            if provider.get('user_data_method', 'GET').upper() == 'POST':
                response = requests.post(provider['user_data_url'], data={'scope': data.get('scope')}, headers=headers)
            else:
                response = requests.get(provider['user_data_url'], data={'scope': data.get('scope')}, headers=headers)
            if response.status_code == 200:
                data = json.loads(response.text)
                username = data[provider['user_data']['username']]
                user = User.objects.filter(username=username).first()
                if user:
                    return user
                elif provider.get('user_data').get('create'):
                    user = User.objects.create(
                        username=username,
                        email=data[provider['user_data']['email']] if provider['user_data']['email'] else ''
                    )
                    return user
        else:
            print(response.text)
    return

def providers():
    oauth = []
    for provider in APPLICATON.get('oauth', {}).values():
        redirect_uri = "{}{}".format(settings.SITE_URL, provider['redirect_uri'])
        authorize_url = '{}?response_type=code&client_id={}&redirect_uri={}'.format(
            provider['authorize_url'], provider['client_id'], redirect_uri
        )
        if provider.get('scope'):
            authorize_url = '{}&scope={}'.format(authorize_url, provider.get('scope'))
        oauth.append(dict(label=f'Entrar com {provider["name"]}', url=authorize_url))
    return oauth
