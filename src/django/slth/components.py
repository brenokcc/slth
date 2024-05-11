from datetime import date, timedelta, datetime
from django.template.loader import render_to_string


SUCCESS = "success"
PRIMARY = "primary"
WARNING = "warning"
DANGER = "danger"


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
    def __init__(self, color, label):
        self["type"] = "badge"
        self["color"] = color
        self["label"] = str(label)


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
    def __init__(self, title):
        self["type"] = "boxes"
        self["title"] = str(title)
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


class TemplateContent(dict):
    def __init__(self, name, context):
        self["type"] = "html"
        self["content"] = render_to_string(name, context)


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


class Navbar(dict):
    def __init__(self, title, subtitle=None, logo=None, user=None):
        self["type"] = "navbar"
        self["title"] = title
        self["subtitle"] = subtitle
        self["logo"] = logo
        self["user"] = user
        self["usermenu"] = []
        self["adder"] = []
        self["tools"] = []
        self["settings"] = []
        self["actions"] = []

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
    def __init__(self, icon=None, navbar=None, menu=None, footer=None, oauth=()):
        self["type"] = "application"
        self["icon"] = icon
        self["navbar"] = navbar
        self["menu"] = menu
        self["footer"] = footer
        self["oauth"] = oauth


class Response(dict):

    def __init__(self, message=None, redirect=None, store=None):
        self["type"] = "response"
        self["message"] = message
        self["redirect"] = redirect
        self["store"] = store or {}


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
    INTERVALS = {1: ["00"], 2: ["00", "30"]}

    def __init__(
        self,
        start_time=7,
        end_time=20,
        chucks=2,
        start_day=None,
        days=7,
        initial=(),
        single_selection=False,
        input_name="schedule",
        readonly=False,
    ):
        self["type"] = "scheduler"
        self["single_selection"] = single_selection
        self["input_name"] = input_name
        self["readonly"] = readonly
        start_day = start_day or date.today()
        self.times = []
        for hour in range(start_time, end_time + 1):
            for minute in Scheduler.INTERVALS[chucks]:
                self.times.append("{}:{}".format(str(hour).rjust(2, "0"), minute))
        self.days = []
        for n in range(0, days):
            self.days.append(start_day.strftime("%d/%m/%Y"))
            start_day = start_day + timedelta(days=1)
        self["slots"] = {}
        for day in self.days:
            self["slots"][day] = {k: None for k in self.times}
        for obj in initial:
            if isinstance(obj, datetime):
                day = obj.strftime("%d/%m/%Y")
                time = obj.strftime("%H:%M")
                value = ""
            else:
                if len(obj) == 3:
                    day, time, value = obj
                else:
                    date_time, value = obj
                    day = date_time.strftime("%d/%m/%Y")
                    time = date_time.strftime("%H:%M")
            self["slots"][day][time] = value

        self["matrix"] = [[""] + self.days]
        for time in self.times:
            row = [time]
            for day in self.days:
                row.append(self["slots"][day][time])
            self["matrix"].append(row)
