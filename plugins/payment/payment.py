from collections import Mapping
from xml.dom import minidom

import time
import requests
import re
import xmltodict

class Payment():
    def __init__(self, payments_config):
        self.api_key = payments_config["nmi"]["api_key"]
        self.username = payments_config["nmi"]["username"]
        self.password = payments_config["nmi"]["password"]

    # Takes a Python dict and sends it to the API as XML
    def send_dict(self, data):
        # convert dict to XML
        xml = xmltodict.unparse(data)
        headers = {'Content-Type': 'text/xml'}
        return requests.post(
            'https://secure.nmi.com/api/v2/three-step',
            data=xml,
            headers=headers
        ).text

    # Gets the value of the first element: `element` from XML string
    def get_xml_value(self, element, xml):
        value = minidom.parseString(xml)\
            .getElementsByTagName(element)[0]\
            .firstChild\
            .nodeValue
        return value

    # Requests a form URL for stage 1 of NMI's 'three-step' API
    def get_form_url(self, redirect_url):
        data = {
            "add-customer": {
                "redirect-url": redirect_url,
                "api-key": self.api_key
            }
        }
        res = self.send_dict(data)
        return xmltodict.parse(res)['response']['form-url']

    # Can be called from within a flask route to respond as the redirect page
    def form_url_callback(self, request):
        from flask import request
        token_id = request.args.get("token-id")
        print (token_id)
        res = self.complete_action(token_id)
        if res["response"]["result"] == "1":
            return res
        return "Credit card info was rejected"

    # Sends the final request to complete the 'three-step' "transaction"
    def complete_action(self, token_id):
        res = self.send_dict({
            "complete-action": {
                "api-key": self.api_key,
                "token-id": token_id
            }
        })
        data = xmltodict.parse(res)
        return data

    # Emulates the browser's form request on the back end
    def send_cc(self, cc, exp, form_url, cvv=False):
        form_data = {
            'billing-cc-number': cc,
            'billing-cc-exp': exp
        }
        if cvv:
            # cvv is optional
            form_data['billing-cvv'] = cvv
        # make request but don't use the redirect
        response = requests.post(form_url, form_data, allow_redirects=False)
        return True if response.status_code == 301 else Exception()

    # Handles the whole 'three-step' process in one step.
    def create_vault(self, cc, exp, cvv=False):
        # get a form url
        # set the redirect url as something neutral because we're not using it
        form_url = self.get_form_url('https://secure.nmi.com/api/v2/three-step')
        # parse the token from the request URL
        token_id = form_url[41:]
        # send the cc deets. we don't need the return value
        self.send_cc(cc, exp, form_url, cvv=cvv)
        completed = self.complete_action(token_id)
        return completed['response']

    # Charges a vault ID
    def do_transaction(self, amount, vault):
        return requests.post(
            "https://secure.networkmerchants.com/api/transact.php",
            {
                "customer_vault_id": vault,
                "username": self.username,
                "password": self.password,
                "amount": "%.2f" % amount
            }
        ).text

if __name__ == "__main__":
    # Testing info
    payments_config = {
        "nmi":{
            "api_key": "2F822Rw39fx762MaV7Yy86jXGTC7sCDy",
            "username": "demo",
            "password": "password"
        }
    }
    p = Payment(payments_config)
    # sample info
    print(p.create_vault('4111111111111111', '10/25', cvv='999'))
