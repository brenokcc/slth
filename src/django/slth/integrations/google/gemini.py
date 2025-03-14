import os
import requests

"""
from slth.integrations.google import gemini
gemini.ask("Qual a capital do Brasil?")
"""

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def ask(prompt):
    data = {"contents": [{"parts":[{"text": prompt}]}]}
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={}".format(
            GEMINI_API_KEY
        ), json=data
    )
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except KeyError or IndexError:
        return Exception(response.text)
    