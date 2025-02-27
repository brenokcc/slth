import json
import os
import requests
from pywebpush import webpush
from slth.application import Application as ApplicationConfig


def send_push_web_notification(user, title, message, url=None, icon=None):
    application = ApplicationConfig.get_instance()
    icon = icon or application.icon
    for subscription in user.pushsubscription_set.all():
        print(subscription.user, subscription.device, subscription.data, title, message, url)
        data = webpush(
            subscription_info=subscription.data,
            data=json.dumps(dict(title=title, message=message, url=url, icon=icon)),
            vapid_private_key=os.environ['VAPID_PRIVATE_KEY'],
            vapid_claims={"sub": "mailto:admin@admin.com"}
        )
        print(data)


def send_whatsapp_notification(to, title, messsage, url=None):
    api_url = 'https://whatsapp.aplicativo.click/send'
    headers={"Content-Type": "application/json", "Authorization": "Token undefined"}
    to = to.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    to = '55{}{}@c.us'.format(to[0:2], to[3:])
    data = {"to": to, "message": "*{}*\n{}\n{}".format(title, messsage, url or "")}
    response = requests.post(api_url, headers=headers, json=data)
    response.status_code == 200
