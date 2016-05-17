from collections import Mapping
from xml.dom import minidom
import time
import requests
import re

class Payment():

    def __init__(self, api_key):
        self.api_key = api_key

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

    def get_url(self, amount):
        # this is never acutally used :\
        redirect_url = "/"
        # construct the first stage request
        stage_1 = {
            "add-customer": {
                "redirect-url": redirect_url,
                "api-key": self.api_key
            }
        }
        # send stage 1
        stage_1_result = self.send_dict(stage_1)
        print(stage_1_result)
        # parse stage_1 results
        stage_2_url = self.get_xml_value('form-url', stage_1_result)
        # construct stage 3
        stage_3 = {
            "complete-action": {
                "api-key": self.api_key,
                "token-id": stage_2_url
            }
        }
        s3r = self.send_dict(stage_3)
        if self.get_xml_value('result', s3r) == 1:
            # transaction was successful
            # store token in user data for use with later purchases
            # return token
            pass
        return s3r

if __name__ == "__main__":
    # NOTE: This is not my real API key you fools
    pm = Payment('2F822Rw39fx762MaV7Yy86jXGTC7sCDy')
    print (pm.first_purchase('5431111111111111', '10/25', '999', '10'))
