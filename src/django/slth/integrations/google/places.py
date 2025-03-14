import os
import requests

"""
from slth.integrations.google import places
places.search("Natal Shopping, Natal, RN")
places.geolocation("ChIJj2AvPX__sgcRNr1SxD-1jdU")
"""

GOOGLE_TOKEN = os.environ['GOOGLE_TOKEN']

def search(key_words):
    
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?input={}&key={}".format(
            key_words, GOOGLE_TOKEN
        )
    )
    data = response.json()
    try:
        return [dict(id=prediction['place_id'], description=prediction['value']) for prediction in data['predictions']]
    except KeyError:
        return Exception(response.text)

def geolocation(place_id):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&key={}".format(
            place_id, GOOGLE_TOKEN
        )
    )
    data = response.json()
    try:
        location = data['result']['geometry']['location']
        return location['lat'], location['lng']
    except KeyError:
        return Exception(response.text)
