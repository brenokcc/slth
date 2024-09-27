import requests
from django.http import HttpResponse
from django.template.loader import render_to_string
from . import Endpoint
from ..exceptions import ReadyResponseException


class ReportEndpoint(Endpoint):

    def process(self):
        data = super().process()
        template = '{}.html'.format(self.__class__.__name__.lower())
        html = render_to_string(template, data)
        headers = {'Content-type': 'text/html'}
        response = requests.post('http://weasyprint.aplicativo.click/pdf', headers=headers, data=html)
        raise ReadyResponseException(HttpResponse(response.content, content_type='application/pdf'))
