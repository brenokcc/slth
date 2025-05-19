from datetime import date, timedelta, datetime
from django.template.loader import render_to_string
from . import geo

SUCCESS = "success"
PRIMARY = "primary"
WARNING = "warning"
DANGER = "danger"

class Text(dict):
    def __init__(self, text, color="inherite", size="inherite", bold=False, italic=False):
        self["type"] = "text"
        self["text"] = text
        self["color"] = color
        self["bold"] = bold
        self["italic"] = italic

class Image(dict):
    def __init__(self, src, width=None, height=None, round=False, placeholder=None):
        if width is None and height is None:
            width = 100
            height = 100
        if width and not height:
            height = width
        if height and not width:
            width = height
        self["type"] = "image"
        self["src"] = src
        self["width"] = width
        self["height"] = height
        self["round"] = round
        self["placeholder"] = placeholder


class FileLink(dict):
    def __init__(self, url, modal=False, icon=None):
        self["type"] = "filelink"
        self["url"] = url
        self["modal"] = modal
        self["icon"] = icon


class FileViewer(dict):
    def __init__(self, url):
        self["type"] = "filepreview"
        self["url"] = url


class QrCode(dict):
    def __init__(self, text):
        self["type"] = "qrcode"
        self["text"] = text


class Progress(dict):
    def __init__(self, value, style="primary"):
        self["type"] = "progress"
        self["value"] = int(value or 0)
        self["style"] = style


class Status(dict):
    def __init__(self, style, label):
        self["type"] = "status"
        self["style"] = style
        self["label"] = str(label)


class Badge(dict):
    def __init__(self, color, label, icon=None):
        self["type"] = "badge"
        self["color"] = color
        self["label"] = str(label)
        self["icon"] = icon


class Shell(dict):
    def __init__(self, output):
        self["type"] = "shell"
        self["output"] = output


class Indicators(dict):
    def __init__(self, title):
        self["type"] = "indicators"
        self["title"] = title
        self["items"] = []
        self["actions"] = []

    def append(self, name, value):
        self["items"].append(dict(name=str(name), value=value))

    def action(self, label, url, modal=False):
        self["actions"].append(dict(label=str(label), url=url, modal=modal))


class Boxes(dict):
    def __init__(self, title=None):
        self["type"] = "boxes"
        self["title"] = str(title) if title else None
        self["items"] = []

    def append(self, icon, label, url, style=None):
        self["items"].append(dict(icon=icon, label=str(label), url=url, style=style))


class Info(dict):
    def __init__(self, title, message):
        self["type"] = "info"
        self["title"] = title
        self["message"] = message
        self["actions"] = []

    def action(self, label, url, modal=False, icon=None):
        self["actions"].append(dict(label=str(label), url=url, modal=modal, icon=icon))


class Warning(dict):
    def __init__(self, title, message):
        self["type"] = "warning"
        self["title"] = title
        self["message"] = message
        self["actions"] = []

    def action(self, label, url, modal=False, icon=None):
        self["actions"].append(dict(label=str(label), url=url, modal=modal, icon=icon))


class Table(dict):
    def __init__(self, title, subset=None, pagination=None):
        self["type"] = "table"
        self["title"] = title
        self["actions"] = []
        self["subsets"] = []
        self["subset"] = subset
        self["filters"] = []
        self["flags"] = []
        self["rows"] = []
        self["pagination"] = {}

    def add_subset(self, name, label, count):
        self["subsets"].append(dict(name=name, label=label, count=count))

    def add_action(self, name, label, icon=None, batch=True):
        self["actions"].append(dict(name=name, label=label, icon=icon, batch=batch))

    def add_flag(self, name, label, checked=False):
        self["flags"].append(dict(name=name, label=label, checked=checked))

    def add_filter(self, ftype, name, label, value, choices=None):
        self["filters"].append(
            dict(type=ftype, name=name, label=label, value=value, choices=choices)
        )

    def pagination(self, size, page, total, sizes):
        self["pagination"].update(size=size, page=page, total=total, sizes=sizes)

    def add_row(self, row):
        self["rows"].append(row)

    def row(self, value=None, checkable=False, deleted=False):
        self["rows"].append(
            [dict(name="#", value=value, checkable=checkable, deleted=deleted)]
        )

    def cell(self, name, value, style=None, url=None, actions=None):
        self["rows"][-1].append(
            dict(name=name, value=value, style=style, url=url, actions=actions)
        )


class HtmlContent(dict):
    def __init__(self, content, autoreload=None):
        self["type"] = "html"
        self["content"] = content
        self["autoreload"] = autoreload * 1000 if autoreload else None


class TemplateContent(dict):
    def __init__(self, name, context, autoreload=None):
        self["type"] = "html"
        self["content"] = render_to_string(name, context)
        self["autoreload"] = autoreload * 1000 if autoreload else None


class GeoMap(dict):
    
    def __init__(self, lat=0, lon=0, zoom=10, min_zoom=None, max_zoom=None, title=None):
        self["type"] = "geomap"
        self["title"] = title
        self["lat"] = lat
        self["long"] = lon
        self["zoom"] = zoom
        self["min_zoom"] = min_zoom or zoom
        self["max_zoom"] = max_zoom or zoom
        self["polygons"] = []
        self["points"] = []

    def to_html(self, info):
        if isinstance(info, dict):
            info = "<br>".join([f"<b>{k}</b>: {v}" for k, v in info.items()])
        elif info:
            info = str(info).replace("\n", "<br>")
        return info

    def add_polygon(self, coordinates, info="", color="#0b2353"):
        feature = { "type": "Feature", "properties": { "info": self.to_html(info) }, "geometry": { "type": "Polygon", "coordinates": coordinates} }
        return self.add_polygon_feature(feature, color=color)

    def add_polygon_feature(self, feature, color="#0b2353"):
        style = dict(weight=2, color="white", opacity=1, fillColor=color, fillOpacity=0.8)
        feature['properties']['style'] = style
        self["polygons"].append(feature)
        return feature

    def add_point(self, lat, lon, info="", label="", color="red"):
        feature = {"geometry": {"type": "Point", "coordinates": [lat, lon]}, "type": "Feature", "properties": {"info": self.to_html(info), "label": str(label), "color": color}}
        return self.add_point_feature(feature, color=color)

    def add_point_feature(self, feature, color="red"):
        style = dict(radius=5, fillColor=color, color=color, weight=1, opacity=1, fillOpacity=0.8)
        feature['properties']['style'] = style
        self["points"].append(feature)
        return feature
    

class BrGeoMap(GeoMap):
    
    def __init__(self, color='#0b2353', show_info=True):
        self.show_info = show_info
        super().__init__(-50.6178, -12.5, zoom=4, max_zoom=7)
        self.data = {
            'AC': {'lat': -9.9754, 'lon': -67.8243},
            'AL': {'lat': -9.6658, 'lon': -35.735},
            'AP': {'lat': 0.0349, 'lon': -51.0694},
            'AM': {'lat': -3.119, 'lon': -60.0217},
            'BA': {'lat': -12.9714, 'lon': -38.5014},
            'CE': {'lat': -3.7172, 'lon': -38.5433},
            'DF': {'lat': -15.7939, 'lon': -47.8828},
            'ES': {'lat': -20.3155, 'lon': -40.3128},
            'GO': {'lat': -16.6864, 'lon': -49.2643},
            'MA': {'lat': -2.5307, 'lon': -44.3068},
            'MT': {'lat': -15.601, 'lon': -56.0974},
            'MS': {'lat': -20.4697, 'lon': -54.6201},
            'MG': {'lat': -19.9167, 'lon': -43.9345},
            'PA': {'lat': -1.455, 'lon': -48.5022},
            'PB': {'lat': -7.1153, 'lon': -34.861},
            'PR': {'lat': -25.4284, 'lon': -49.2733},
            'PE': {'lat': -8.0476, 'lon': -34.877},
            'PI': {'lat': -5.0919, 'lon': -42.8034},
            'RJ': {'lat': -22.9068, 'lon': -43.1729},
            'RN': {'lat': -5.7945, 'lon': -35.211},
            'RS': {'lat': -30.0346, 'lon': -51.2177},
            'RO': {'lat': -8.7612, 'lon': -63.9004},
            'RR': {'lat': 2.8238, 'lon': -60.6753},
            'SC': {'lat': -27.5954, 'lon': -48.548},
            'SP': {'lat': -23.5505, 'lon': -46.6333},
            'SE': {'lat': -10.9472, 'lon': -37.0731},
            'TO': {'lat': -10.2491, 'lon': -48.3243},
        }

        features = geo.brazil_states().get('features')
        for feature in features:
            feature["properties"]["info"] = feature["properties"]["name"] if self.show_info else None
            self.add_polygon_feature(feature, color=color)

    def add_data(self, state, label="", info="", color="red"):
        lat = self.data[state]["lat"]
        lon = self.data[state]["lon"]
        label = f"<b>{state}</b>: {label}" if label != "" else label
        self.add_point(lon, lat, info=info, label=label, color=color)

class BrRegionGeoMap(GeoMap):
    
    def __init__(self, color='#0b2353', show_info=True):
        self.show_info = show_info
        super().__init__(-50.6178, -12.5, zoom=4, max_zoom=7)
        self.data = {
            'Norte': {'lon': -58.5921662263205, 'lat': -3.5078467396601667},
            'Nordeste': {'lon': -41.64106903888117, 'lat': -7.60494867268045},
            'Centro-Oeste': {'lon': -54.41021386798654, 'lat': -14.676752818694368},
            'Sul': {'lon': -51.72844646026684, 'lat': -25.845669451210867},
            'Sudeste': {'lon': -45.40620191141343, 'lat': -19.14188754461283},
        }
        features = geo.brazil_regions().get('features')
        for feature in features:
            feature["properties"]["info"] = feature["properties"]["NOME1"] if self.show_info else None
            self.add_polygon_feature(feature, color=color)

    def add_data(self, region, label="", info="", color="red"):
        lat = self.data[region]["lat"]
        lon = self.data[region]["lon"]
        label = f"<b>{region}</b>: {label}" if label != "" else label
        self.add_point(lon, lat, info=info, label=label, color=color)

class Banner(dict):
    def __init__(self, src):
        self["type"] = "banner"
        self["src"] = src


class Map(dict):
    def __init__(self, latitude, longitude, width="100%", height=400):
        self["type"] = "map"
        self["latitude"] = str(latitude)
        self["longitude"] = str(longitude)
        self["width"] = width
        self["height"] = height


class Steps(dict):
    def __init__(self, icon=None):
        self["type"] = "steps"
        self["icon"] = icon
        self["steps"] = []

    def append(self, name, done):
        number = len(self["steps"]) + 1
        self["steps"].append(dict(number=number, name=name, done=bool(done)))


class WebConf(dict):
    def __init__(self, caller, receiver):
        self["type"] = "webconf"
        self["caller"] = caller
        self["receiver"] = receiver


class ZoomMeet(dict):
    def __init__(self, token, username):
        self["type"] = "zoommeet"
        self["token"] = token
        self["username"] = username


class Navbar(dict):
    def __init__(self, title, subtitle=None, logo=None, user=None, photo=None, search=False, roles=None):
        self["type"] = "navbar"
        self["title"] = title
        self["subtitle"] = subtitle
        self["logo"] = logo
        self["user"] = user
        self["photo"] = photo
        self["usermenu"] = []
        self["adder"] = []
        self["tools"] = []
        self["settings"] = []
        self["actions"] = []
        self["toolbar"] = []
        self["search"] = search
        self["roles"] = roles

    def add_action(self, entrypoint, name, url, modal=True, icon=None):
        self[entrypoint].append(dict(name=name, url=url, modal=modal, icon=icon))


class Menu(dict):
    def __init__(self, items, user=None, image=None):
        self["type"] = "menu"
        self["items"] = items
        self["user"] = user
        self["image"] = image


class Footer(dict):
    def __init__(self, version):
        self["type"] = "navbar"
        self["version"] = version


class Application(dict):
    def __init__(self, icon=None, navbar=None, menu=None, footer=None, oauth=(), sponsors=()):
        self["type"] = "application"
        self["icon"] = icon
        self["navbar"] = navbar
        self["menu"] = menu
        self["footer"] = footer
        self["oauth"] = oauth
        self["sponsors"] = sponsors


class Response(dict):

    def __init__(self, message=None, redirect=None, store=None, **kwargs):
        self["type"] = "response"
        self["message"] = message
        self["redirect"] = redirect or '..'
        self["store"] = store or {}
        self.update(**kwargs)


class IconSet(dict):
    def __init__(self):
        self["type"] = "iconset"


class Grid(dict):
    def __init__(self):
        self["type"] = "grid"
        self["items"] = []

    def append(self, component):
        self["items"].append(component)


class Scheduler(dict):
    INTERVALS = {1: ["00"], 2: ["00", "30"], 3: ["00", "20", "40"]}

    def __init__(
        self,
        start_time=0,
        end_time=23,
        chucks=2,
        start_day=None,
        days=7,
        single_selection=False,
        input_name="schedule",
        readonly=False,
        title=None,
        watch=[],
        url=None,
        selectable=None,
        weekly=False
    ):
        self["type"] = "scheduler"
        self["title"] = title
        self["single_selection"] = single_selection
        self["input_name"] = input_name
        self["readonly"] = readonly
        self["watch"] = watch
        self["url"] = url
        self["selectable"] = ['{} {}'.format(obj.strftime("%d/%m/%Y"), obj.strftime("%H:%M")) for obj in selectable] if selectable is not None else None
        self["weekly"] = weekly
        if weekly:
            self.end_day = datetime.now()
            while self.end_day.weekday() > 0:
                self.end_day = self.end_day - timedelta(days=1)
            days = 7
        else:
            self.end_day = start_day or datetime.now()
            self.end_day = datetime(self.end_day.year, self.end_day.month, self.end_day.day)
        self.times = []
        for hour in range(start_time, end_time + 1):
            for minute in Scheduler.INTERVALS[chucks]:
                self.times.append("{}:{}".format(str(hour).rjust(2, "0"), minute))
        self.days = []
        for n in range(0, days):
            if n == 0:
                self.start_day = self.end_day
            self.days.append(self.end_day.strftime("%d/%m/%Y"))
            self.end_day = self.end_day + timedelta(days=1)
        self.end_day = datetime(self.end_day.year, self.end_day.month, self.end_day.day, 23, 59, 59)
        self["slots"] = {}
        for day in self.days:
            self["slots"][day] = {k: None for k in self.times}

        self["matrix"] = []
        row = [dict(text='', icon=None, color=None)]
        for day in self.days:
            row.append(dict(text=day, icon=None, color=None))
        self["matrix"].append(row)
        for time in self.times:
            row = [dict(text=time, icon=None, color=None)]
            for day in self.days:
                row.append(self["slots"][day][time])
            self["matrix"].append(row)

    def append(self, date_time, text=None, icon='check'):
        if date_time.strftime("%d/%m/%Y") in self.days:
            day = date_time.strftime("%d/%m/%Y")
            time = date_time.strftime("%H:%M")
            value = dict(text=text, icon=icon)
            self["slots"][day][time] = value
            j = self.days.index(day) + 1 if day in self.days else -1
            x = self.times.index(time) + 1 if time in self.times else -1
            self["matrix"][x][j] = value

    def append_weekday(self, weekday, hour, minute):
        date_time = self.start_day
        while date_time < self.end_day + timedelta(days=-1):
            if date_time.weekday() == int(weekday):
                self.append(datetime(date_time.year, date_time.month, date_time.day, hour, minute, 0))
            date_time += timedelta(days=1)
    