import os
import tempfile
from django.apps import apps
from django.core.files.storage import Storage
from django.conf import settings
from django.contrib.staticfiles.finders import AppDirectoriesFinder
from .s3 import Client

"""
if USE_S3:
    S3_URL = os.environ.get('S3_URL', 'https://api.minio.aplicativo.click/test3')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', 'admin')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')
    STORAGES = {
        "default": {"BACKEND": "slth.storage.S3Storage"},
        "staticfiles": {"BACKEND": "slth.storage.StaticStorage"}
    }
"""

class File:
    def __init__(self, client, name, mode='rb'):
        self.client = client
        self.name = name
        self.mode = mode
    
    def read(self):
        content = self.client.get_object(self.name)
        return content if 'b' in self.mode else content.decode()
    
    def write(self, content):
        content = content if 'b' in self.mode else content.encode()
        return self.client.put_object(self.name, content)


class S3Storage(Storage):

    def __init__(self):
        url = settings.S3_URL
        access_key = settings.S3_ACCESS_KEY
        secret_key = settings.S3_SECRET_KEY
        self.client = Client(url, access_key, secret_key)

    def _open(self, name, mode='rb'):
        return File(self.client, name, mode=mode)

    def _save(self, name, content):
        return self._open(name, mode='wb').write(content)

    def path(self, name):
        tmp_path = tempfile.mktemp()
        with open(tmp_path, 'wb') as file:
            file.write(self._open(name).read())
        return tmp_path

    def exists(self, name):
        return bool(self.client.list_objects(name))
    
    def delete(self, name):
        self.client.delete_object(name)

    def url(self, name):
        return self.client.get_object(name, only_url=True)


class StaticStorage(S3Storage):

    def url(self, name):
        return f'{self.client.url}/static/{name}'
    
    def collectstatic(self):
        local = {}
        finder = AppDirectoriesFinder()
        ignore_patterns = ['CVS', '.*', '*~'] 
        for name, storage in finder.list(ignore_patterns):
            path = storage.path(name)
            md5 = s3.md5(path)
            local[f'static/{name}'] = dict(path=path, md5=md5, status=None)
        remote = self.client.list_objects('static/')
        print(remote)
        for name, info in local.items():
            md5 = remote.get(name)
            if md5:
                del remote[name]
                if info['md5'] == md5:
                    info['status'] = 'equals'
                else:
                    info['status'] = 'updated'
            else:
                info['status'] = 'created'
            
            if info['status'] in ('created', 'updated'):
                with open(info['path'], 'rb') as file:
                    self.open(name, 'wb').write(file.read())

            print(name, info['status'])
        for name in remote:
            self.delete(name)
            print(name, 'deleted')
        return local
