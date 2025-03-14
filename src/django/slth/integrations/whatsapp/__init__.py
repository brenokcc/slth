import requests

def send(to, title, message, url=None):
    headers={"Content-Type": "application/json", "Authorization": "Token undefined"}
    to = to.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    to = '55{}{}@c.us'.format(to[0:2], to[3:])
    data = {"to": to, "message": "*{}*\n{}\n{}".format(title, message, url or "")}
    response = requests.post('https://whatsapp.aplicativo.click/send', headers=headers, json=data)
    response.status_code == 200
