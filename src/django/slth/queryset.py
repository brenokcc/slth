import slth
import pickle
import base64
import zlib
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
import tempfile
import xlsxwriter
from django.http import FileResponse
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.template.loader import render_to_string
from django.db import models
from .serializer import Serializer
from .exceptions import JsonResponseException, ReadyResponseException
from .utils import absolute_url, append_url, build_url


class QuerySet(models.QuerySet):

    def __init__(self, *args, **kwargs):
        self.metadata = {}
        self.instance = None
        self.request = None
        self.base_url = None
        super().__init__(*args, **kwargs)

    def total(self, x=None):
        return self.values_list(x).order_by(x).distinct().count() if x else self.count()

    def counter(self, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).count(x=x, y=y) if x else super().count()

    def sum(self, z, x=None, y=None, title=None, chart=None):
        return Statistics(self, title=title, chart=chart).sum(z, x=x, y=y) if x else super().aggregate(sum=Sum(z))['sum'] or 0

    def _clone(self):
        qs = super()._clone()
        qs.instance = self.instance
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
        self.metadata['fields'] = ('id',) + names if 'id' not in names else names
        if [name for name in names if not isinstance(name, str)]:
            return self.rows()
        return self
    
    def serializer(self, serializer):
        self.metadata['serializer'] = serializer
        return self

    def search(self, *names):
        if 'search' not in self.metadata:
            self.metadata['search'] = [name if '__' in name else '{}__icontains'.format(name) for name in names]
        return self

    def filters(self, *names, **kwargs):
        self.metadata['filters'] = names
        self.metadata['custom_filters'] = kwargs
        return self

    def actions(self, *names, **replacement):
        if 'actions' not in self.metadata:
            self.metadata['actions'] = []
        for k in names:
            if k not in self.metadata['actions']:
                self.metadata['actions'].append(k)
        for k, v in replacement.items():
            if k in self.metadata['actions']:
                self.metadata['actions'].remove(k)
            self.metadata['actions'].append(v)
        return self

    def subsets(self, *names):
        self.metadata['subsets'] = names
        return self
    
    def style(self, name):
        self.metadata['style'] = name
        return self
    
    def renderer(self, name):
        self.metadata['renderer'] = name
        return self
    
    def info(self, text):
        self.metadata['info'] = text
        return self
    
    def timeline(self):
        return self.renderer('timeline')
    
    def accordion(self):
        return self.renderer('accordion')
    
    def cards(self):
        return self.renderer('cards')
    
    def rows(self):
        return self.renderer('rows')
    
    def bi(self, *names, **dependency):
        self.metadata['bi'] = dict(fields=[], dependency=dependency)
        for name in names:
            self.metadata['bi']['fields'].append((name,) if isinstance(name, str) else name)
        return self

    def settitle(self, name=None):
        self.metadata['title'] = name or str(self.model._meta.verbose_name_plural)
        return self
    
    def attrname(self, name):
        self.metadata['attrname'] = name
        return self
    
    def reloadable(self):
        self.metadata['reloadable'] = True
        return self
    
    def calendar(self, name):
        self.metadata['calendar'] = name
        return self
    
    def ignore(self, *names):
        self.metadata['ignore'] = names
        return self
    
    def xlsx(self, *names):
        self.metadata['xlsx'] = names
        return self
    
    def limit(self, limit, *limits):
        self.metadata['limit'] = limit
        self.metadata['page_sizes'] = (limit,) + limits
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

        filters = qs.metadata.get('filters', ())
        for lookup in filters:
            if request and lookup in request.GET and lookup != choices_field_name:
                qs = qs.apply_filter(lookup, request.GET[lookup])
        custom_filters = qs.metadata.get('custom_filters', {})
        for lookup in custom_filters:
            if request and lookup in request.GET and lookup != choices_field_name:
                qs = custom_filters[lookup].filter(qs, request.GET[lookup])
        search = qs.metadata.get('search', ())
        if request and search and 'q' in request.GET:
            qs = qs.apply_search(request.GET['q'], search)

        if choices_field_name:
            term = self.request.GET.get('term')
            if choices_field_name in custom_filters:
                choices = custom_filters[choices_field_name].choices(self, term)
            else:
                field = qs.model.get_field(choices_field_name)
                choices = field.related_model.objects.filter(pk__in=qs.values_list(choices_field_name, flat=True))
                if term:
                    choices = choices.apply_search(term)
            raise JsonResponseException([dict(id=obj.id, value=str(obj).strip()) for obj in choices[0:20]])

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
            search_fields = getattr(self.model._meta, 'search_fields', None)
            if search_fields is None:
                search_fields = [field.name for field in self.model._meta.get_fields() if isinstance(field, CharField)]
            lookups = [f'{name}__icontains' for name in search_fields]
        else:
            lookups = [name if name.endswith('__icontains') else f'{name}__icontains' for name in lookups]
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
        ignore = self.metadata.get('ignore', ())
        renderer = self.metadata.get('renderer')
        info = self.metadata.get('info')
        reloadable = self.metadata.get('reloadable')
        style = self.metadata.get('style')
        xlsx = self.metadata.get('xlsx')
        bi = self.metadata.get('bi', [])
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

        if self.request and self.request.GET.get('xlsx'):
            file = tempfile.NamedTemporaryFile(suffix='.xlsx', mode='w+b', delete=False)
            workbook = xlsxwriter.Workbook(file)
            worksheet = workbook.add_worksheet('A')
            header = []
            rows = []
            serializer = Serializer(None, self.request).fields(*self.metadata['xlsx'])
            for i, obj in enumerate(self):
                row = []
                serializer.obj = obj
                serialized = serializer.serialize(forward_exception=True)
                for item in serialized['data']:
                    if i == 0:
                        header.append(item['label'])
                    if item.get('type') == 'field':
                        row.append(item['value'])
                if i == 0:
                    rows.append(header)
                rows.append(row)
            for row_idx, row_data in enumerate(rows):
                for col_idx, col in enumerate(row_data):
                    worksheet.write(row_idx, col_idx, col)
            workbook.close()
            file.close()
            raise ReadyResponseException(FileResponse(open(file.name, 'rb')))
    
        if self.request and 'action' in self.request.GET:
            cls = slth.ENDPOINTS[self.request.GET.get('action')]
            actions = self.metadata.get('actions', ())
            if cls.get_key_name() in actions:
                source = self._hints.get('instance')
                if source is None:
                    pk = self.request.GET.get('id')
                    source = self.model.objects.get(pk=pk) if pk else qs
                endpoint = cls.instantiate(self.request, source)
                if endpoint.check_permission():
                    raise JsonResponseException(endpoint.serialize())
                raise Exception()

        base_url = append_url(build_url(self.request, self.base_url), 'only={}'.format(attrname) if attrname else '')
        if self.request.GET.urlencode():
            base_url = append_url(base_url, self.request.GET.urlencode())

        for qualified_name in self.metadata.get('actions', ()):
            cls = slth.ENDPOINTS[qualified_name]
            if cls.has_args():
                instance_actions.append(cls)
            else:
                queryset_actions.append(cls)

        for cls in queryset_actions:
            endpoint = cls.instantiate(self.request, self)
            if endpoint.check_permission():
                action = endpoint.get_api_metadata(self.request, base_url)
                actions.append(action)

        subset = self.parameter('subset')
        qs = self.filter()
        qs = qs.order_by('id') if not qs.ordered else qs
        if subset:
            qs = getattr(qs, subset)()
        if 'calendar' in qs.metadata:
            qs, calendar = qs.to_calendar(qs.metadata['calendar'])
        template = self.metadata.get('template')

        for name in qs.metadata.get('search', ()):
            search.append(name)

        for lookup in qs.metadata.get('filters', ()):
            field = self.filter_field(lookup, base_url)
            if field and lookup not in ignore:
                filters.append(field)
        for filtername, filter in qs.metadata.get('custom_filters', {}).items():
            field = self.custom_filter_field(filtername, filter, base_url)
            if field:
                filters.append(field)
        
        total = qs.count()
        for name in self.metadata.get('subsets', ()):
            attr = getattr(self, name)
            label = getattr(attr, 'verbose_name', name.title())
            subsets.append(dict(name=name, label=label, count=attr().count()))
        if subsets:
            subsets.insert(0, dict(name=None, label='Tudo', count=total))

        for name in self.metadata.get('aggregations', ()):
            api_name = name[4:] if name.startswith('get_') else name
            aggregation = dict(name=api_name, label=api_name, value=getattr(self, name)())
            if isinstance(aggregation['value'], Decimal):
                aggregation['value'] = str(aggregation['value']).replace('.', ',')
            aggregations.append(aggregation)

        data = dict(type='queryset', title=title, key=attrname, url=base_url, total=total, count=total, icon=None, actions=actions, filters=filters, search=search, q=self.request.GET.get('q'))
        if info:
            data.update(info=info)
        if renderer:
            data.update(renderer=renderer)
        if reloadable:
            data.update(reloadable=reloadable)
        if bi:
            bi_data = []
            for names in bi['fields']:
                items = []
                for name in names:
                    depends_on = bi['dependency'].get(name)
                    if depends_on is None or self.parameter(depends_on):
                        attr = getattr(qs, name)
                        title = getattr(attr, 'verbose_name', name.title())
                        value = attr()
                        if isinstance(value, dict):
                            item = value
                            item['title'] = title
                        else:
                            item = dict(type='counter', title=title, value=value)
                        items.append(item)
                if items:
                    bi_data.append(items)
            data.update(bi=bi_data)
        else:
            objs = []
            page_size = min(int(self.parameter('page_size', self.metadata.get('limit', 20))), 1000)
            page_sizes = self.metadata.get('page_sizes', [page_size])
            pages = (total // page_size) + (1 if total % page_size else 0)
            page = min(int(self.parameter('page', 1)), pages) or 1
            start = page_size * (page - 1)
            end = start + page_size
            previous = None if page ==1 else page -1
            next = None if page == pages else page + 1
            count = qs[start:end].count()
            title_func_name = '__str__'
            serializer:Serializer = qs.metadata.get('serializer')
            if serializer is None:
                fields = qs.metadata.get('fields', [field.name for field in (qs.model._meta.fields + qs.model._meta.many_to_many) if field.name not in ignore])
                list_fields = [
                    f'get_{field_name}' if hasattr(qs.model, f'get_{field_name}') else
                    (f'get_{field_name}_display' if hasattr(qs.model, f'get_{field_name}_display')
                    else field_name) for field_name in fields
                ]
                serializer = Serializer(None, self.request).fields(*list_fields)
            serializer.request = self.request
            
            for obj in qs[start:end]:
                serializer.title = getattr(obj, title_func_name)()
                serializer.obj = obj
                serialized = serializer.serialize(forward_exception=True)
                for cls in instance_actions:
                    endpoint = cls.instantiate(self.request, obj)
                    if endpoint.check_permission():
                        action = endpoint.get_api_metadata(self.request, base_url, obj.pk)
                        action['name'] = action['name'].replace(" {}".format(self.model._meta.verbose_name), "")
                        serialized['actions'].append(action)
                if style:
                    serialized['style'] = getattr(obj, style)()
                objs.append(serialized)

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
            pagination = dict(
                start=start+1, end=min(end, total), page=dict(
                    total=pages, previous=previous, current=page, next=next,
                    size=page_size, sizes=page_sizes
                )
            )
            data.update(count=count, data=objs, pagination=pagination)
            if xlsx:
                data.update(xlsx=xlsx)
        if debug:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    
    def custom_filter_field(self, name, filter, base_url):
        options = filter.choices(self)
        value = self.parameter(name)
        if isinstance(options, list) or isinstance(options, tuple):
            field_type = 'choice'
            choices = [{'id': '', 'value':''}]
            choices.extend([{'id': k, 'value': v} for k, v in options])
            choices.append({'id': 'null', 'value':'Nulo'})
        else:
            field_type = 'choice'
            choices = append_url(base_url, f'choices={name}')
        return dict(name=name, type=field_type, value=value, label=filter.get_label(), required=False, mask=None, choices=choices)

    def filter_field(self, lookups, base_url):
        name = lookups.strip()
        suffix = None
        choices = None
        field = None
        value = None
        ignore = 'icontains', 'contains', 'gt', 'gte', 'lt', 'lte', 'id', 'year', 'month'
        symbols = dict(gt=' >', gte=' ⋝', lt=' <', lte=' ⋜')
        tmp = []
        for lookup in name.split('__'):
            if lookup in ignore:
                suffix = lookup
            else:
                tmp.append(lookup)
        field = self.model.get_field('__'.join(tmp)) if tmp else None
        if field:
            label = None
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
                if suffix == 'year':
                    field_type = 'choice'
                    label = "Ano"
                    choices = [{'id': '', 'value':''}]
                    choices.extend([{'id': year, 'value': year} for year in self.model.objects.order_by(name).values_list(name, flat=True).distinct()])
            elif isinstance(field, models.ForeignKey):
                field_type = 'choice'
                value = self.parameter(name)
                if value:
                    value = dict(id=value, label=self.parameter(f'{name}__autocomplete'))
                choices = append_url(base_url, f'choices={name}')
            elif isinstance(field, models.ManyToManyField):
                field_type = 'choice'
                choices = append_url(base_url, f'choices={name}')
            if getattr(field, 'choices'):
                field_type = 'choice'
                choices = [{'id': '', 'value':''}]
                choices.extend([{'id': k, 'value': v} for k, v in field.choices])
                choices.append({'id': 'null', 'value':'Nulo'})
            label = label or str(field.verbose_name).title()
            symbol = symbols.get(suffix) if suffix else None
            label = label + symbol if symbol else label
            data = dict(name=name, type=field_type, value=value, label=label, required=False, mask=None)
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
    
    def dump(self):
        query = base64.b64encode(zlib.compress(pickle.dumps(self.query))).decode()
        return {'model': self.model._meta.label.lower(), 'query': query}
    
    @classmethod
    def load(cls, data):
        model = apps.get_model(data['model'])
        query = pickle.loads(zlib.decompress(base64.b64decode(data['query'].encode())))
        queryset = model.objects.none()
        queryset.query = query
        return queryset
