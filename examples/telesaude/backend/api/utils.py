import os
import requests
from .models import Estado, Municipio
        

def buscar_endereco(cep):
    endereco = {}
    if cep:
        dados = requests.get('{}{}'.format(os.environ['CEP_API_URL'], cep.replace('.', '').replace('-', ''))).json()
        sigla, nome, codigo = dados['estado'], dados['estado_info']['nome'], dados['estado_info']['codigo_ibge']
        estado = Estado.objects.get_or_create(sigla=sigla, codigo=codigo, nome=nome)[0]
        nome, codigo = dados['cidade'], dados['cidade_info']['codigo_ibge']
        municipio = Municipio.objects.filter(codigo=codigo).first()
        if municipio is None:
            municipio = Municipio.objects.get_or_create(estado=estado, codigo=codigo, nome=nome)[0]
        endereco.update(bairro=dados['bairro'], logradouro=dados['logradouro'], municipio=municipio)
    return endereco