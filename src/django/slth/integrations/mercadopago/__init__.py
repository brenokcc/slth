
import os
import requests
import uuid

"""
from slth.integrations import mercadopago
id = mercadopago.payment("04770402414", "juca@mail.com", "pix", "Produto 01", 1)
mercadopago.approved(id)
"""

MERCADOPAGO_TOKEN = os.environ.get('MERCADOPAGO_TOKEN')

def payment_methods():
    url = 'https://api.mercadopago.com/v1/payment_methods'
    headers = {'Authorization': f'Bearer {MERCADOPAGO_TOKEN}'}
    response = requests.get(url, headers=headers)
    return [dict(id=method['id'], value=method['name']) for method in response.json()]

def payment(cpf, email, payment_method, description, amount):
    url = 'https://api.mercadopago.com/v1/payments'
    headers = {'Authorization': f'Bearer {MERCADOPAGO_TOKEN}'}
    data = {
        "description": description,
        "external_reference": cpf,
        "payer": {
            "email": email,
            "identification": {
            "type": "CPF",
            "number": cpf
            }
        },
        "payment_method_id": payment_method,
        "transaction_amount": float(amount)
    }
    response = requests.post(url, headers=headers, json=data)
    data = response.json()
    try:
        return data['id']
    except KeyError:
        raise Exception(response.text)

def approved(id):
    url = f'https://api.mercadopago.com/v1/payments/{id}'
    headers = {'Authorization': f'Bearer {MERCADOPAGO_TOKEN}'}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data['status'] == "approved"
