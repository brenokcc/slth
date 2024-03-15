import json
from django.apps import apps
from django.db import models

def serialize(obj):
    return str(obj)

def getfield(obj, name_or_names, size=100):
    fields = []
    if isinstance(name_or_names, str):
        value = getattr(obj, name_or_names)
        fields.append(dict(type='field', name=name_or_names, value=serialize(value), size=size))
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name)
        field = dict(type='field', name=name_or_names.name, value=serialize(value), size=size)
        if value:
            field.update(url=name_or_names.endpoint.get_api_url(value.id))
        fields.append(field)
    else:
        for name in name_or_names:
            fields.append(getfield(obj, name, size=int(100/len(name_or_names))))
    return fields

class LinkField:
    def __init__(self, name, endpoint):
        self.name = name
        self.endpoint = endpoint

class Serializar:
    def __init__(self, obj):
        self._obj = obj
        self._title= str(obj)
        self._actions = []
        self._data = []
    
    def fields(self, *names):
        for name in names:
            self._data.extend(getfield(self._obj, name))
        return self

    def fieldset(self, title, *names, relation=None):
        actions=[]
        fields=[]
        obj = getattr(self._obj, relation) if relation else self._obj
        for name in names:
            fields.extend(getfield(obj, name))
        self._data.append(dict(type='fieldset', title=title, actions=actions, fields=fields))
        return self
    
    def serialize(self, debug=False):
        data = dict(title=self._title, actions=self._actions, data=self._data)
        output = json.dumps(data, indent=4, ensure_ascii=False)
        if debug:
            print(output)
        return output

