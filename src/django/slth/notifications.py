import json
from pywebpush import webpush
from slth import APPLICATON

def send_push_web_notification(user, title, message, url=None, icon=None):
    icon = icon or APPLICATON['icon']
    for subscription in user.pushsubscription_set.all():
        data = webpush(
            subscription_info=subscription.data,
            data=json.dumps(dict(title=title, message=message, url=url, icon=icon)),
            vapid_private_key="GoFJpuTAdhepzfxOHdrW7u2ONh7V8ZIjPkjgpWSS3ks",
            vapid_claims={"sub": "mailto:admin@admin.com"}
        )
        print(data)
