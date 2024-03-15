import json
from datetime import date, datetime
from django.apps import apps
from django.db import models
from django.utils.text import slugify


def serialize(obj):
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, datetime):
        return obj.strftime('%d/%m/%Y %H:%M:%S')
    elif isinstance(obj, list):
        return [serialize(obj) for obj in obj]
    elif isinstance(obj, models.Model):
        return dict(pk=obj.pk, str=str(obj))
    elif isinstance(obj, models.QuerySet):
        return [dict(pk=item.pk, str=str(item)) for item in obj]
    return str(obj)

def getfield(obj, name_or_names, request=None, size=100):
    fields = []
    if isinstance(name_or_names, str):
        value = getattr(obj, name_or_names)
        fields.append(dict(type='field', name=name_or_names, value=serialize(value), size=size))
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name)
        field = dict(type='field', name=name_or_names.name, value=serialize(value), size=size)
        if value:
            endpoint = name_or_names.endpoint(request, value.id)
            if endpoint.check_permission():
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
    def __init__(self, obj, request=None):
        self._obj = obj
        self._title= str(obj)
        self._actions = []
        self._data = []
        self._request = request
        self._only = request.GET.getlist('only') if request else ()
    
    def fields(self, *names):
        for name in names:
            self._data.extend(getfield(self._obj, name, self._request))
        return self
    
    def endpoint(self, title, cls):
        if not self._only or slugify(title) in self._only:
            endpoint = cls(self._request, self._obj)
            if endpoint.check_permission():
                data = serialize(endpoint.get())
            self._data.append(dict(type='fieldset', slug=slugify(title), title=title, actions=[], data=data))
        return self

    def fieldset(self, title, *names, relation=None):
        if not self._only or slugify(title) in self._only:
            actions=[]
            fields=[]
            obj = getattr(self._obj, relation) if relation else self._obj
            for name in names:
                fields.extend(getfield(obj, name, self._request))
            self._data.append(dict(type='fieldset', title=title, slug=slugify(title), actions=actions, data=fields))
        return self
    
    def serialize(self, debug=False):
        data = dict(title=self._title, actions=self._actions, data=self._data)
        if debug:
            json.dumps(data, indent=2, ensure_ascii=False)
        return data

