import os
import slth
import json
import types
from decimal import Decimal
from datetime import date, datetime
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.utils.text import slugify
from .exceptions import JsonResponseException
from .utils import absolute_url, build_url
from .components import Image, FileLink, FileViewer, Banner, Boxes
from django.db.models.fields.files import ImageFieldFile, FieldFile


def getattrr(obj, args):
    return getattr_rec(obj, args.split('__'))


def getattr_rec(obj, args):
    if obj is None:
        return None
    if len(args) > 1:
        attr = args.pop(0)
        return getattr_rec(getattrr(obj, attr), args)
    else:
        return getattr(obj, args[0])


def to_snake_case(name):
    return slugify(name).replace('-', '_')


def serialize(obj, primitive=False, request=None, logging=False):
    if obj is None:
        return None
    elif isinstance(obj, dict):
        if request:
            if isinstance(obj, Image) or isinstance(obj, Banner):
                if isinstance(obj['src'], ImageFieldFile):
                    obj['src'] = build_url(request, obj['src'].url) if obj['src'] else None
            elif isinstance(obj, FileLink) or isinstance(obj, FileViewer):
                if isinstance(obj['url'], FieldFile):
                    obj['url'] = build_url(request, obj['url'].url) if obj['url'] else None
        return obj
    elif isinstance(obj, datetime):
        return obj.strftime('%d/%m/%Y %H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, bool):
        return obj
    if isinstance(obj, Decimal) or isinstance(obj, float):
        return str(obj).replace('.', ',')
    elif isinstance(obj, list):
        return [serialize(obj) for obj in obj]
    elif isinstance(obj, Model):
        if logging:
            return f'{obj.pk}:{str(obj)}'
        else:
            try:
                return str(obj) if primitive else dict(pk=obj.pk, str="{}".format(obj))
            except TypeError:
                return str(obj) if primitive else dict(pk=obj.pk, str="?")
    elif isinstance(obj, QuerySet) or isinstance(obj, Manager) or type(obj).__name__ == 'ManyRelatedManager':
        if logging:
            return [f'{obj.pk}:{str(obj)}' for obj in obj.filter()]
        else:
            return [str(obj) for obj in obj.filter()] if primitive else obj.serialize()
    elif isinstance(obj, ImageFieldFile) or isinstance(obj, FieldFile):
        return str(obj)
    elif hasattr(obj, 'serialize'):
        return obj.serialize()
    return str(obj)

def getfield(obj, name_or_names, request=None):
    cls = type(obj)
    get_display_methods = getattr(cls, '_display_methods_', None)
    if get_display_methods is None:
        get_display_methods = [name for name in dir(cls) if name.endswith("_display")]
        setattr(obj, '_display_methods_', get_display_methods)
    if isinstance(name_or_names, str):
        if ':' in name_or_names:
            name_or_names, action_name = name_or_names.split(':')
        else:
            name_or_names, action_name = name_or_names, None
        get_display_method_name = f"get_{name_or_names}_display"
        if get_display_method_name in get_display_methods:
            attr = getattrr(obj, get_display_method_name)()
        else:
            attr = getattrr(obj, name_or_names)
        if type(attr) == types.MethodType:
            value = attr()
            label = getattr(attr, 'verbose_name', name_or_names.replace('get_', ''))
        elif name_or_names.startswith('get_') and name_or_names.endswith('_display'):
            value = attr()
            label = cls.get_field(name_or_names[4:-8]).verbose_name
        else:
            value = attr
            label = cls.get_field(name_or_names).verbose_name
        label = label.title().replace('_', ' ') if label and label.islower() else label
        field = dict(type='field', name=name_or_names, label=label, value=serialize(value, primitive=True, request=request))
        if action_name:
            cls = slth.ENDPOINTS[action_name]
            endpoint = cls.instantiate(request, obj)
            if endpoint.check_permission():
                field.update(url=endpoint.get_api_url(obj.id))
        return field
    else:
        fields = []
        for name in name_or_names:
            fields.append(getfield(obj, name, request))
        return fields


class Serializer:
    def __init__(self, obj=None, request=None, serializer=None, type='object', title=None, show_title=True, info=None):
        self.path = serializer.path.copy() if serializer else []
        self.obj = obj
        self.lazy = False
        self.ignore_only = False
        self.request = request
        self.metadata = dict(actions=[], content=[], allow=[])
        self.serializer:Serializer = serializer
        self.type = type
        if title:
            self.title = title
            self.path.append(to_snake_case(title))
        elif isinstance(obj, Model):
            self.title = str(obj)
        else:
            self.title = None
        self.show_title = show_title
        self.base_url = None
        if info:
            self.info(info)

    def actions(self, *actions) -> 'Serializer':
        self.metadata['actions'].extend(actions)
        self.metadata['allow'].extend(actions)
        return self
    
    def info(self, text):
        self.metadata['info'] = text
        return self
    
    def todo(self, *endpoints):
        self.metadata['todo'] = endpoints
        return self
    
    def field(self, name, reload=True, condition=None, roles=()) -> 'Serializer':
        self.metadata['content'].append(('field', name, dict(name=name, reload=reload, condition=condition, roles=roles)))
        return self
        
    def fields(self, *names, condition=None, roles=()) -> 'Serializer':
        self.metadata['content'].append(('fields', None, dict(names=names, condition=condition, roles=roles)))
        return self
    
    def fieldset(self, title, fields=(), actions=(), attr=None, reload=True, condition=None, roles=(), info=None) -> 'Serializer':
        self.metadata['allow'].extend(actions)
        item = dict(title=title, names=fields, attr=attr, actions=actions, reload=reload, condition=condition, roles=roles, info=info)
        self.metadata['content'].append(('fieldset', to_snake_case(title), item))
        return self
        
    def queryset(self, name, condition=None, roles=()) -> 'Serializer':
        self.metadata['content'].append(('queryset', name, dict(condition=condition, roles=roles)))
        return self
    
    def endpoint(self, cls, wrap=False, condition=None, roles=()) -> 'Serializer':
        if isinstance(cls, str):
            cls = slth.ENDPOINTS[cls]
        key = cls.get_api_name().replace('.', '_')
        self.metadata['content'].append(('endpoint', key, dict(cls=cls, wrap=wrap, condition=condition, roles=roles)))
        return self
    
    def append(self, component, condition=None, roles=()) -> 'Serializer':
        self.metadata['content'].append(('component', 'shortcut', dict(component=component, condition=condition, roles=roles)))
        return self
    
    def shortcuts(self, *endpoints) -> 'Serializer':
        boxes = Boxes()
        for name in endpoints:
            cls = slth.ENDPOINTS[name]
            endpoint = cls().contextualize(self.request)
            if endpoint.check_permission():
                icon = endpoint.get_icon() or "link"
                label = endpoint.get_verbose_name()
                url = build_url(self.request, cls.get_api_url())
                boxes.append(icon, label, url)
        return self.append(boxes)

    def section(self, title=None, info=None) -> 'Serializer':
        show_title = True
        if title is None:
            title = 'group'
            show_title = False
        return Serializer(obj=self.obj, request=self.request, serializer=self, type='section', title=title, show_title=show_title, info=info)
    
    def group(self, title=None, info=None) -> 'Serializer':
        show_title = True
        if title is None:
            title = 'group'
            show_title = False
        return Serializer(obj=self.obj, request=self.request, serializer=self, type='group', title=title, show_title=show_title, info=info)

    def parent(self) -> 'Serializer':
        self.serializer.metadata['content'].append(('serializer', to_snake_case(self.title), dict(serializer=self, condition=None, roles=())))
        return self.serializer
    
    def endsection(self) -> 'Serializer':
        return self.parent()
    
    def endgroup(self) -> 'Serializer':
        return self.parent()
    
    def contextualize(self, request) -> 'Serializer':
        self.request = request
        return self
    
    def settitle(self, title) -> 'Serializer':
        if title != 'Visualizar':
            self.title = title
        return self
    
    def serialize(self, debug=False, forward_exception=False):
        try:
            return self.to_dict(debug=debug)
        except JsonResponseException as e:
            if self.serializer or forward_exception:
                raise e
            if debug:
                print(json.dumps(e.data, indent=2, ensure_ascii=False))
            return e.data
        
    def __str__(self):
        return f'{self.title} / {self.type}'

    def check_condition(self, name):
        if name:
            deny = False
            if name.startswith('not '):
                deny, name = name.split()
            attr = getattr(self.obj, name)
            if callable(attr):
                attr = attr()
            return not attr if deny else attr
        return True
    
    def check_role(self, names):
        from slth.models import Role
        return self.request.user.is_superuser or not names or Role.objects.filter(username=self.request.user.username, name__in=names).exists()

    def to_dict(self, debug=False):
        base_url = absolute_url(self.request).replace('?only=actions', '')
        if self.request is None and self.serializer:
            self.request = self.serializer.request
        if self.ignore_only:
            only = []
        else:
            only = self.request and self.request.GET.get('only', None)
            if only:
                only = only.split('__')

        if self.request and 'action' in self.request.GET and not only:
            cls = slth.ENDPOINTS[self.request.GET.get('action')]
            if cls:### and cls.get_key_name() in self.metadata['allow']:
                self.request.GET._mutable = True
                self.request.GET.pop('action', None)
                self.request.GET._mutable = False
                endpoint = cls.instantiate(self.request, self.obj)
                if endpoint.check_permission():
                    raise JsonResponseException(endpoint.serialize())
                
        actions = []
        if (not only or 'actions' in only) and not self.lazy:
            leaf = only and only[-1] == 'actions'
            for qualified_name in self.metadata['actions']:
                cls = slth.ENDPOINTS[qualified_name]
                endpoint = cls.instantiate(self.request, self.obj)
                if endpoint.check_permission():
                    if cls.has_args():
                        action = endpoint.get_api_metadata(self.request, base_url, self.obj.pk)
                        action['name'] = action['name'].replace(' {}'.format(self.obj._meta.verbose_name), '')
                    else:
                        action = endpoint.get_api_metadata(self.request, base_url)
                    actions.append(action)
            if leaf:
                raise JsonResponseException(actions)

        if not self.metadata['content'] and self.obj and isinstance(self.obj, Model):
            self.fields(*[field.name for field in type(self.obj)._meta.fields])
            for m2m in type(self.obj)._meta.many_to_many:
                self.queryset(m2m.name)
        
        items = []
        if not self.lazy:
            for i, (datatype, key, item) in enumerate(self.metadata['content']):
                if not self.check_condition(item['condition']):
                    continue
                if not self.check_role(item['roles']):
                    continue
                leaf = only and only[-1] == key
                lazy = i and self.type == 'group' and not leaf
                data = None
                if datatype == 'field':
                    path = self.path + [item['name']]
                    data = getfield(self.obj, item['name'], self.request)
                    if item['reload']:
                        data['url'] = absolute_url(self.request, 'only={}'.format('__'.join(path)))
                    if leaf: raise JsonResponseException(data)
                elif datatype == 'fields':
                    data = []
                    if not lazy:
                        for name in item['names']:
                            if key is None or not only or name in only:
                                data.append(getfield(self.obj, name, self.request))
                        if only and only[-1] == name: raise JsonResponseException(data)
                elif datatype == 'fieldset':
                    title = item['title']
                    names = item['names']
                    attr = item['attr']
                    reload = item['reload']
                    info = item['info']
                    if not only or key in only:
                        fieldset_actions=[]
                        fieldset_fields=[]
                        title = title.title() if title and title.islower() else title
                        url = absolute_url(self.request, 'only={}'.format('__'.join(self.path + [key])))
                        if lazy:
                            data = dict(type='fieldset', title=title, key=key, url=url)
                        else:
                            obj = getattr(self.obj, attr) if attr else self.obj
                            if obj:
                                for name in names:
                                    fieldset_fields.append(getfield(obj, name, self.request))
                            for qualified_name in item['actions']:
                                cls = slth.ENDPOINTS[qualified_name]
                                endpoint = cls.instantiate(self.request, obj)
                                if obj and endpoint.check_permission():
                                    fieldset_actions.append(endpoint.get_api_metadata(self.request, base_url, obj.pk))
                            data = dict(type='fieldset', title=title, info=info, key=key, url=url if reload else None, actions=fieldset_actions, data=fieldset_fields)
                        if leaf: raise JsonResponseException(data)
                elif datatype == 'queryset':
                    if not only or key in only:
                        attr = getattr(self.obj, key)
                        if type(attr) == types.MethodType:
                            title = getattr(attr, 'verbose_name', key.replace('get_', '').title())
                            value = attr().filter()
                        else:
                            title = getattr(attr, 'verbose_name', key.title())
                            value = attr.filter()
                        value.instance = self.obj
                        path = self.path + [key]
                        if lazy:
                            data = dict(type='queryset', title=title, key=key)
                        else:
                            data = value.settitle(title).attrname('__'.join(path)).contextualize(self.request).serialize(debug=False)
                        
                        data['url'] = absolute_url(self.request, 'only={}'.format('__'.join(path)))
                        if leaf:
                            raise JsonResponseException(data)
                elif datatype == 'endpoint':
                    data = {}
                    cls = item['cls']
                    wrap = item['wrap']
                    if not only or key in only:
                        returned = {}
                        endpoint = cls.instantiate(self.request, self.obj)
                        if endpoint.check_permission():
                            if not lazy:                     
                                returned = endpoint.process()
                                if isinstance(returned, QuerySet) or isinstance(returned, Serializer):
                                    returned.base_url = endpoint.base_url
                                    returned = returned.contextualize(self.request)
                            path = self.path + [key]
                            if wrap:
                                data = dict(type='fieldset', key=key, title= endpoint.get_verbose_name(), url=None, data=serialize(returned))
                            else:
                                data = serialize(returned)
                                if lazy:
                                    data['title'] = endpoint.get_verbose_name()
                            if isinstance(data, dict) and data.get('type') is None:
                                data['url'] = absolute_url(self.request, 'only={}'.format('__'.join(path)))
                            if leaf: raise JsonResponseException(data)
                            
                elif datatype == 'component':
                    data = {}
                    if not only or key in only:
                        data = serialize(item['component'])
                    path = self.path + [key]
                    data['url'] = absolute_url(self.request, 'only={}'.format('__'.join(path)))
                    if leaf: raise JsonResponseException(data)
                elif datatype == 'serializer':
                    serializer = item['serializer']
                    serializer.request = serializer.serializer.request
                    serializer.lazy = lazy
                    if not only or key in only:
                        serializer.lazy = False
                        serializer.ignore_only = self.ignore_only or leaf
                        data = serializer.to_dict()
                        if leaf: raise JsonResponseException(data)
                if data:
                    items.extend(data) if datatype == 'fields' else items.append(data)

        info = self.metadata.get('info')
        todo = []
        for action_name in self.metadata.get('todo', ()):
            cls = slth.ENDPOINTS[action_name]
            endpoint = cls.instantiate(self.request, self.obj)
            if endpoint.check_permission():
                if cls.has_args():
                    action = endpoint.get_api_metadata(self.request, base_url, self.obj.pk)
                else:
                    action = endpoint.get_api_metadata(self.request, base_url)
                todo.append(action)
        output = dict(type=self.type, title=self.title if self.show_title else None)
        if info:
            output.update(info=info)
        if todo:
            output.update(todo=todo)
        if self.serializer:
            datatype = to_snake_case(self.title)
            output.update(key=datatype)
        if self.path:
            url = absolute_url(self.request, 'only={}'.format('__'.join(self.path)))
        else:
            url = absolute_url(self.request)
        output.update(url=url)
        if not self.lazy:
            output.update(actions=actions, data=items)
        if debug:
            print(json.dumps(output, indent=2, ensure_ascii=False))
        return output
