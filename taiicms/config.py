import json
from binascii import b2a_hex
from os import urandom

from . import app

CONFIG_PATH = "./config.json"

default_config = {
    "secret_key": b2a_hex(urandom(32)).decode("utf8"),
    "port": 5000,
    "bind_addr": "0.0.0.0",

    "debug": False,

    "mongo": {
        "host": "localhost",
        "port": 27017,
        "default_db": "component",
        "auth_db": "auth",
    }
}


def merge_dicts(a, b):
    """Use a as base, overwrite with items from b"""
    new_dict = a
    for key, value in b.items():
        if isinstance(value, dict):
            if key in a:
                merge_dicts(a[key], b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]

    return new_dict

try:
    loaded_config = json.load(open(CONFIG_PATH))
    config = merge_dicts(default_config, loaded_config)
except IOError:
    print("Config file not found. Loading defaults...")
    print("You should probably edit the config file with your settings.")
    config = default_config

json.dump(
    config,
    open(CONFIG_PATH, "w"),
    sort_keys = True,
    indent = 2,
    separators = (',', ': ')
)

app.secret_key = config["secret_key"]
