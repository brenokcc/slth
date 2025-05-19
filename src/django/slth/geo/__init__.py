import json
import gzip
import slth
import os

def load(name):
    path = os.path.join(os.path.dirname(slth.__file__), "geo", f"{name}.json.gz")
    with gzip.open(path, 'rb') as f_in:
        return json.loads(f_in.read())


def brazil_states():
    return load("brazil-states")

def brazil_regions():
    return load("brazil-regions")
