from .payment import Payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response, user, util

from collections import Mapping
from xml.dom import minidom
from flask import request
from bson import ObjectId
import requests
import time
import json
import re

def main(config):
    global payments_config, pm
    payments_config = config
    pm = Payment(payments_config)

users = util.get_collection('users', db=util.config["auth_db"])
payments_user = users.find_one({"username": "Payments"})
products_user = users.find_one({"username": "Products"})

@app.route("/api/plugin/payment/add-card", methods=["POST"])
def add_card():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")
    try:
        cc = request.form['card_number']
        exp = request.form['card_expiry']
        cvv = request.form['security_code']\
                if 'security_code' in request.form else False
    except KeyError as e:
        return make_error_response('data_required', e.args)
    global pm
    vault_unrefined = pm.create_vault(cc, exp, cvv=cvv)
    if vault_unrefined['result'] == '3':
      return make_error_response("data_invalid", vault_unrefined['result-text'])
    vault = {
        "cc-number": vault_unrefined['billing']['cc-number'],
        "billing-id": vault_unrefined['billing']['billing-id'],
        "customer-id": vault_unrefined['customer-id'],
        "customer-vault-id": vault_unrefined['customer-vault-id'],
        "added": time.time()
    }
    if vault_unrefined['result'] == "1":
        # store the vault info somewhere in the user data
        users.update_one({"_id": usern["_id"]}, {
            "$push": {
                "nmi_vaults": vault
            }
        })
        usern = users.find_one({"_id": usern['_id']})
        return make_success_response({"vaults": usern["nmi_vaults"]})
    else:
        return make_error_response('data_invalid')

@app.route("/api/plugin/payment/remove-method", methods=["POST"])
def remove_card():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")

    try:
        method_id = request.form["method_id"]
    except KeyError as e:
        return make_error_response('data_required', e.args[0])
    try:
        method_id = int(method_id)
    except ValueError:
        return make_error_response("data_invalid", "method_id")

    if method_id < len(usern["nmi_vaults"]):
        if usern["default_method"] == method_id:
            usern = users.find_one_and_update(
                {"_id": usern["_id"]},
                {
                    "$unset": {"nmi_vaults.%s" % method_id: ""},
                    "$set": {"default_method": False}
                }
            )
        else:
            usern = users.find_one_and_update(
                {"_id": usern["_id"]},
                {"$unset": {"nmi_vaults.%s" % method_id: ""}}
            )
        return make_success_response({"vaults": usern["nmi_vaults"]})
    else:
        return make_error_response("data_invalid", "method_id")


@app.route("/api/plugin/payment/set-default-method", methods=['POST'])
def set_default_method():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")

    try:
        method_id = request.form["method_id"]
    except KeyError as e:
        return make_error_response('data_required', e.args[0])
    try:
        method_id = int(method_id)
    except ValueError:
        return make_error_response("data_invalid", "method_id")

    res = users.update_one(
        {"_id": usern["_id"]},
        {"$set": {"default_method": method_id}}
    )
    if res:
        return make_success_response()
    else:
        return make_error_response("unknown_error")


@app.route("/api/plugin/payment/get-payment-methods", methods=['POST'])
def get_payment_methods():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")
    if not "nmi_vaults" in usern:
        return make_error_response("data_missing", "user has no vaults")
    if 'default_method' in usern:
        default_card = usern['default_method']
    else:
        default_card = False
    vaults = []
    for i in range(len(usern['nmi_vaults'])):
        vault = usern["nmi_vaults"][i]
        if vault:
          vault['index'] = i
          del vault['customer-vault-id']
        vaults.append(vault)
    return make_success_response({
        "default_method": default_card,
        "payment_methods": vaults
    })

def get_product(product_id):
    products = util.get_collection('products')
    product_id = ObjectId(product_id) if type(product_id) is str else product_id
    print(products_user['_id'])
    return products.find_one({'_id': ObjectId(product_id), "sender": str(products_user['_id'])})

# Posts to a datachest, but accepts money instead of a session key
@app.route("/api/plugin/payment/make-payment", methods=['POST'])
def make_payment():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")
    try:
        orders = json.loads(request.form['orders'])
        shipping = json.loads(request.form['shipping'])
        payment_method = request.form['payment_method']
    except KeyError as e:
        return make_error_response('data_required', e.args)
    # build order list
    order_list = []
    cost = 0
    for order in orders:
        print(order)
        order_item = {}
        product = get_product(order['id'])
        print(product)
        if not product:
            return make_error_response('data_invalid', 'product_id')
        if product['data']['require_shipping']:
            if not shipping:
                return make_error_response('data_required', 'shipping')
            order_item['shipping'] = shipping
        order_item['product'] = product
        order_item['quantity'] = order['quantity']
        order_item['amount'] = order_item['product']['data']['amount']\
                * order_item['quantity']
        cost += order_item['amount']
        order_list.append(order_item)
    
    # charge the user the cost
    transaction = pm.do_transaction(cost, usern['nmi_vaults'][int(payment_method)])
    if not transaction:
        return make_error_response("data_invalid", "transaction-failed")
    for order in order_list:
        sale = {}
        sale['recipient'] = str(usern['_id'])
        sale['sender'] = str(payments_user['_id'])
        sale['ts'] = time.time()
        sale['data'] = order
        util.store(sale, 'sales', visible=True)
    return make_success_response()

"""
example product
{
    "require_shipping": bool,
        True if the product requires shipping information
    "recur": bool,
        True if the product is billed on a cycle
    "recur_type": False | ["ndays", "at_day"],
        False: `recur` is False,
        "ndays": `amount` is charged every `recur_ndays`
        "at_day": `amount` is charged every day of month specified by the sale
                  document's `recur_at_day`. Defaults to the day of purchase
    "recur_ndays": False | int,
    "amount": float,
    "name": str,
    "desc": str,
    "file_id": False | str,
        ID of file to be added to the user's downloadable files
    "type": ["recuring", "onetime", "prepaid"],
    "ongoing": bool
}
"""
