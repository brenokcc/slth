import requests

def consultar(cep):
    cep = cep.replace('.', '').replace('-', '')
    url = 'https://viacep.com.br/ws/{}/json/'.format(cep)
    return requests.get(url, timeout=5).json()
