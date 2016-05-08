from taiicms import app, config, save_config, plugins
from taiicms.api import make_error_response, make_success_response, user
from taiicms.api.errors import error_names, add_error

from collections import Mapping
from xml.dom import minidom
from flask import request
import json

payments_config = None

def main(config):
    global payments_config
    payments_config = config

def dict2element(root, structure, doc):
    if isinstance(root, str):
        root = doc.createElement(root)
    for key, value in structure.items():
        el = doc.createElement("" if key is None else key)
        if isinstance(value, Mapping):
            dict2element(el, value, doc)
        else:
            el.appendChild(doc.createTextNode("" if value is None
                                              else value))
        root.appendChild(el)
    return root

def dict2xml(structure, tostring=False):
    root_element_name, value = next(iter(structure.items()))
    impl = minidom.getDOMImplementation()
    doc = impl.createDocument(None, root_element_name, None)
    dict2element(doc.documentElement, value, doc)
    return doc.toxml() if tostring else doc

@app.route("/api/plugin/payment/request_money", methods=["POST"])
def request_money():
    global payments_config
    # get api keys from config
    if 'nmi_api_key' in payments_config and payments_config['nmi_api_key']:
        api_key = payments_config['nmi_api_key']
    else:
        return make_error_response(
            "data_required",
            "Add NMI API keys into config.json"
        )
    # get the amount of money from POST
    try:
        amount = request.form['amount']
    except KeyError as e:
        return make_error_response("data_required", e.args)
    # if redirect_url is specified, get it
    if 'redirect_url' in request.form and request.form['redirect_url']:
        redirect_url = request.form['redirect_url']
    else:
        redirect_url = request.base_url + "stage_2"
    # construct the first stage request
    stage_1 = {
        "sale": {
            "amount": amount,
            "redirect_url": redirect_url,
            "api_key": api_key
        }
    }
    stage_1 = dict2xml(stage_1)
    return stage_1.toxml()
