import os
import requests
import base64


def ocr(uri):
        if uri.startswith('http'):
            image = {"source": {"image_uri": uri}}
        else:
            with open(uri, 'rb') as file:
                image = {"content": base64.b64encode(file.read()).decode()}
        url = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(os.environ['GOOGLE_TOKEN'])
        data = {"requests": [{"image": image, "features": {"type": "TEXT_DETECTION"}}]}
        response = requests.post(url, json=data).json()
        for item in response['responses']:
            if item and 'fullTextAnnotation' in item:
                return item['fullTextAnnotation']['text']
        return None
