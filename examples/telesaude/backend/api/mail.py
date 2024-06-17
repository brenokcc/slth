import os
import requests

def send_mail(to, subject, text, html=None):
    print('Sending e-mail to {}...'.format(to))
    url = 'https://api.mailersend.com/v1/email'
    headers = {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Authorization': 'Bearer {}'.format(os.environ.get('MAILERSEND_API_TOKEN'))}
    data = {'from': {'email': 'no-replay@trial-3yxj6ljvpqqldo2r.mlsender.net'}, 'to': [{'email': email} for email in to], 'subject': subject, 'text': text, 'html': html or text}
    response = requests.post(url, headers=headers, json=data)
    print(response.text)
