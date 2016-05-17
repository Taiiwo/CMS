from .payment import Payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response, user

from collections import Mapping
from xml.dom import minidom
from flask import request
import requests
import json


payments_config = None
pm = None


def main(config):
    global payments_config, pm
    payments_config = config
    pm = Payment(payments_config, app)


@app.route("/api/plugin/payment/step_one", methods=["POST"])
def request_money():
    user_data = user.authenticate()
    print(user_data)
    if user_data is None and not app.debug:
        return make_error_response("login_required")
    return make_success_response({
        "url": pm.step_one()
    })
