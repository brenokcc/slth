import json
from typing import Any
import datetime
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django.forms.models import ModelChoiceIterator, ModelMultipleChoiceField
from django.forms import fields
from django.db.models import Model, QuerySet, Manager
from django.utils.text import slugify
from django.db import transaction
from django.db.models import Manager
from .exceptions import JsonResponseException
from .utils import absolute_url, build_url, append_url
from .serializer import Serializer
from slth import ENDPOINTS
from .components import Scheduler


DjangoModelForm = ModelForm
DjangoForm = Form
DjangoModelChoiceField = ModelChoiceField
DjangoMultipleChoiceField = MultipleChoiceField
DjangoModelMultipleChoiceField = ModelMultipleChoiceField
DjangoFileField = FileField
DjangoImageField = ImageField

MASKS = dict(
    cpf="999.999.999-99",
    cnpj="99.999.999/9999-99",
    telefone="(99) 99999-9999",
    cep='99.999-990',
    cpf_cnpj="999.999.999-99|99.999.999/9999-99",
)


class FormController:

    def __init__(self, form: Form | ModelForm):
        super().__init__()
        self.form = form
        self.controls = dict(hide=[], show=[], reload=[], set={})

    def hide(self, *names):
        self.controls["hide"].extend(names)

    def show(self, *names):
        self.controls["show"].extend(names)

    def visible(self, visible, *names):
        self.show(*names) if visible else self.hide(*names)

    def reload(self, *names):
        self.controls["reload"].extend(names)

    def set(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, Model):
                v = dict(id=v.id, value=str(v))
            elif isinstance(v, QuerySet) or isinstance(v, Manager):
                v = [dict(id=v.id, value=str(v)) for v in v]
            elif isinstance(v, bool):
                v = str(v).lower()
            elif isinstance(v, datetime.datetime):
                v = v.strftime("%Y-%m-%d %H:%M")
            elif isinstance(v, datetime.date):
                v = v.strftime("%Y-%m-%d")
            self.controls["set"][k] = v

    def get(self, field_name, *field_names, default=None):
        value = self.field_value(field_name, self.form.request.GET.get(field_name, default))
        if field_names:
            values = [value]
            for field_name in field_names:
                values.append(self.field_value(field_name, self.form.request.GET.get(field_name, default)))
            return values
        else:
            return value

    def field_value(self, name, value, default=None):
        if value is None:
            return default
        else:
            try:
                value = self.form.fields[name].to_python(value)
            except KeyError:
                pass
            except ValidationError:
                pass
            return default if value is None else value

    def clear(self):
        self.controls["show"].clear()
        self.controls["hide"].clear()
        self.controls["set"].clear()

    def on_field_change(self, field_name):
        self.clear()
        value = self.get(field_name)
        getattr(self.form._endpoint, f"on_{field_name}_change")(value)
        return self.controls

    def get_field_queryset(self, field_name, queryset):
        method_attr = None
        method_name = f"get_{field_name}_queryset"
        if hasattr(self.form._endpoint, method_name):
            method_attr = getattr(self.form._endpoint, method_name)
        elif hasattr(self.form, "instance") and hasattr(
            self.form.instance, method_name
        ):
            method_attr = getattr(self.form.instance, method_name)
        queryset = method_attr(queryset) if method_attr else queryset
        return queryset.apply_lookups(self.form.request.user)

    def values(self):
        data = dict(**self.controls["set"])
        for name in self.form.fields:
            value = self.get(name)
            if value:
                data[name] = value
        return data


class FormMixin:

    def fieldset(self, title, fields):
        self.fieldsets[title] = fields
        return self

    def parse_json(self):
        content_type = self.request.META.get("CONTENT_TYPE")
        method = self.request.method.lower()
        if content_type and content_type.lower() in "application/json":
            if method == "get" or method == "post":
                d1 = json.loads(self.request.body.decode()) if self.request.body else {}
                d2 = self.request.GET if method == "get" else self.request.POST
                d2._mutable = True
                d2.clear()
                for k, v in d1.items():
                    if isinstance(v, list):
                        for i, item in enumerate(v):
                            prefix = f"{k}__{i}"
                            d2[f"{prefix}__id"] = item.get("id")
                            for k1, v1 in item.items():
                                d2[f"{prefix}__{k1}"] = v1
                    elif isinstance(v, dict):
                        prefix = k
                        d2[f"{prefix}__id"] = v.get("id")
                        for k1, v1 in v.items():
                            d2[f"{prefix}__{k1}"] = v1
                    else:
                        d2[k] = v
                d2._mutable = False

    @classmethod
    def get_metadata(cls, name, default=None):
        metaclass = getattr(cls, "Meta", None)
        return getattr(metaclass, name, default) if metaclass else default

    def serialize(self):
        return self.to_dict()

    def display(self, serializable):
        self._display = serializable
        return self

    def to_dict(self, prefix=None):
        field_name = self.request.GET.get("on_change")
        if field_name:
            raise JsonResponseException(self.controller.on_field_change(field_name))
        data = dict(
            type="form",
            key=self._key,
            method=self._method,
            title=self.get_metadata("title", self._title),
            icon=self.get_metadata("icon"),
            style=self.get_metadata("style"),
            url=absolute_url(self.request),
            info=self._info,
            image=self._image,
            autosubmit=self._autosubmit,
            submit_label=self._submit_label,
            submit_icon=self._submit_icon,
        )
        data.update(
            controls=self.controller.controls, width=self.get_metadata("width", "100%")
        )
        if self._display:
            if isinstance(self._display, Serializer):
                self._display.request.GET._mutable = True
                self._display.request.GET.pop('only', None)
                self._display.request.GET._mutable = False
                data.update(
                    display=self._display.serialize(forward_exception=True)["data"]
                )
        choices_field_name = self.request.GET.get("choices")
        if self.fieldsets:
            fieldsetlist = []
            for title, names in self.fieldsets.items():
                fields = []
                if prefix:
                    value = self.instance.pk if isinstance(self, ModelForm) else ""
                    fields.append(
                        [
                            dict(
                                type="hidden",
                                name=f"{prefix}__id",
                                value=value,
                                label="ID",
                            )
                        ]
                    )
                for name in names:
                    if isinstance(name, str):
                        field = self.serialize_field(
                            name, self.fields[name], prefix, choices_field_name
                        )
                        fields.append([field])
                    else:
                        fields.append(
                            [
                                self.serialize_field(
                                    name, self.fields[name], prefix, choices_field_name
                                )
                                for name in name
                            ]
                        )
                if (
                    len(fields) == 1
                    and isinstance(fields[0], list)
                    and fields[0][0]["type"] == "inline"
                ):
                    fieldsetlist.append(fields[0][0])
                else:
                    fieldsetlist.append(
                        dict(type="fieldset", title=title, name=slugify(title), fields=fields)
                    )
            data.update(fieldsets=fieldsetlist)
        else:
            fields = []
            if prefix:
                value = self.instance.pk if isinstance(self, ModelForm) else ""
                fields.append(
                    dict(type="hidden", name=f"{prefix}__id", value=value, label="ID")
                )
            for name, field in self.fields.items():
                fields.append(
                    self.serialize_field(name, field, prefix, choices_field_name)
                )
            data.update(fields=fields)
        return data

    def serialize_field(self, name, field, prefix, choices_field_name):
        if isinstance(field, InlineFormField) or isinstance(field, InlineModelField):
            value = []
            instances = []
            is_one_to_one = field.max == field.min == 1
            if isinstance(self, ModelForm):
                if isinstance(field, OneToOneField):
                    instances.append(
                        getattr(self.instance, name) if self.instance.id else None
                    )
                elif isinstance(field, OneToManyField):
                    instances.extend(
                        getattr(self.instance, name).all() if self.instance.id else ()
                    )
            for i, instance in enumerate(instances):
                prefix = name if is_one_to_one else f"{name}__{i}"
                kwargs = (
                    dict(instance=instance, endpoint=self._endpoint)
                    if isinstance(field, InlineModelField)
                    else dict(endpoint=self._endpoint)
                )
                value.append(field.form(**kwargs).to_dict(prefix=prefix))
            if not is_one_to_one:
                value.append(
                    field.form(endpoint=self._endpoint).to_dict(prefix=f"{name}__n")
                )
            required = getattr(field, "required2", field.required)
            label = field.label.title() if field.label and field.label.islower() else field.label
            data = dict(
                type="inline",
                min=field.min,
                max=field.max,
                name=name,
                count=len(instances),
                label=str(label),
                required=required,
                value=value,
            )
        else:
            extra = {}
            ftype = FIELD_TYPES.get(type(field).__name__, "text")
            if name in self._values:
                ftype = "hidden"
                value = self._values[name]
                value = value.pk if isinstance(value, Model) else value
            else:
                value = None
                if self.instance is None or self.instance.id is None:
                    value = field.initial or self.initial.get(name)
                else:
                    value = self.initial.get(name)
                if callable(value):
                    value = value()

                if isinstance(field, ModelMultipleChoiceField) or isinstance(
                    field, DjangoModelMultipleChoiceField
                ):
                    value = (
                        [dict(id=obj.id, label=str(obj).strip()) for obj in value]
                        if value
                        else []
                    )
                elif isinstance(field, MultipleChoiceField) or isinstance(
                    field, DjangoMultipleChoiceField
                ):
                    value = value if value else []
                elif value and (
                    isinstance(field, ModelChoiceField)
                    or isinstance(field, DjangoModelChoiceField)
                ):
                    obj = field.queryset.get(pk=value) if isinstance(value, int) else value
                    value = dict(id=obj.id, label=str(obj).strip())
                elif isinstance(field, DjangoImageField):
                    value = build_url(self.request, value.url) if value else None
                    extra.update(
                        extensions=field.extensions,
                        width=field.width,
                        height=field.height,
                    )
                elif isinstance(field, DjangoFileField):
                    value = build_url(self.request, value.url) if value else None
                    extra.update(extensions=field.extensions, max_size=field.max_size)

            if isinstance(field.widget, HiddenInput):
                ftype = "hidden"
                value = value["id"] if isinstance(value, dict) else value

            fname = name if prefix is None else f"{prefix}__{name}"
            data = dict(
                type=ftype,
                name=fname,
                label=str(field.label) if field.label else None,
                required=field.required,
                value=value,
                help_text=str(field.help_text),
                mask=None,
            )
            data.update(**extra)
            for word in MASKS:
                if word in name:
                    data.update(mask=MASKS[word])
            for word in ("password", "senha"):
                if word in name:
                    data.update(type="password")
            pick = getattr(field, "pick", False)
            if isinstance(field, fields.CharField) or isinstance(field, fields.IntegerField):
                mask = getattr(field, "mask", None)
                if mask:
                    data.update(mask=mask)
            if isinstance(field.widget, Textarea):
                data.update(type="textarea")
            if ftype == "decimal":
                data.update(mask="decimal")
            elif ftype == "scheduler":
                data.update(scheduler=field.scheduler)
            elif ftype == "choice" or pick:
                choiceurl = self._endpoint.base_url if self._endpoint else None
                if name in self.request.GET and not choices_field_name:
                    data.update(type="hidden", value=self.request.GET[name])
                else:
                    if choices_field_name == fname or (isinstance(field.choices, ModelChoiceIterator) and not pick):
                        if choices_field_name == fname:
                            qs = field.choices.queryset
                            qs = self.controller.get_field_queryset(fname, qs)
                            if "term" in self.request.GET:
                                qs = qs.apply_search(self.request.GET["term"])
                            raise JsonResponseException(
                                [dict(id=obj.id, value=str(obj).strip()) for obj in qs[0:(50 if pick else 25)]]
                            )
                        else:
                            data["choices"] = append_url(choiceurl, f"choices={fname}") if choiceurl else  absolute_url(
                                self.request, f"choices={fname}"
                            )
                    else:
                        if isinstance(field.choices, ModelChoiceIterator):
                            data["choices"] = [
                                dict(id=obj.id, value=str(obj).strip())
                                for obj in self.controller.get_field_queryset(fname, field.choices.queryset)
                            ]
                        else:
                            data["choices"] = [
                                dict(id=str(k), value=v) for k, v in field.choices
                            ]
                    if pick:
                        data.update(pick=append_url(choiceurl, f"choices={fname}") if choiceurl else  absolute_url(
                            self.request, f"choices={fname}"
                        ))
            if ftype == "boolean":
                data.update(choices=[
                    {"id": "true", "value": "Sim"}, {"id": "false", "value": "Não"}, {"id": "null", "value": "Não Informado"}
                ])

        attr_name = f"on_{prefix}__{name}_change" if prefix else f"on_{name}_change"
        on_change_name = f"{prefix}__{name}" if prefix else name
        if hasattr(self._endpoint, attr_name):
            data["onchange"] = absolute_url(self.request, f"on_change={on_change_name}")
        if name in self._actions:
            cls = ENDPOINTS[self._actions[name]]
            endpoint = cls.instantiate(self.request, self)
            if endpoint.check_permission():
                action=endpoint.get_api_metadata(self.request, absolute_url(self.request))
                action['name'] = action['name'].replace(field.label, "").strip()
                data.update(action=action)
        return data

    def submit(self):
        data = {}
        errors = {}
        inline_fields = {
            name: field
            for name, field in self.fields.items()
            if isinstance(field, InlineFormField) or isinstance(field, InlineModelField)
        }
        self.is_valid()
        errors.update(self.errors)
        inline_forms = []
        for inline_field_name, inline_field in inline_fields.items():
            data[inline_field_name] = []
            for i in range(0, inline_field.max):
                is_one_to_one = inline_field.max == inline_field.min == 1
                prefix = (
                    inline_field_name if is_one_to_one else f"{inline_field_name}__{i}"
                )
                inline_form_field_name = f"{prefix}__id"
                if inline_form_field_name in self.data:
                    inline_form_data = {}
                    inline_form_field_value = self.data.get(inline_form_field_name)
                    if inline_form_field_value or is_one_to_one:
                        pk = int(inline_form_field_value or 0)
                        for name in inline_field.form.base_fields:
                            inline_form_field = inline_field.form.base_fields[name]
                            inline_form_field_name = f"{prefix}__{name}"
                            inline_form_data[name] = self.data.getlist(
                                inline_form_field_name
                            ) if (
                                (
                                    isinstance(inline_form_field, DjangoMultipleChoiceField)
                                    or isinstance(inline_form_field, ModelMultipleChoiceField)
                                )
                                and not isinstance(inline_form_field, TypedChoiceField)
                                ) else self.data.get(
                                inline_form_field_name
                            )
                            if (
                                self.request.FILES
                                and inline_form_field_name in self.request.FILES
                            ):
                                self.request.FILES._mutable = True
                                self.request.FILES[name] = self.request.FILES[
                                    inline_form_field_name
                                ]
                                self.request.FILES._mutable = False
                        instance = (
                            inline_field.form._meta.model.objects.get(pk=abs(pk))
                            if pk
                            else None
                        )
                        if pk < 0:
                            setattr(instance, "deleting", True)
                        inline_form = inline_field.form(
                            data=inline_form_data,
                            instance=instance,
                            endpoint=self._endpoint,
                        )
                        if is_one_to_one and not inline_field.required and not inline_form_field_value:
                            data[inline_field_name] = []
                        else:
                            if inline_form.is_valid():
                                if isinstance(inline_form, DjangoModelForm):
                                    data[inline_field_name].append(inline_form.instance)
                                else:
                                    data[inline_field_name].append(inline_form.cleaned_data)
                                inline_forms.append(inline_form)
                            else:
                                errors.update(
                                    {
                                        f"{prefix}__{name}": error
                                        for name, error in inline_form.errors.items()
                                    }
                                )
        if errors:
            raise JsonResponseException(
                dict(type="error", text="Por favor, corrija os erros.", errors=errors)
            )
        else:
            self.cleaned_data.update(**data)
            data.update(
                {
                    field_name: self.cleaned_data.get(field_name)
                    for field_name in self.fields
                    if field_name not in inline_fields
                }
            )
            for attr_name in dir(self._endpoint):
                if attr_name.startswith('clean_'):
                    try:
                        getattr(self._endpoint, attr_name)(data)
                    except ValidationError as e:
                        fieldname = attr_name.replace('clean_', '')
                        raise JsonResponseException(dict(type="error", text="Por favor, corrija os erros.", errors={fieldname: ''.join(e.messages)}))
            with transaction.atomic():
                for inline_form in inline_forms:
                    inline_form.save()
                if isinstance(self, DjangoModelForm):
                    self.instance.pre_save()
                    for inline_field_name in inline_fields:
                        for obj in self.cleaned_data[inline_field_name]:
                            obj.save()
                            # set one-to-one
                            if hasattr(self.instance, f"{inline_field_name}_id"):
                                if hasattr(obj, "deleting"):
                                    setattr(self.instance, inline_field_name, None)
                                else:
                                    setattr(self.instance, inline_field_name, obj)
                    self.save()
                    for inline_field_name in inline_fields:
                        for obj in self.cleaned_data[inline_field_name]:
                            if hasattr(obj, "deleting"):
                                obj.delete()
                    self.instance.post_save()
                return self.cleaned_data

    def settitle(self, title):
        self._title = title
        return self

    def values(self, **kwargs):
        self._values.update(**kwargs)
        return self

    def actions(self, **kwargs):
        self._actions.update(kwargs)
        return self


class Form(DjangoForm, FormMixin):

    def __init__(self, *args, endpoint=None, **kwargs):
        self._display = []
        self._endpoint = endpoint
        self._info = None
        self._image = None
        self._message = None
        self._redirect = None
        self._dispose = False
        self._values = {}
        self._title = type(self).__name__
        self._actions = {}
        self._method = "POST"
        self._key = self._title.lower()
        self._autosubmit = None
        self._submit_label = "Enviar"
        self._submit_icon = "chevron-right"

        self.fieldsets = {}
        self.fields = {}
        self.request = endpoint.request
        self.controller = FormController(self)
        self.instance = kwargs.pop("instance", None)
        self.parse_json()
        if "data" not in kwargs:
            if self.request.method.upper() == "GET":
                data = self.request.GET or None
            elif self.request.method.upper() == "POST":
                data = self.request.POST or {}
        else:
            data = kwargs["data"]
        kwargs.update(data=data)
        if self.request:
            kwargs.update(files=self.request.FILES or None)
        super().__init__(*args, **kwargs)


class ModelForm(DjangoModelForm, FormMixin):

    def __init__(self, instance=None, endpoint=None, **kwargs):
        self._display = []
        self._endpoint = endpoint
        self._info = None
        self._image = None
        self._message = None
        self._redirect = None
        self._dispose = False
        self._values = {}
        self._title = type(self).__name__
        self._actions = {}
        self._method = "POST"
        self._key = self._title.lower()
        self._autosubmit = None
        self._submit_label = "Enviar"
        self._submit_icon = "chevron-right"

        self.fieldsets = {}
        self.request = endpoint.request
        self.controller = FormController(self)

        self.parse_json()
        if "data" not in kwargs:
            if self.request.method.upper() == "GET":
                data = self.request.GET or None
            elif self.request.method.upper() == "POST":
                data = self.request.POST or {}
            else:
                data = None
        else:
            data = kwargs["data"]
        kwargs.update(data=data)
        if self.request:
            kwargs.update(files=self.request.FILES or None)
        super().__init__(instance=instance, **kwargs)

    def is_valid(self):
        valid = super().is_valid()
        return valid

class InlineFormField(Field):
    def __init__(self, *args, form=None, min=1, max=3, **kwargs):
        self.form = form
        self.max = max
        self.min = min
        super().__init__(*args, **kwargs)
        self.required = False


class InlineModelField(Field):
    def __init__(
        self, model, *args, fields="__all__", exclude=(), min=1, max=3, **kwargs
    ):
        if fields == "__all__":
            self.form = modelform_factory(
                model, form=ModelForm, fields=fields, exclude=exclude
            )
        else:
            field_names = []
            for field_name in fields:
                if isinstance(field_name, str):
                    field_names.append(field_names)
                else:
                    field_names.extend(field_name)
            self.form = modelform_factory(
                model, form=ModelForm, fields=field_names, exclude=exclude
            )
            self.form.fieldsets = {None: fields}
        self.max = max
        self.min = min
        super().__init__(*args, **kwargs)
        self.required = False


class OneToManyField(InlineModelField):
    def __init__(self, model, fields="__all__", exclude=(), min=1, max=3, **kwargs):
        super().__init__(model, fields=fields, exclude=exclude, min=min, max=max)


class OneToOneField(InlineModelField):
    def __init__(self, model, fields="__all__", exclude=(), **kwargs):
        super().__init__(model, fields=fields, exclude=exclude, min=1, max=1)


class DecimalField(DecimalField):
    def to_python(self, value):
        if isinstance(value, str) and "," in value:
            value = value.replace(".", "").replace(",", ".")
        return super().to_python(value)


class ColorField(CharField):
    pass


class FileField(FileField):
    def __init__(self, *args, extensions=("pdf",), max_size=5, **kwargs):
        self.extensions = extensions
        self.max_size = max_size
        super().__init__(*args, **kwargs)


class ImageField(ImageField):
    def __init__(
        self,
        *args,
        extensions=("png", "jpg", "jpeg"),
        width=None,
        height=None,
        **kwargs,
    ):
        self.extensions = extensions
        if width or height:
            self.width = width or height
            self.height = height or width
        else:
            self.width = self.height = 500
        super().__init__(*args, **kwargs)


class CharField(CharField):

    def __init__(self, *args, **kwargs):
        self.mask = kwargs.pop("mask", None)
        super().__init__(*args, **kwargs)


class ChoiceField(ChoiceField):

    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop("pick", False)
        super().__init__(*args, **kwargs)


class MultipleChoiceField(MultipleChoiceField):

    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop("pick", False)
        super().__init__(*args, **kwargs)


class ModelChoiceField(ModelChoiceField):

    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop("pick", False)
        super().__init__(*args, **kwargs)


class ModelMultipleChoiceField(ModelMultipleChoiceField):

    def __init__(self, *args, **kwargs):
        self.pick = kwargs.pop("pick", False)
        super().__init__(*args, **kwargs)


class SchedulerField(CharField):
    def __init__(self, *args, scheduler=None, **kwargs):
        self.scheduler = scheduler or Scheduler()
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        values = dict(select=[], deselect=[])
        if value:
            data = json.loads(value)
            for key in values.keys():
                for date, hour in data[key]:
                    data_string = "{} {}".format(date, hour)
                    values[key].append(datetime.datetime.strptime(data_string, "%d/%m/%Y %H:%M"))
        if self.scheduler["single_selection"]:
            return values['select'][0] if values['select'] else None
        else:
            return values
    
    def clean(self, value):
        value = self.to_python(value)
        if self.scheduler["single_selection"]:
            if self.required and value is None:
                raise ValidationError('Este campo é obrigatório.')
        return value


FIELD_TYPES = {
    "CharField": "text",
    "EmailField": "email",
    "DecimalField": "decimal",
    "BooleanField": "boolean",
    "NullBooleanField": "boolean",
    "DateTimeField": "datetime",
    "DateField": "date",
    "IntegerField": "number",
    "ChoiceField": "choice",
    "TypedChoiceField": "choice",
    "ModelChoiceField": "choice",
    "MultipleChoiceField": "choice",
    "ModelMultipleChoiceField": "choice",
    "ColorField": "color",
    "FileField": "file",
    "ImageField": "file",
    "SchedulerField": "scheduler",
}
