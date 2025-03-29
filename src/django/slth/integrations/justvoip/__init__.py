import os
import requests

JUSTVOIP_USERNAME = os.environ.get('JUSTVOIP_USERNAME')
JUSTVOIP_PASSWORD = os.environ.get('JUSTVOIP_PASSWORD')
JUSTVOIP_FROM = os.environ.get('JUSTVOIP_FROM')


def send(to, message):
    to = '55{}'.format(to).replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    url = 'https://www.justvoip.com/myaccount/sendsms.php?username={}&password={}&from={}&to={}&text={}'.format(
        JUSTVOIP_USERNAME, JUSTVOIP_PASSWORD, JUSTVOIP_FROM, to, message
    )
    response = requests.get(url)
    print(response.text)
