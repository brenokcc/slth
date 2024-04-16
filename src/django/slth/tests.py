import os
from datetime import date, timedelta
from unittest import skipIf
from django.apps import apps
from django.core.cache import cache
from django.core.management import call_command
from .selenium import SeleniumTestCase
from django.contrib.auth.models import User


# @skipIf(os.environ.get("FRONTEND_PROJECT_DIR") is None, "FRONTEND_PROJECT_DIR is not set")
class IntegrationTest(SeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test(self):
        if self.step("1"):
            self.create_superuser("admin@tavos.com", "123")
        if self.step("2"):
            self.open("/admin/")
            self.wait(3)
            self.open('/')


import base64
import json

import requests
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from .selenium import SeleniumTestCase


class HttpData:
    def __init__(self, data=None):
        self._mutable = False
        self.data = data or {}
        
    def get(self, k, default=None):
        v = self.data.get(k)
        if isinstance(v, list):
            return v[0] if v else default
        return default if v is None else v

    def getlist(self, k):
        return self.data.get(k) or []
    
    def __contains__(self, item):
        return item in self.data
    
    def __getitem__(self, item):
        return self.data[item]
    
    def clear(self):
        self.data.clear()

class HttpRequest:
    def __init__(self, querystring=None, data=None):
        self.path = ''
        self.scheme = 'http'
        self.method = 'POST' if data else 'GET'
        self.body = None
        self.GET = HttpData()
        self.POST = HttpData(data)
        self.META = {
            'CONTENT_TYPE': '_application/json'
        }
        self.user = User.objects.filter(is_superuser=True).first() or User()
        self.FILES = None

        if querystring:
            for parameter in querystring[1:].split('&'):
                name, value = parameter.split('=')
                if name not in self.GET.data:
                    self.GET.data[name] = []
                self.GET.data[name].append(value)

    def get_host(self):
        return 'localhost'
    
    def get_port(self):
        return '8000'

class ServerTestCase(StaticLiveServerTestCase):

    def __init__(self, *args, **kwargs):
        self.authorization = None
        self.debug = False
        super().__init__(*args, **kwargs)

    def get_headers(self, ):
        if self.authorization:
            headers = {}
            headers['Authorization']= self.authorization
            return headers
        return None

    def log(self, method, url, data, response):
        if self.debug:
            print('{}: {}'.format(method, url))
            try:
                if data:
                    print('Input:\n{}'.format(json.dumps(data, indent=2, ensure_ascii=False)))
                print('Output:\n{}'.format(json.dumps(response.json(), indent=2, ensure_ascii=False)))
            except Exception:
                print(response.text)
                import traceback
                print(traceback.format_exc())
                print(data)
            print('\n')

    def url(self, path):
        if path.startswith('/o/'):
            return '{}{}'.format(self.live_server_url, path)
        return '{}{}'.format(self.live_server_url, path)

    def get(self, path, data=None, status_code=200):
        url = self.url(path)
        response = requests.get(url, data=data, headers=self.get_headers())
        self.log('GET', url, data, response)
        self.assertEquals(response.status_code, status_code)
        return response.json()

    def post(self, path, data=None, json=None, status_code=200):
        url = self.url(path)
        response = requests.post(url, data=data, json=json, headers=self.get_headers())
        self.log('POST', url, data or json, response)
        self.assertEquals(response.status_code, status_code)
        return response.json()

    def put(self, path, data=None, status_code=200):
        url = self.url(path)
        response = requests.put(url, data=data, headers=self.get_headers())
        self.log('PUT', url, data, response)
        self.assertEquals(response.status_code, status_code)
        return response.json()

    def delete(self, path, data=None, status_code=200):
        url = self.url(path)
        response = requests.delete(url, data=data, headers=self.get_headers())
        self.log('DELETE', url, data, response)
        self.assertEquals(response.status_code, status_code)
        return response.json()

    def login(self, username, password):
        self.authorization = 'Basic {}'.format(
            base64.b64encode('{}:{}'.format(username, password).encode()).decode()
        )

    def authorize(self, access_token, token_type='Bearer'):
        self.authorization = '{} {}'.format(token_type, access_token)

    def logout(self):
        self.authorization = None

    def assert_model_count(self, model, n):
        self.assertEquals(self.objects(model).count(), n)

    def objects(self, model):
        return apps.get_model(model).objects
    
    def print(self, data):
        print(json.dumps(data, indent=2, ensure_ascii=False))


    @staticmethod
    def create_user(username, password, is_superuser=False):
        user = User.objects.create(username=username)
        user.set_password(password)
        user.is_superuser = is_superuser
        user.save()
        return user
