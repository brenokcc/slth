import io
import qrcode
import base64
from datetime import datetime
from weasyprint import HTML
from django.conf import settings
from django.template.loader import render_to_string


class Signature:
    def __init__(self, date, validation_url, verify_code, auth_code):
        self.date = date
        self.validation_url = '{}{}'.format(settings.SITE_URL, validation_url)
        self.verify_code = verify_code
        self.auth_code = auth_code
        self.signers = []
        self.qrcode = qrcode_base64(self.validation_url)

    def add_signer(self, identifier, signature_date):
        self.signers.append((identifier, signature_date))


def qrcode_base64(texto):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered =io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def to_pdf(data, template, file_name=None, signature=None):
    templates = []
    buffer = io.BytesIO()
    templates.append(template)
    if signature:
        data.update(signature=signature)
        templates.append('signature.html')
    pages = []
    for template in templates:
        data.update(page=len(pages)+1)
        html = render_to_string(template, data)
        doc = HTML(string=html).render()
        pages.extend(doc.pages)
    doc = doc.copy(pages=pages) if len(templates) > 1 else doc
    doc.write_pdf(file_name or buffer, base_url=settings.SITE_URL, stylesheets=[])
    buffer.seek(0)
    return buffer

def test():
    data = dict(lines=range(50))
    signature = Signature(date=datetime.now(), validation_url='/', verify_code=123, auth_code=123)
    signature.add_signer('Carlos Silva', datetime.now())
    signature.add_signer('Juca Silva', None)
    to_pdf(data, 'report.html', '/Users/breno/Downloads/a.pdf', signature=signature)