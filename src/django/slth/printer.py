import io
import qrcode
import base64
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string


class Signature:
    def __init__(self, date, validation_url, verify_code=None, auth_code=None):
        self.date = date
        if validation_url.startswith('http'):
            self.validation_url = validation_url
        else:
            self.validation_url = '{}{}'.format(settings.SITE_URL, validation_url)
        self.verify_code = verify_code
        self.auth_code = auth_code
        self.signers = []
        self.qrcode = qrcode_base64(self.validation_url)

    def add_signer(self, identifier, signature_date=None):
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

def image_base64(image_bytes):
    return 'data:image/png;base64, {}'.format(base64.b64encode(image_bytes).decode())


def to_pdf(data, template, file_name=None, signature=None):
    from weasyprint import HTML
    templates = []
    buffer = io.BytesIO()
    templates.append(template)
    if data: data.update(base_url=settings.SITE_URL)
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

def test2():
    data = dict(lines=range(50))
    signature = Signature(date=datetime.now(), validation_url='https://validar.iti.gov.br/')
    signature.add_signer('Carlos Silva (075.803.982-90)', None)
    signature.add_signer('Juca Silva (075.803.982-90)', None)
    to_pdf(data, 'report.html', '/Users/breno/Downloads/a.pdf', signature=signature)
