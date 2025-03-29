import os
import requests

"""
from slth.integrations.openai import chatgpt
chatgpt.ask("Qual a capital do Brasil?")
"""

OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN')

def ask(prompt, model="gpt-4"):
    headers = {
        "Authorization": "Bearer {}".format(OPENAI_TOKEN),
        "Content-Type": "application/json"
    }
    data = {
        "model": model,  # Or "gpt-3.5-turbo"
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    data = response.json()
    try:
        return data['choices'][0]['message']['content']
    except KeyError:
        return Exception(response.text)
