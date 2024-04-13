from pywebpush import webpush

def send_push_web_notification(user, text):
    for subscription in user.pushsubscription_set.all():
        data = webpush(
            subscription_info=subscription.data,
            data=text,
            vapid_private_key="GoFJpuTAdhepzfxOHdrW7u2ONh7V8ZIjPkjgpWSS3ks",
            vapid_claims={"sub": "mailto:admin@admin.com"}
        )
        print(data)
