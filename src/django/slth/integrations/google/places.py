import os
import requests
import json
from django.core.cache import cache
from django.utils.text import slugify
from datetime import datetime

"""
from slth.integrations.google import places
places.search("Natal Shopping, Natal, RN")
places.geolocation("ChIJj2AvPX__sgcRNr1SxD-1jdU")
"""

def search(description):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?input={}&key={}".format(
            description, os.environ['GOOGLE_TOKEN']
        ), timeout=5
    )
    data = response.json()
    try:
        return [dict(id=prediction['place_id'], value=prediction['description']) for prediction in data['predictions']]
    except KeyError:
        return Exception(response.text)

def geolocation(id_or_description):
    key = f'latlng-{slugify(id_or_description)}'
    latlng = cache.get(key, None)
    if latlng is not None:
        return latlng
    if ' ' in id_or_description:
        data = search(id_or_description)
        place_id = data[0]['id'] if data else None
    else:
        place_id = id_or_description
    
    if place_id:
        url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&key={}".format(
            place_id, os.environ['GOOGLE_TOKEN']
        )
        response = requests.get(
            url, timeout=5
        )
        data = response.json()
        try:
            location = data['result']['geometry']['location']
            latlng = location['lat'], location['lng']
            cache.set(key, latlng, 600)
            with open("geolocation.log", "a") as file:
                file.write('>>> {} "{}" - {}\n'.format(datetime.now().strftime("%d/%m/%Y %H:%M"), id_or_description, latlng))
            return latlng
        except KeyError:
            file.write('>>> {} "{}" - ERROR\n'.format(datetime.now().strftime("%d/%m/%Y %H:%M"), id_or_description))
            return Exception(response.text)
    return None
