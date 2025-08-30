import tempfile
from django.apps import apps
from django.core.files.storage import Storage
from django.conf import settings
from django.contrib.staticfiles.finders import AppDirectoriesFinder
from . import s3


class File:
    def __init__(self, bucket, name, mode='rb'):
        self.bucket = bucket
        self.name = name
        self.mode = mode
    
    def read(self):
        response = s3.get_object(self.bucket, self.name)
        return response.content if 'b' in self.mode else response.content.decode()
    
    def write(self, content):
        content = content if 'b' in self.mode else content.encode()
        return s3.put_object(self.bucket, self.name, content)


class S3Storage(Storage):

    def __init__(self):
        self.bucket = "test3"
        # if bucket does not exist, create and define the policy
        if not s3.list_objects(self.bucket):
            s3.put_object(self.bucket)
            s3.aws_request("PUT", self.bucket, "policy=", s3.policy(self.bucket))

    def _open(self, name, mode='rb'):
        return File(self.bucket, name, mode=mode)

    def _save(self, name, content):
        return self._open(name, mode='wb').write(content)

    def path(self, name):
        tmp_path = tempfile.mktemp()
        with open(tmp_path, 'wb') as file:
            file.write(self._open(name).read())
        return tmp_path

    def exists(self, name):
        return bool(s3.list_objects(self.bucket, name))
    
    def delete(self, name):
        s3.delete_object(self.bucket, name)

    def url(self, name):
        print(name, 8888)
        if name.startswith('static/'):
            return f'/{name}'
        return s3.get_object(self.bucket, name, only_url=True)
    
    def staticfiles(self, sync=False):
        local = {}
        finder = AppDirectoriesFinder()
        # apps.get_app_config("staticfiles").ignore_patterns
        ignore_patterns = ['CVS', '.*', '*~'] 
        for name, storage in finder.list(ignore_patterns):
            path = storage.path(name)
            md5 = s3.md5(path)
            local[f'static/{name}'] = dict(path=path, md5=md5, status=None)
        if sync:
            remote = s3.list_objects(self.bucket, 'static/')
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
