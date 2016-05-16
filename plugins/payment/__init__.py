from . import payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response

from collections import Mapping
from xml.dom import minidom
from flask import request
import requests
import json

payments_config = None

def main(config):
    global payments_config
    payments_config = config

def get_api_key(self):
    # get api keys from config
    global payments_config
    if 'nmi_api_key' in payments_config and payments_config['nmi_api_key']:
        api_key = payments_config['nmi_api_key']
    else:
        return make_error_response(
            "data_required",
            "Add NMI API keys into config.json"
        )

@app.route("/api/plugin/payment/get_url", methods=["POST"])
def request_money():
    pm = payment.Payment(get_api_key())
    return pm.get_url(10)
