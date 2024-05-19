import json
from decimal import Decimal
from django.db.models.aggregates import Count, Sum, Avg
from django.core.exceptions import FieldDoesNotExist


MONTHS = 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'
PIE_CHART = 'pie'
POLAR_CHART = 'polar'
DONUT_CHART = 'donut'
BAR_CHART = 'bar'
STACKED_BAR_CHART = 'stacked_bar'
COLUMN_CHART = 'column'
STACKED_COLUMN_CHART = 'stacked_column'
TREE_MAP_CHART = 'tree_map'
LINE_CHART = 'line'
AREA_CHART = 'area'
PROGRESS_CHART = 'progress'


class Statistics(object):

    def __init__(self, qs, title=None, chart=None):
        self.qs = qs
        self.x = None
        self.y = None
        self.func = None
        self.z = 'id'
        self._xfield = None
        self._yfield = None
        self._xdict = {}
        self._ydict = {}
        self._values_dict = None
        self.title = title
        self.chart = chart

    def _calc(self):
        if '__month' in self.x:
            self._xdict = {i + 1: month for i, month in enumerate(MONTHS)}
        if self.y and '__month' in self.y:
            self._ydict = {i + 1: month for i, month in enumerate(MONTHS)}
        if self._values_dict is None:
            self.calc()

    def _xfield_display_value(self, value):
        if hasattr(self._xfield, 'choices') and self._xfield.choices:
            for choice in self._xfield.choices:
                if choice[0] == value:
                    return choice[1]
        return value

    def _yfield_display_value(self, value):
        if hasattr(self._yfield, 'choices') and self._yfield.choices:
            for choice in self._yfield.choices:
                if choice[0] == value:
                    return choice[1]
        return value

    def _clear(self):
        self._xfield = None
        self._yfield = None
        self._xdict = {}
        self._ydict = {}
        self._values_dict = None

    def calc(self):
        self._values_dict = {}
        if self.y:
            values_list = self.qs.values_list(self.x, self.y).order_by(self.x, self.y).annotate(self.func(self.z))
        else:
            values_list = self.qs.values_list(self.x).order_by(self.x).annotate(self.func(self.z))

        self._xfield = self.qs.model.get_field(self.x.replace('__year', '').replace('__month', ''))
        if self._xdict == {}:
            xvalues = self.qs.values_list(self.x, flat=True).order_by(self.x).distinct()
            if self._xfield.related_model:
                if hasattr(self._xfield.related_model, 'cor'):
                    self.colors = {pk: color for pk, color in self._xfield.related_model.objects.values_list('id', 'cor')}
                self._xdict = {
                    obj.pk: str(obj) for obj in self._xfield.related_model.objects.filter(pk__in=xvalues)
                }
            else:
                self._xdict = {
                    value: value for value in self.qs.values_list(self.x, flat=True)
                }
            if None in xvalues:
                self._xdict[None] = 'Não-Informado'
        if self.y:
            self._yfield = self.qs.model.get_field(self.y.replace('__year', '').replace('__month', ''))
            yvalues = self.qs.values_list(self.y, flat=True).order_by(self.y).distinct()
            if self._ydict == {}:
                if self._yfield.related_model:
                    self._ydict = {
                        obj.pk: str(obj) for obj in self._yfield.related_model.objects.filter(pk__in=yvalues)
                    }
                else:
                    self._ydict = {
                        value: value for value in yvalues
                    }
            self._values_dict = {(vx, vy): calc for vx, vy, calc in values_list}
            if None in yvalues:
                self._ydict[None] = 'Não-Informado'
        else:
            self._ydict = {}
            self._values_dict = {(vx, None): calc for vx, calc in values_list}

    def debug(self):
        print(json.dumps(self.serialize(), indent=4, ensure_ascii=False))

    def serialize(self):
        tx = []
        ty = []
        series = dict()
        self._calc()

        formatter = {True: 'Sim', False: 'Não', None: ''}

        def format_value(value):
            return float(value) if isinstance(value, Decimal) else value

        if self._ydict:
            for i, (yk, yv) in enumerate(self._ydict.items()):
                data = []
                for j, (xk, xv) in enumerate(self._xdict.items()):
                    data.append([formatter.get(xv, str(self._xfield_display_value(xv))), format_value(self._values_dict.get((xk, yk), 0)), '#000000'])
                series.update(**{formatter.get(yv, str(self._yfield_display_value(yv))): data})
            ty = []
            for k, serie in series.items():
                sy = 0
                ly = len(serie)
                for i, item in enumerate(serie):
                    sy += item[1]
                ty.append(sy)
            tx = [0 for i in range(0, ly)]
            # breakpoint()
            for i in range(0, len(tx)):
                for kj in series:
                    tx[i] += series[kj][i][1]
            if len(tx) == len(ty) == 1:
                tx = ty = []
            elif len(tx) > 1 and len(ty) > 1:
                ty.append(sum(ty))
                tx.append(sum(tx))
            elif len(ty) > 1:
                if len(ty) > 2: tx.append(sum(tx))
                ty = []
            elif len(tx) > 1:
                if len(tx) > 2: ty.append(sum(ty))
                tx = []
        else:
            sx = 0
            data = list()
            for j, (xk, xv) in enumerate(self._xdict.items()):
                data.append([formatter.get(xv, str(self._xfield_display_value(xv))), format_value(self._values_dict.get((xk, None), 0)), '#000000'])
                sx+=data[-1][1]
            if data:
                series['default'] = data
            tx = [sx]
        return dict(type='statistics', title=self.title, series=series['default'] if 'default' in series else series, chart=self.chart)

    def count(self, x, y=None):
        self.func = Count
        self.x = x
        self.y = y
        self._calc()
        return self.serialize()

    def sum(self, z, x=None, y=None):
        self.func = Sum
        self.x = x
        self.y = y
        self._calc()
        return self.serialize()
