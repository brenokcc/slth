import json
import types
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.utils.text import slugify
from django.db import models


def role_filter_field(request):
    value = request.GET.get('userrole')
    choices = [{'id': '', 'text': ''}]
    choices.extend({'id': k, 'text': v} for k, v in ['adm', 'Administrador'])
    return dict(name='userrole', type='select', value=value, label='Papel', choices=choices)


def filter_field(model, lookups, request):
    name = lookups.strip()
    suffix = None
    choices = None
    field = None
    value = None
    ignore = 'icontains', 'contains', 'gt', 'gte', 'lt', 'lte', 'id', 'year', 'month'
    tmp = []
    for lookup in name.split('__'):
        if lookup in ignore:
            suffix = lookup
        else:
            tmp.append(lookup)
    field = model.get_field('__'.join(tmp)) if tmp else None
    if field:
        if getattr(field, 'choices'):
            field_type = 'select'
            choices = [{'id': k, 'text': v} for k, v in field.choices]
        elif isinstance(field, models.CharField):
            field_type = 'text'
            value = request.GET.get(name)
        elif isinstance(field, models.BooleanField):
            field_type = 'boolean'
            value = request.GET.get(name)
            if value:
                value = value == 'true'
        elif isinstance(field, models.DateField):
            field_type = 'text' if suffix in ('year', 'month') else 'date'
        elif isinstance(field, models.ForeignKey):
            field_type = 'select'
            value = request.GET.get(name)
            if value:
                value = dict(id=value, text=request.GET.get(f'{name}__autocomplete'))
        elif isinstance(field, models.ManyToManyField):
            field_type = 'select'
        return dict(name=name, type=field_type, value=value, label=str(field.verbose_name))
    return None


def to_calendar(qs, request, attr_name):
    today = date.today()
    day = request.GET.get(f'{attr_name}__day')
    month = request.GET.get(f'{attr_name}__month')
    year = request.GET.get(f'{attr_name}__year')
    if month and year:
        start = date(int(year), int(month), 1)
    else:
        start = qs.filter(**{f'{attr_name}__month': today.month}).values_list(attr_name, flat=True).first()
        if start is None:
            start = qs.order_by(attr_name).values_list(attr_name, flat=True).first() or today
        month = start.month
        year = start.year
    current = date(start.year, start.month, 1)
    qs = qs.filter(**{f'{attr_name}__year': start.year, f'{attr_name}__month': start.month})
    total = {}
    for key in qs.values_list(attr_name, flat=True):
        key = key.strftime('%d/%m/%Y')
        if key not in total:
            total[key] = 0
        total[key] += 1
    if day:
        qs = qs.filter(**{f'{attr_name}__day': day})
    next = current + timedelta(days=31)
    previous = current + timedelta(days=-1)
    return qs, dict(
        field=attr_name, total=total,
        day=day, month=month, year=year, next=dict(month=next.month, year=next.year),
        previous=dict(month=previous.month, year=previous.year)
    )


def serialize(obj, primitive=False):
    if obj is None:
        return None
    elif isinstance(obj, dict):
        return obj
    elif isinstance(obj, date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, datetime):
        return obj.strftime('%d/%m/%Y %H:%M:%S')
    elif isinstance(obj, list):
        return [serialize(obj) for obj in obj]
    elif isinstance(obj, Model):
        return str(obj) if primitive else dict(pk=obj.pk, str=str(obj))
    elif isinstance(obj, QuerySet) or isinstance(obj, Manager):
        if primitive:
            return [str(obj) for obj in obj.filter()]
        else:
            return [dict(pk=item.pk, str=str(item)) for item in obj.filter()]
    return str(obj)

def getfield(obj, name_or_names, request=None, size=100):
    fields = []
    if isinstance(name_or_names, str):
        value = getattr(obj, name_or_names) if obj else None
        fields.append(dict(type='field', name=name_or_names, value=serialize(value, primitive=True), size=size))
    elif isinstance(name_or_names, LinkField):
        value = getattr(obj, name_or_names.name) if obj else None
        field = dict(type='field', name=name_or_names.name, value=serialize(value, primitive=True), size=size)
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

class Serializer:
    def __init__(self, obj, request=None):
        self.obj = obj
        self.request = request
        self.only = request.GET.getlist('only') if request else ()
        if isinstance(obj, Model):
            self.data = dict(type='instance', title=str(obj), actions=[], data=[])
        elif isinstance(self.obj, QuerySet) or isinstance(self.obj, Manager):
            self.obj = self.obj.filter()
            #self.data= dict(type='queryset', title=self.obj.model._meta.verbose_name_plural, data={})
            self.data = QuerysetSerializer(self.obj, request).serialize(True)
    
    def fields(self, *names):
        for name in names:
            self.data['data'].extend(getfield(self.obj, name, self.request))
        return self
    
    def relation(self, name):
        title = name
        if not self.only or slugify(title) in self.only:
            attr = getattr(self.obj, name)
            value = attr() if type(attr) == types.MethodType else attr
            data = serialize(value)
            if isinstance(value, QuerySet) or isinstance(value, Manager):
                data = dict(type='queryset', data=data)
            self.data['data'].append(dict(type='fieldset', slug=slugify(title), title=name, data=data))
        return self
    
    def endpoint(self, title, cls):
        if not self.only or slugify(title) in self.only:
            endpoint = cls(self.request, self.obj)
            if endpoint.check_permission():
                data = serialize(endpoint.get())
            self.data['data'].append(
                dict(type='fieldset', slug=slugify(title), title=title, actions=[], data=data)
            )
        return self

    def fieldset(self, title, names, relation=None):
        if not self.only or slugify(title) in self.only:
            actions=[]
            fields=[]
            obj = getattr(self.obj, relation) if relation else self.obj
            for name in names:
                fields.extend(getfield(obj, name, self.request))
            self.data['data'].append(
                dict(type='fieldset', title=title, slug=slugify(title), actions=actions, data=fields)
            )
        return self
    
    def serialize(self, debug=False):
        if not self.data['data']:
            self.data['data'] = serialize(self.obj)
        if debug:
            json.dumps(self.data, indent=2, ensure_ascii=False)
        return self.data


class QuerysetSerializer:
    def __init__(self, qs, request):
        self.qs = qs
        self.request = request

    def serialize(self, debug=False):
        title = str(self.qs.model._meta.verbose_name_plural)
        url = self.request.path
        subset = None
        actions = []
        filters = []
        search = []
        subsets = []
        aggregations = []
        template = None
        list_calendar = None
        calendar = None

        subset = self.request.GET.get('subset')
        subset = None if subset == 'all' else subset
        page = int(self.request.GET.get('page', 1))
        page_size = min(int(self.request.GET.get('page_size', 10)), 1000)
        qs = self.qs.filter()
        qs = qs.order_by('id') if not qs.ordered else qs
        if list_calendar:
            qs, calendar = to_calendar(qs, self.request, list_calendar)
        if subset:
            qs = getattr(qs, self.subset)()
        metadata = qs.metadata
        if metadata:
            if subset and 'subsets' in metadata:
                subset_metadata = metadata['subsets'][subset]
                if subset_metadata:
                    metadata = {k: v for k, v in metadata.items()}
                    if subset_metadata['actions']:
                        metadata['actions'] = subset_metadata['actions']
                    if subset_metadata.get('requires'):
                        metadata['requires'] = subset_metadata['requires']
                    if len(subset_metadata['filters']) > 1:
                        metadata['filters'] = subset_metadata['filters']
            template = metadata.get('template')
            title = metadata.get('title') or title

            for name in metadata.get('search', ()):
                search.append(name)

            for lookup in metadata.get('filters', ()):
                if lookup.endswith('userrole'):
                    field = role_filter_field(self.request)
                else:
                    field = filter_field(self.qs.model, lookup, self.request)
                if field:
                    filters.append(field)

            for name in metadata.get('subsets', ()):
                subsets.append(dict(name=name, label=name, count=getattr(self.qs, name)().count()))

            for name in metadata.get('aggregations', ()):
                api_name = name[4:] if name.startswith('get_') else name
                aggregation = dict(name=api_name, label=api_name, value=getattr(self.qs, name)())
                if isinstance(aggregation['value'], Decimal):
                    aggregation['value'] = str(aggregation['value']).replace('.', ',')
                aggregations.append(aggregation)

        rows = []
        start = page_size * (page - 1)
        end = start + page_size
        qs = qs.contextualize(self.request)[start:end]
        for obj in qs:
            fields = qs.metadata.get('fields', [field.name for field in qs.model._meta.fields])
            rows.append(Serializer(obj, self.request).fields(*fields).serialize())


        data = {}
        model_name = self.qs.model.__name__
        data.update(type='queryset', model=model_name, title=title, icon=None, url=url, actions=actions, filters=filters, search=search, data=rows)
        if calendar:
            data.update(calendar=calendar)
            data['filters'].extend([
                {'name': '{}__day'.format(self.calendar['field']), 'type': 'hidden', 'value': self.calendar['day']},
                {'name': '{}__month'.format(self.calendar['field']), 'type': 'hidden', 'value': self.calendar['month']},
                {'name': '{}__year'.format(self.calendar['field']), 'type': 'hidden', 'value': self.calendar['year']}
            ])
        if subsets:
            data.update(subsets=subsets, subset=subset)
        if aggregations:
            data.update(aggregations=aggregations)
        if template:
            data.update(html=render_to_string(template, data))
        data.update(page_size=page_size, page_sizes=[5, 10, 15, 20, 25, 50, 100])
        if debug:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return data