# pip install --upgrade fpdf2
from fpdf import FPDF, FontFace
import hashlib
import base64
import os
import re
import slthlib
from datetime import datetime
import tempfile
from PIL import Image, ImageDraw, ImageFont
from django.template.loader import render_to_string
from django.conf import settings

SIGNATURE_URL = 'https://assinatura-api.staging.iti.br/externo/v2/assinarPKCS7'
SIGNATURE_SIZE = 18944
BYTERANGE='[                                  ]'

STYLE = {
    'h1': FontFace(color="#000000", size_pt=28, family='Helvetica'),
    'h2': FontFace(color="#000000", size_pt=24, family='Helvetica'),
}

class PdfWriter:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.add_page()

    def render(self, template_name, context):
        context.update(base_url=settings.SITE_URL)
        html = render_to_string(template_name, context)
        self.write(html)

    def write(self, html):
        self.pdf.write_html(html, tag_styles=STYLE, font_family="Courier")

    def save(self, path):
        self.pdf.output(path)


class PdfSigner:
    def __init__(self, path, signer):
        self.path = path
        self.signer = signer
        self.xref = None
        self.data = []
        with open(path, 'rb') as fp:
            self.content = fp.read()# + b'\r\n'
        self.offset = len(self.content)
        self.byterange = []
        self.path = path.split('.')[0]
        self.startxref = [int(x[9:].strip()) for x in re.findall(b'startxref[\n\r ]*\\d+', self.content)]
        self.objects = {}
        for xref in re.findall(b'xref[\n\r\\w\\d ]*trailer', self.content[self.startxref[0]:]):
            for offset in sum([[int(n) for n in re.findall(b'\\d{10}', xref) if int(n)]], []):
                self.objects[b' '.join(self.content[offset:offset + 15].split()[0:2]).decode()] = offset
        self.trailer = self.content[self.startxref[-1]:].split(b'trailer')[1].split(b'startxref')[0].strip()
        self.root = root = re.findall(b'/Root \\d+ \\d+ R', self.trailer)[-1][6:-2].decode()
        self.size = int(re.findall(b'/Size \\d+', self.trailer)[-1][5:].strip())
        self.page()

    def obj(self, key=None):
        key = key or self.root
        return self.content[self.objects[key]: self.objects[key] + self.content[self.objects[key]:].index(b'endobj') + 6].replace(b'\r', b'') + b'\n'

    def next(self, i):
        return max([int(k.split()[0]) for k in self.objects]) + i

    def add(self, data):
        offset = str(self.offset).rjust(10, '0')
        self.offset += len(data)
        self.data.append(data)
        if self.xref is None:
            self.xref = ['xref', '0 1', '0000000000 65535 f\r']
        self.xref.append('{} 1'.format(data.split()[0]))
        self.xref.append('{} 00000 n\r'.format(offset))

    def page(self):
        for key, offset in self.objects.items():
            content = self.content[offset:offset + 500]
            if b'/Page' in content and b'/Pages' not in content:
                return key
        raise BaseException('No page was found in the PDF')

    def finalize(self):
        xrefstart = str(self.offset)
        data = '\n'.join(self.xref)
        data += '\ntrailer\n<<\n/Size {}\n/Root {} R\n/Prev {}\n>>\n'.format(
            (self.size + len(self.xref) - 5), self.root, self.startxref[-1]
        )
        data += 'startxref\n'
        data += xrefstart
        data += '\n%%EOF'
        self.offset += len(data)
        self.data.append(data)

    def hash(self, n=0):
        w, h = 900, 200
        left = n * 200
        signer = self.signer.split(':')[0]
        stamp_file_path = self.stamp(signer)
        print(stamp_file_path)
        self.add(self.obj().decode().replace('>>', '/AcroForm <<\n/Fields [{} 0 R]\n/SigFlags 3\n>>\n>>'.format(self.next(1))))
        self.add(self.obj(self.page()).decode().replace('/Page', '/Page /Annots [{} 0 R]'.format(self.next(1))))
        a = "{} 0 obj\n<<\n/FT /Sig\n/Type /Annot\n/Subtype /Widget\n/F 132\n/T (Signature1)\n/V {} 0 R\n/P {} R\n/Rect [{} 0 {} {}]\n/AP {} 0 R\n>>\nendobj\n".format(
            self.next(1), self.next(2), self.page(), w/10*2+left, left, h/10*2, self.next(3))
        b = "{} 0 obj\n<<\n/Type /Sig\n/Filter /Adobe.PPKLite\n/SubFilter /adbe.pkcs7.detached\n/M ({})\n/Contents <{}>\n/ByteRange {}\n/Name ({})\n>>\nendobj\n".format(
            self.next(2), datetime.now().strftime("D:%Y%m%d%H%M%S+00'00'"), '0' * SIGNATURE_SIZE, BYTERANGE, signer)
        c = "{} 0 obj\n<<\n/N {} 0 R\n>>\nendobj\n".format(self.next(3), self.next(4))
        stream = 'q\n{} 0 0 {} 0 0 cm\n/Img1 Do\nQ'.format(w, h)
        d = "{} 0 obj\n<</Type/XObject/Subtype/Form/Resources<</XObject<</Img1 {} 0 R>>>>/BBox[0 0 {} {}]/Length {}>>\nstream\n{}\nendstream\nendobj\n".format(self.next(4), self.next(5), w, h, len(stream), stream)
        x = base64.a85encode(open(stamp_file_path, 'rb').read()).decode()
        e = "{} 0 obj\n<<\n/BitsPerComponent 8 /ColorSpace /DeviceRGB /Filter [ /ASCII85Decode /DCTDecode ] /Length {} /Subtype /Image /Type /XObject /Width {} /Height {} /Resources<<    >> >>\nstream\n{}\nendstream\nendobj\n".format(self.next(5), len(x), w, h, x)
        self.add(a)
        i = self.offset + b.index('/Contents') + 10
        j = i + SIGNATURE_SIZE + 2
        self.add(b)
        self.add(c)
        self.add(d)
        self.add(e)
        self.finalize()
        self.byterange = [0, i, j, self.length() - j]
        self.data[3] = self.data[3].replace(
            BYTERANGE, '[{} {} {} {}]'.format(*self.byterange).ljust(len(BYTERANGE), ' ')
        )
        for data in self.data:
            self.content += data.encode()
        i, j, x, y = self.byterange
        content = self.content[i:i+j] + self.content[x:x+y]
        hash = base64.b64encode(hashlib.sha256(content).digest()).decode()
        return hash

    def length(self):
        i = len(self.content)
        for data in self.data:
            i += len(data)
        return i

    def signed(self, name):
        return '/Name ({})'.format(name).encode() in self.content

    def stamp(self, name):
        w, h = 900, 200
        bgcolor = '#FFFFFF'
        date = datetime.now()
        img = Image.new('RGB', (w, h), (255, 255, 255))
        img1 = ImageDraw.Draw(img)
        img1.rectangle([(3, 3), (w - 3, h - 3)], fill=bgcolor, outline=bgcolor)
        fontdir = os.path.join(os.path.dirname(slthlib.__file__), 'static', 'fonts')
        font = ImageFont.truetype(os.path.join(fontdir, 'MicrosoftSansSerif.ttf'), 25)
        bold = ImageFont.truetype(os.path.join(fontdir, 'MicrosoftSansSerifBold.ttf'), 25)
        x, y = 380, 10
        img1.text((x, y), 'DOCUMENTO ASSINADO DIGITALMENTE', (0, 0, 0), font=font)
        y += 45
        img1.text((x, y), name, (0, 0, 0), font=bold)
        y += 35
        img1.text((x, y), 'Data/Hora: {}'.format(date.strftime('%d/%m/%Y %H:%M:%S')), (0, 0, 0), font=font)
        y += 35
        img1.text((x, y), 'Verifique em https://verificador.iti.br', (0, 0, 0), font=font)
        y += 35
        tmp = tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False)
        imgdir = os.path.join(os.path.dirname(slthlib.__file__), 'static', 'images')
        logo = Image.open(os.path.join(imgdir, 'icp-brasil.png'))
        img.paste(logo.resize((int(logo.width*0.6), int(logo.height*0.6))), (5, 10))
        img = img.convert("RGB")
        img.save(tmp.name, format='jpeg')
        return tmp.name
    
    def sign(self, path=None):
        signature = self.sign_hash(self.hash())
        path = path or '{}-signed.pdf'.format(self.path)
        with open(path, 'wb') as fp:
            content = self.content
            if signature:
                i, j, x, y = self.byterange
                content = self.content[i:i + j] + b'<' + base64.b64decode(signature).hex().ljust(SIGNATURE_SIZE, '0').encode() + b'>' + self.content[x:x + y]
            fp.write(content)
    
    def sign_hash(self, hash):
        return None


#curl -X POST 'https://verificador.staging.iti.br/report' --header 'Content-Type: multipart/form-data' --form 'report_type="json"' --form 'signature_files[]=@"hello-assinado.pdf"' --form 'detached_files[]=""'
