import os
import re
import time
import json

from flask import request, jsonify, url_for

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from . import app, config, api
from cms.api import (
    util,
    make_error_response,
    make_success_response,
    ApiError,
    UnknownError,
    DataInvalid,
    DataRequired,
    JsonInvalid
)


@app.route('/verify-email/<string:uid>/<string:verification_key>')
def verify_email(uid, verification_key):
    user = api.users.find_one(
        {"_id": ObjectId(uid), "email_verification": verification_key}
    )
    if user:
        # set email_verified = True
        # remove email_verification
        user.update({
            "$set": {"email_verified": True},
            "$unset": {"email_verification": ""}
        })
