import os
import requests

"""
from slth.integrations.google import places
places.search("Natal Shopping, Natal, RN")
places.geolocation("ChIJj2AvPX__sgcRNr1SxD-1jdU")
"""

def search(description):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?input={}&key={}".format(
            description, os.environ['GOOGLE_TOKEN']
        )
    )
    data = response.json()
    try:
        return [dict(id=prediction['place_id'], value=prediction['description']) for prediction in data['predictions']]
    except KeyError:
        return Exception(response.text)

def geolocation(id_or_description):
    if ' ' in id_or_description:
        data = search(id_or_description)
        place_id = data[0]['id'] if data else None
    else:
        place_id = id_or_description
    
    if place_id:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&key={}".format(
                place_id, os.environ['GOOGLE_TOKEN']
            )
        )
        data = response.json()
        try:
            location = data['result']['geometry']['location']
            return location['lat'], location['lng']
        except KeyError:
            return Exception(response.text)
    return None
