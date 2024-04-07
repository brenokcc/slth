import slth
from django.apps import apps
from django.db import models
from django.db.models import manager, Q, CharField, CASCADE
from django.db.models.aggregates import Sum, Avg
from django.db.models.base import ModelBase
from .statistics import Statistics
from functools import reduce
from datetime import datetime
import operator
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db.models import Model, QuerySet, Manager
from django.db import models
from .serializer import Serializer
from .exceptions import JsonResponseException
from .utils import absolute_url, append_url, build_url


class QuerySet(models.QuerySet):

    def __init__(self, *args, **kwargs):
        self.metadata = {}
        self.request = None
        super().__init__(*args, **kwargs)

    def counter(self, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).count(x=x, y=y) if x else super().count()

    def sum(self, z, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).sum(z, x=x, y=y) if x else super().aggregate(sum=Sum(z))['sum'] or 0

    def _clone(self):
        qs = super()._clone()
        qs.request = self.request
        for k, v in self.metadata.items():
            v = self.metadata[k]
            if isinstance(v, list):
                qs.metadata[k] = list(v)
            elif isinstance(v, dict):
                qs.metadata[k] = dict(v)
            else:
                qs.metadata[k] = v
        return qs

    def fields(self, *names):
        if 'fields' not in self.metadata:
            self.metadata['fields'] = ('id',) + names if 'id' not in names else names
        return self
    
    def serializer(self, serializer):
        self.metadata['serializer'] = serializer
        return self

    def search(self, *names):
        if 'search' not in self.metadata:
            self.metadata['search'] = [name if '__' in name else '{}__icontains'.format(name) for name in names]
        return self

    def filters(self, *names):
        if 'filters' not in self.metadata:
            self.metadata['filters'] = names
        return self

    def actions(self, *names):
        if 'actions' not in self.metadata:
            self.metadata['actions'] = []
        self.metadata['actions'].extend(names)
        return self

    def subsets(self, *names):
        if 'subsets' not in self.metadata:
            self.metadata['subsets'] = names
        return self

    def title(self, name=None):
        self.metadata['title'] = name or str(self.model._meta.verbose_name_plural)
        return self
    
    def attrname(self, name):
        self.metadata['attrname'] = name
        return self
    
    def calendar(self, name):
        self.metadata['calendar'] = name
        return self
    
    def limit(self, limit):
        self.metadata['limit'] = limit
        return self
    
    def lookup(self, role_name=None, **lookups):
        if 'lookups' not in self.metadata:
            self.metadata['lookups'] = {}
        self.metadata['lookups'][role_name] = lookups
        return self

    def apply_lookups(self, user):
        from . import permissions
        lookups = self.metadata.get('lookups')
        if lookups:
            return permissions.apply_lookups(self, lookups, user)
        return self

    def contextualize(self, request):
        pk = request and request.GET.get('id')
        choices_field_name = request and request.GET.get('choices')
        self.request = request
        qs = self._clone()
        if pk:
            if self.metadata.get('attrname') is None or request.GET.get('only') == self.attrname:
                qs = qs.filter(pk=pk)
    
        if self.request and 'action' in self.request.GET:
            cls = slth.ENDPOINTS[self.request.GET.get('action')]
            actions = self.metadata.get('actions', ())
            if cls.get_api_name() in actions:
                source = self.model.objects.get(pk=pk) if pk else self
                endpoint = cls.instantiate(self.request, source)
                if endpoint.check_permission():
                    raise JsonResponseException(endpoint.serialize())
                raise Exception()

        filters = qs.metadata.get('filters', ())
        for lookup in filters:
            if lookup.endswith('userrole'):
                from api.models import Role
                rolename = qs.parameter('userrole')
                if rolename:
                    qs = qs.filter(
                        **{'{}__in'.format(lookup[0:-10]):
                        Role.objects.filter(name=rolename).values_list('username', flat=True)}
                    )
            elif request and lookup in request.GET and lookup != choices_field_name:
                qs = qs.apply_filter(lookup, request.GET[lookup])
        search = qs.metadata.get('search', ())
        if request and search and 'q' in request.GET:
            qs = qs.apply_search(request.GET['q'], search)

        if choices_field_name:
            field = qs.model._meta.get_field(choices_field_name)
            choices = field.related_model.objects.filter(pk__in=qs.values_list(choices_field_name, flat=True))
            term = self.request.GET.get('term')
            if term:
                choices = choices.apply_search(term)
            raise JsonResponseException([dict(id=obj.id, value=str(obj)) for obj in choices[0:20]])


        return qs

    def apply_filter(self, lookup, value):
        booleans = dict(true=True, false=False, null=None)
        if len(value) == 10 and '-' in value:
            value = datetime.strptime(value, '%Y-%m-%d');
        if value in booleans:
            value = booleans[value]
        return self.filter(**{lookup: value}) if value != '' else self

    def apply_search(self, term, lookups=None):
        if lookups is None:
            lookups = [f'{field.name}__icontains' for field in self.model._meta.get_fields()
                       if isinstance(field, CharField)] or []
        if lookups:
            terms = term.split(' ') if term else []
            conditions = []
            for term in terms:
                queries = [
                    Q(**{lookup: term})
                    for lookup in lookups
                ]
                conditions.append(reduce(operator.or_, queries))

            return self.filter(reduce(operator.and_, conditions)) if conditions else self
        return self
    
    def parameter(self, name, default=None):
        return self.request.GET.get(name, default) if self.request else default
    
    def serialize(self, debug=False, forward_exception=False):
        try:
            return self.to_dict(debug=debug)
        except JsonResponseException as e:
            if debug:
                print(json.dumps(e.data, indent=2, ensure_ascii=False))
            return e.data
    
    def to_dict(self, debug=False):
        title = self.metadata.get('title', str(self.model._meta.verbose_name_plural))
        title = title.title() if title and title.islower() else title
        attrname = self.metadata.get('attrname')
        subset = None
        actions = []
        filters = []
        search = []
        subsets = []
        aggregations = []
        template = None
        calendar = None

        instance_actions = []
        queryset_actions = []

        base_url = absolute_url(self.request, 'only={}'.format(attrname) if attrname else '')

        for qualified_name in self.metadata.get('actions', ()):
            cls = slth.ENDPOINTS[qualified_name]
            if cls.has_args():
                instance_actions.append(cls)
            else:
                queryset_actions.append(cls)

        for cls in queryset_actions:
            if cls.instantiate(self.request, self).check_permission():
                action = cls.get_api_metadata(self.request, base_url)
                action['name'] = action['name'].replace(" {}".format(self.model._meta.verbose_name.title()), "")
                actions.append(action)

        subset = self.parameter('subset')
        subset = None if subset == 'all' else subset
        page = int(self.parameter('page', 1))
        page_size = min(int(self.parameter('page_size', self.metadata.get('limit', 20))), 1000)
        qs = self.filter()
        qs = qs.order_by('id') if not qs.ordered else qs
        if 'calendar' in self.metadata:
            qs, calendar = self.to_calendar(self.metadata['calendar'])
        if subset:
            qs = getattr(qs, self.subset)()
        
        if subset and 'subsets' in self.metadata:
            subset_metadata = self.metadata['subsets'][subset]
            if subset_metadata:
                self.metadata = {k: v for k, v in self.metadata.items()}
                if subset_metadata['actions']:
                    self.metadata['actions'] = subset_metadata['actions']
                if subset_metadata.get('requires'):
                    self.metadata['requires'] = subset_metadata['requires']
                if len(subset_metadata['filters']) > 1:
                    self.metadata['filters'] = subset_metadata['filters']
        template = self.metadata.get('template')

        for name in self.metadata.get('search', ()):
            search.append(name)

        for lookup in self.metadata.get('filters', ()):
            if lookup.endswith('userrole'):
                field = self.role_filter_field()
            else:
                field = self.filter_field(lookup)
            if field:
                filters.append(field)

        for name in self.metadata.get('subsets', ()):
            subsets.append(dict(name=name, label=name, count=getattr(self, name)().count()))

        for name in self.metadata.get('aggregations', ()):
            api_name = name[4:] if name.startswith('get_') else name
            aggregation = dict(name=api_name, label=api_name, value=getattr(self, name)())
            if isinstance(aggregation['value'], Decimal):
                aggregation['value'] = str(aggregation['value']).replace('.', ',')
            aggregations.append(aggregation)

        objs = []
        total = self.count()
        pages = (total // page_size) + (total % page_size)
        start = page_size * (page - 1)
        end = start + page_size
        serializer:Serializer = qs.metadata.get('serializer')
        previous = None if page ==1 else page -1
        next = None if page == pages else page + 1
        count = qs[start:end].count()
        for obj in qs[start:end]:
            if serializer:
                serializer.obj = obj
                serializer.request = self.request
                serializer.title = str(obj)
            else:
                fields = qs.metadata.get('fields', [field.name for field in (qs.model._meta.fields + qs.model._meta.many_to_many)])
                serializer = Serializer(obj, self.request).fields(*fields)
            serialized = serializer.serialize(forward_exception=True)
            for cls in instance_actions:
                if cls.instantiate(self.request, obj).check_permission():
                    action = cls.get_api_metadata(self.request, base_url, obj.pk)
                    action['name'] = action['name'].replace(" {}".format(self.model._meta.verbose_name.title()), "")
                    serialized['actions'].append(action)
            objs.append(serialized)

        data = dict(type='queryset', title=title, key=attrname, url=base_url, total=total, count=count, icon=None, actions=actions, filters=filters, search=search)
        if attrname:
            data.update(attrname=attrname)
        if calendar:
            data.update(calendar=calendar)
            data['filters'].extend([
                {'name': '{}__day'.format(calendar['field']), 'type': 'hidden', 'value': calendar['day']},
                {'name': '{}__month'.format(calendar['field']), 'type': 'hidden', 'value': calendar['month']},
                {'name': '{}__year'.format(calendar['field']), 'type': 'hidden', 'value': calendar['year']}
            ])
        if subsets:
            data.update(subsets=subsets, subset=subset)
        if aggregations:
            data.update(aggregations=aggregations)
        if template:
            data.update(html=render_to_string(template, data))
        data.update(data=objs, page=page, start=start+1, end=end, previous=previous, next=next, pages=pages, page_size=page_size, page_sizes=[1, 2, 3, 5, 10, 15, 20, 25, 50, 100])
        if debug:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    
    def role_filter_field(self):
        value = self.parameter('userrole')
        choices = [{'id': '', 'text': ''}]
        choices.extend({'id': k, 'text': v} for k, v in ['adm', 'Administrador'])
        return dict(name='userrole', type='choice', value=value, label='Papel', required=False, mask=None, choices=choices)

    def filter_field(self, lookups):
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
        field = self.model.get_field('__'.join(tmp)) if tmp else None
        if field:
            if isinstance(field, models.CharField):
                field_type = 'text'
                value = self.parameter(name)
            elif isinstance(field, models.BooleanField):
                field_type = 'choice'
                value = self.parameter(name)
                if value:
                    value = value == 'true'
                choices = [dict(id='', value=''), dict(id='true', value='Sim'), dict(id='false', value='Não'), dict(id='null', value='Nulo')]
            elif isinstance(field, models.DateField):
                field_type = 'text' if suffix in ('year', 'month') else 'date'
                value = self.parameter(name)
            elif isinstance(field, models.ForeignKey):
                field_type = 'choice'
                value = self.parameter(name)
                if value:
                    value = dict(id=value, label=self.parameter(f'{name}__autocomplete'))
                choices = absolute_url(self.request, f'choices={name}')
            elif isinstance(field, models.ManyToManyField):
                field_type = 'choice'
                choices = absolute_url(self.request, f'choices={name}')
            if getattr(field, 'choices'):
                field_type = 'choice'
                choices = [{'id': '', 'value':''}]
                choices.extend([{'id': k, 'value': v} for k, v in field.choices])
                choices.append({'id': 'null', 'value':'Nulo'})
            data = dict(name=name, type=field_type, value=value, label=str(field.verbose_name), required=False, mask=None)
            if choices:
                data.update(choices=choices)
            return data
        return None

    def to_calendar(self, attr_name):
        today = date.today()
        day = self.parameter(f'{attr_name}__day')
        month = self.parameter(f'{attr_name}__month')
        year = self.parameter(f'{attr_name}__year')
        if month and year:
            start = date(int(year), int(month), 1)
        else:
            start = self.filter(**{f'{attr_name}__month': today.month}).values_list(attr_name, flat=True).first()
            if start is None:
                start = self.order_by(attr_name).values_list(attr_name, flat=True).first() or today
            month = start.month
            year = start.year
        current = date(start.year, start.month, 1)
        qs = self.filter(**{f'{attr_name}__year': start.year, f'{attr_name}__month': start.month})
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