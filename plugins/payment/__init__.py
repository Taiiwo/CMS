from .payment import Payment
from taiicms import app
from taiicms.api import make_error_response, make_success_response, user, util

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
    users = util.get_collection('users', db=util.config["auth_db"])
    payment_user = users.find_one({"username": "payments"}, {"_id": True})

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
        usern.update({
            "$push": {
                "nmi_vaults": vault
            }
        })
        return make_success_response()
    else:
        return make_error_response('data_invalid')

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
    index = 0
    for vault in usern['nmi_vaults']:
        vault['method_index'] = index
        del vault['vault_id']
        vaults.append(vault)
        index += 1
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
