from .payment import Payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response, user, util

from collections import Mapping
from xml.dom import minidom
from flask import request
import requests
import time
import json
import re

def main(config):
    global payments_config, pm, users
    payments_config = config
    pm = False
    users = util.get_collection('users', db=util.config["auth_db"])
    payment_user = users.find_one({"username": "payments"}, {"_id": True})

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
    if not pm:
        pm = Payment(payments_config)
    vault_unrefined = pm.create_vault(cc, exp, cvv=cvv)
    vault = {
        "cc-number": vault_unrefined['billing']['cc-number'],
        "billing-id": vault_unrefined['billing']['billing-id'],
        "customer-id": vault_unrefined['customer-id'],
        "customer-vault-id": vault_unrefined['customer-vault-id'],
        "added": time.time()
    }
    if vault_unrefined['result'] == "1":
        # store the vault info somewhere in the user data
        usern = users.find_and_modify({"_id": usern["_id"]}, {
            "$push": {
                "nmi_vaults": vault
            }
        })
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
        usern = users.find_one_and_update(
            {"_id": usern["_id"]},
            {"$unset": {"nmi_vaults.%s" % card_id: ""}}
        )
        return make_success_response({"vaults": usern["nmi_vaults"]})
    else:
        return make_error_response("data_invalid", "card_id")


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
    if 'default_method' in usern:
        default_card = usern['default_method']
    else:
        default_card = False
    vaults = []
    for i in range(len(usern['nmi_vaults'])):
        vault = usern["nmi_vaults"][i]
        # ignore removed vaults
        if vault is None:
            continue

        vault['index'] = i
        del vault['customer-vault-id']
        vaults.append(vault)
    return make_success_response({
        "default_method": default_card,
        "payment_methods": vaults
    })

def get_product(product_id):
    products = util.get_collection('products')
    product_id = ObjectId(product_id) if type(product_is) is str else product_id
    return products.find_one({'_id': product_id, sender: payment_user['_id']})

# Posts to a datachest, but accepts money instead of a session key
@app.route("/api/plugin/payment/make-payment", methods=['POST'])
def make_payment():
    usern = user.authenticate()
    if not usern:
        return make_error_response("login_required")
    try:
        # recipient is the customer
        recipient = request.form['user_id']
        # id of the requested product
        product_id = request.form['product_id']
        payment_index = request.form['payment_index']
        shipping = request.form['shipping'] or False
        prepaid = request.form['recur_prepaid'] or False
        recur_at_day = request.form['recur_at_day'] or False
    except KeyError as e:
        return make_error_response('data_required', e.args)
    product = get_product(product_id)
    if not product: return make_error_response('invalid_data', 'product_id')
    product = product['data']
    if product['require_shipping'] and not shipping:
        return make_error_response('data_required', 'shipping')
    vault = usern['nmi_vaults'][payment_index]
    # do the transaction for both recuring and non-recuring payments
    if prepaid_days:
        amount = product['amount'] * prepaid_days
    transaction = pm.do_transaction(amount, vault['vault_id'])
    if not transaction:
        return make_error_response("data_invalid", "transaction-failed")
    sale = {}
    sale['recipient'] = recipient
    sale['sender'] = payment_user['_id']
    sale['ts'] = time.time()
    sale['data'] = {}
    # day of month of payment
    sale['data']['recur_at_day'] = recur_at_day
    # number of prepaid days/months based on recur_type
    sale['data']['recur_prepaid'] = prepaid
    # product reference
    sale['data']['product_id'] = product_id
    # shipping data
    sale['data']['shipping'] = shipping
    sale['data']['']
    util.store(sale, 'sales', visible=True)

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
