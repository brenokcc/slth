import os
import requests
import base64
from datetime import datetime, timedelta
from django.shortcuts import render
 
 
API_KEY = os.environ.get('ZOOM_API_KEY')
API_SEC = os.environ.get('ZOOM_API_SEC')
ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
REDIRECT_URL = os.environ.get('ZOOM_REDIRECT_URL', 'http://localhost:8000')

ZOOM_SDK_KEY = os.environ.get('ZOOM_SDK_KEY')
ZOOM_SDK_SEC = os.environ.get('ZOOM_SDK_SEC')
 

def view(request):
    return render(request, 'zoom.html', dict(ZOOM_SDK_KEY=ZOOM_SDK_KEY, ZOOM_SDK_SEC=ZOOM_SDK_SEC))
 

def create_meeting(topic):
    if API_KEY and API_SEC and ACCOUNT_ID:
        url = 'https://zoom.us/oauth/token?grant_type=account_credentials&account_id={}'.format(os.environ.get('ZOOM_ACCOUNT_ID'))
        auth = base64.b64encode('{}:{}'.format(API_KEY, API_SEC).encode()).decode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic {}".format(auth)}
        print(url, headers)
        response = requests.post(url, headers=headers).json()
        print(response)
        data = {"topic": topic, "settings": {"join_before_host": True}}
        url = 'https://api.zoom.us/v2/users/me/meetings'
        token = response.get('access_token')
        headers = {'authorization': 'Bearer ' + token, 'content-type': 'application/json'}
        print(url, data)
        response = requests.post(url, json=data, headers=headers).json()
        print(response)
        number = response.get('id')
        password = response.get('encrypted_password')
        limit = datetime.now() + timedelta(minutes=40)
        return number, password, limit
    return None, None, None

def authorization_url():
    return 'https://zoom.us/oauth/authorize?response_type=code&client_id=' + API_KEY + '&redirect_uri=' + REDIRECT_URL


def tokens(code):
    ZOOM_API_KEY='IaRHnNqCREiuvBSfrhwOuA'
    ZOOM_API_SEC='zZBKpmuzveUnwOG3tCpnR3aAmBxx1zgl'
    ZOOM_REDIRECT_URL='https://telesaude.aplicativo.click/redirect'
    url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri={}'.format(code, ZOOM_REDIRECT_URL)
    auth = base64.b64encode('{}:{}'.format(ZOOM_API_KEY, ZOOM_API_SEC).encode()).decode()
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic {}".format(auth)}
    resp = requests.post(url, headers=headers).json()
    access_token = resp['access_token']
    refresh_token = resp['refresh_token']
