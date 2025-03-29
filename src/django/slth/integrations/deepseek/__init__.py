import os
import requests

"""
from slth.integrations import deepseek
deepseek.ask("Em uma única palavra, qual a capital do Brasil?")
"""

DEEPSEEK_TOKEN = os.environ.get("DEEPSEEK_TOKEN")


def ask(prompt, model="deepseek-chat"):
    headers = {
        "Authorization": "Bearer {}".format(DEEPSEEK_TOKEN),
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
    }

    response = requests.post(
        "https://api.deepseek.com/chat/completions", headers=headers, json=data
    )
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except KeyError:
        return Exception(response.text)
