import os
import requests
import base64
from datetime import datetime, timedelta
from django.shortcuts import render
 
 
API_KEY = os.environ.get('ZOOM_API_KEY')
API_SEC = os.environ.get('ZOOM_API_SEC')
ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')

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
        data = {"topic": topic}
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
