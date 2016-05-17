from collections import Mapping
from xml.dom import minidom

import time
import requests
import re
import xmltodict

from flask import url_for, request

class Payment():
    redirect_url = "/"
    def __init__(self, payments_config, app):
        self.api_key = payments_config["nmi"]["api_key"]
        self.username = payments_config["nmi"]["username"]
        self.username = payments_config["nmi"]["password"]
        
        app.add_url_rule(
            "/plugins/payments/nmi_callback",
            view_func=self.step_two_callback,
            methods=["POST", "GET"]
        )
        self.redirect_url = "http://localhost:5000/plugins/payments/nmi_callback"
        self.tokens = {}

    def dict2xml(self, structure, tostring=True):
        def dict2element(root, structure, doc):
            if isinstance(root, str):
                root = doc.createElement(root)
            for key, value in structure.items():
                el = doc.createElement("" if key is None else key)
                if isinstance(value, Mapping):
                    dict2element(el, value, doc)
                else:
                    value = "" if value is None else value
                    el.appendChild(doc.createTextNode(value))
                root.appendChild(el)
            return root
        root_element_name, value = next(iter(structure.items()))
        impl = minidom.getDOMImplementation()
        doc = impl.createDocument(None, root_element_name, None)
        dict2element(doc.documentElement, value, doc)
        return doc.toxml() if tostring else doc

    def send_dict(self, data):
        # convert dict to XML
        xml = self.dict2xml(data)
        headers = {'Content-Type': 'text/xml'}
        return requests.post(
            'https://secure.nmi.com/api/v2/three-step',
            data=xml,
            headers=headers
        ).text

    def get_xml_value(self, element, xml):
        value = minidom.parseString(xml)\
            .getElementsByTagName(element)[0]\
            .firstChild\
            .nodeValue
        return value

    def step_one(self):
        data = {
            "add-customer": {
                "redirect-url": self.redirect_url,
                "api-key": self.api_key
            }
        }
        print(data)
        res = requests.post(
            "https://secure.nmi.com/api/v2/three-step",
            self.dict2xml(data),
            headers={"Content-Type": "text/xml"}
        )
        return self.get_xml_value('form-url', res.text)


    def step_two_callback(self):
        token_id = request.args.get("token-id")
        res = self.step_three(token_id)
        if res["response"]["result"] == "1":
            return self.do_transaction(1, res["response"]["customer-vault-id"])
        return "some Error"

    def step_three(self, token_id):
        res = self.send_dict({
            "complete-action": {
                "api-key": '2F822Rw39fx762MaV7Yy86jXGTC7sCDy',
                "token-id": token_id
            }
        })
        data = xmltodict.parse(res)

        return data

    def do_transaction(self, amount, vault):
        print("%.2f" % amount)
        return requests.post(
            "https://secure.networkmerchants.com/api/transact.php",
            {
                "customer_vault_id": vault,
                "username": "demo",
                "password": "password",
                "amount": "%.2f" % amount
            }
        ).text
