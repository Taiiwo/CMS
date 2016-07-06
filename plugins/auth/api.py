import os
import re
import time
import json

from flask import request, jsonify, url_for

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from . import app, config
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

users = util.get_collection(config["mongo"]["col"], db=config["mongo"]["db"])
users.create_index("username", unique=True)
# users.create_index("")

##############################
# All the user api related expceptions go here.
##############################

class LoginRequired(ApiError):
    name = "login_required"
    details = "The resource requested requires authentication."
    status_code = 403


class LoginInvalid(ApiError):
    name = "login_invalid"
    details = "The username and password did not match."


class UsernameTaken(ApiError):
    name = "username_taken"
    details = "The username has been taken."


class UserNotFound(ApiError):
    name = "user_not_found"
    details = "The specified user could not be found."


class PasswordIncorrect(ApiError):
    name = "password_incorrect",
    details = "Password given was incorrect."

##############################
# End user exceptions
##############################


def get_hash(data, as_hex=True):
    hasher = sha512()
    hasher.update(data)
    if as_hex:
        return hasher.hexdigest()
    else:
        return hasher.digest()


def hash_password(password, salt, as_hex=True):
    hasher = sha512()
    hasher.update(password.encode("utf8"))
    hasher.update(salt)
    if as_hex:
        return hasher.hexdigest()
    else:
        return hasher.digest()


def gen_salt(as_hex=True):
    salt = os.urandom(32)
    if as_hex:
        return b2a_hex(salt)
    else:
        return salt


def check_password(user_data, password):
    pass_salt = a2b_hex(user_data["salt"])
    passhash = hash_password(password, pass_salt)
    print(user_data)
    print(passhash)
    print(user_data["passhash"])
    return passhash == user_data["passhash"]

def send_email_verification(request, uid, email):
    # create a verification key
    key = gen_salt(as_hex=True)
    path = "/%s/%s" % (uid, key.decode('ascii'))
    users.update(
        {"_id": ObjectId(uid)},
        {"$set": {
            "email_verification": key,
            "email_verified": False
        }}
    )
    import smtplib
    from email.mime.text import MIMEText
    msg = """
        I don't have time for fancy emails. Verify you email here: %s
    """ % request.url_root + path
    msg = MIMEText(msg)
    msg['Subject'] = "Verify your Email!"
    msg['From'] = "webmaster@llort.gq"
    msg['To'] = email
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail("webmaster@llort.gq", email, msg.as_string())
    return True


def create_user(username, password, details={}, session_salt=None,
                is_datachest=False, email=False):
    salt = gen_salt(as_hex=False)
    salt_hex = b2a_hex(salt)
    passhash = hash_password(password, salt)

    # construct user model
    user_data = {
        "username": username.lower(),
        "display_name": username,
        "passhash": passhash,   # Effective permanent salt
        "salt": salt_hex,
        "details": details,
        "session_salt": session_salt,
        "is_datachest": False,
        "datachests": {
            "public": ["Public", get_hash(b"")],  # add public session
        },
    }
    if email:
        user_data['email'] = email.lower()
    return user_data


def get_safe_user(user):
    if isinstance(user, dict):
        safe_user = {}
        for key in ["username", "display_name", "details", "is_datachest", "datachests"]:
            safe_user[key] = user[key]
        return safe_user
    else:
        user_data = users.find_one({"user": user})
        if user:
            return get_safe_user(user_data)
        else:
            return None

def create_session(user_data):
    # create a salt so the same session key is only valid once
    session_salt = gen_salt(as_hex=False)
    # add the salt to the database so we can verify it later
    users.update(
        {"_id": user_data["_id"]},
        {
            "$set": {"session_salt": session_salt}
        }
    )

    # construct a session key from the salt
    session_key = hash_password(user_data["passhash"], session_salt)
    return session_key

def authenticate(user_id=None, session=None):
    if user_id is None or session is None:
        try:
            user_id = request.cookies["user_id"]
            session = request.cookies["session"]
        except KeyError as e:
            return None

    user_data = users.find_one({'_id': ObjectId(user_id)})
    
    # check if the session is legit
    if not user_data:
        return None
    if not session == hash_password(user_data["passhash"], user_data["session_salt"]):
        return None
    return user_data
