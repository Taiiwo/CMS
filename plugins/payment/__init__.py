from .payment import Payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response, user

from collections import Mapping
from xml.dom import minidom
from flask import request
import requests
import json
import re

def main(config):
    global payments_config, pm
    payments_config = config
    pm = False

@app.route("/api/plugin/payment/add-card", methods=["POST"])
def add_card():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")
    try:
        cc = request.form['cc']
        exp = request.form['exp']
        cvv = request.form['cvv'] if 'cvv' in request.form else False
    except KeyError as e:
        return make_error_response('data_required', e.args)
    global pm
    if not pm:
        pm = Payment(payments_config)
    vault = pm.create_vault(cc, exp, cvv=cvv)
    if vault['result'] == "1":
        # store the vault info somewhere in the user data

        return make_success_response()
    else:
        return make_error_response('data_invalid')
