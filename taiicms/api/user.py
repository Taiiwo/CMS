import os
import re
import time
import json

from flask import request, jsonify, url_for

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from .. import app, config
from . import (
    util,
    make_error_response,
    make_success_response,
    ApiError,
    UnknownError,
    DataInvalid,
    DataRequired,
    JsonInvalid
)


users = util.get_collection("users", db=util.config["auth_db"])
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

@app.route('/verify-email/<string:uid>/<string:verification_key>')
def verify_email(uid, verification_key):
    user = users.find_one(
        {"_id": ObjectId(uid), "email_verification": verification_key}
    )
    if user:
        # set email_verified = True
        # remove email_verification
        user.update({
            "$set": {"email_verified": True},
            "$unset": {"email_verification": ""}
        })

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
        user = util.get_collection("users", db=util.config["auth_db"]).find_one({"user": user})
        return user

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
        except KeyError:
            return None

    user_data = users.find_one({'_id': ObjectId(user_id)})

    # check if the session is legit
    if not user_data:
        return None
    if not session == hash_password(user_data["passhash"], user_data["session_salt"]):
        return None
    return user_data

# Registers a new user and logs them in
@app.route("/api/1/register", methods=["POST"])
def api_register():
    # get required fields
    try:
        username = request.form["username"]
        password = request.form["password"]
        # if no email is submitted and emails are enforced
        if not "email" in request.form and config['force_email_submission']:
            return make_error_response('data_required', 'email')
        # if emails are not enforced, but one is supplied anyway
        elif "email" in request.form:
            email = request.form["email"]
        # if emails are not enforced and none is supplied
        else:
            email = False
    except KeyError as e:
        raise DataRequired(e.args[0])

    # get optional fields
    try:
        details = request.form["details"]
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            raise JsonInvalid()
    except KeyError:
        details = {}
    # test if email is unique
    email_query = {"email": email}
    if config['emails_are_unique'] and users.find_one(email_query):
        return make_error_response("data_invalid", "email taken")
    # validate the username and password
    if not (4 <= len(username) <= 140):
        raise DataInvalid("username")
    if not (6 <= len(password)):
        raise DataInvalid("password")

    # create the user object
    user_data = create_user(username, password, details, email=email)
    try:
        # store the user
        user_data = users.insert(user_data)
    except DuplicateKeyError as e: # if username is not unique
        print (e.args)
        raise UsernameTaken({"username": username})
    if config['verify_emails']:
        send_email_verification(request, user_data, email)
    # user created, log the user in
    return api_login()


# Logs in a user. Returns their authentication information
@app.route("/api/1/login", methods=["POST"])
def api_login():
    try:
        email_login = False
        if not "username" in request.form and config['allow_login_with_email']:
            email = request.form['email']
            email_login = True
        else:
            username = request.form["username"]
        password = request.form["password"]
    except KeyError as e:
        raise DataRequired(e.args[0])

    # find the user in the collection
    if email_login:
        user_data = users.find_one({"email": email.lower()})
    else:
        user_data = users.find_one({"username": username.lower()})
    if user_data is None:
        raise LoginInvalid()

    # check their password
    if not check_password(user_data, password):
        raise LoginInvalid()

    # don't create dynamic session keys for datachests
    if not user_data["is_datachest"]:
        session_key = create_session(user_data)

    user_id = str(user_data["_id"])
    user_data = get_safe_user(user_data)
    return make_success_response({
        "session": session_key,
        "user_id": user_id,
        "user_data": user_data
    })


###
### Here starts the auth-only functions. Make sure you check their session cookies!
###


@app.route("/api/1/change_password", methods=["POST"])
def api_change_password():
    """Changes a user"s password."""
    try:
        cur_password = request.form["cur_password"]
        new_password = request.form["new_password"]
    except KeyError as e:
        raise DataRequired(e.args[0])

    # Make sure the user is logged in
    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    # check if the old password matches the current password
    # it should be, but just in case they're cookie stealing
    if not check_password(user_data, cur_password):
        raise PasswordIncorrect()

    # update the user
    salt = gen_salt(as_hex=False)
    salt_hex = b2a_hex(salt)
    passhash = hash_password(new_password, salt)

    util.update_user(
        user_data["_id"],
        {
            "$set": {
                "salt": salt_hex,
                "passhash": passhash,
            }
        }
    )

    # calling user will need new session key, but ceebs

    return make_success_response()


# Completely deletes a user"s account
@app.route("/api/1/delete_account", methods=["POST"])
def api_delete_account():
    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    users.delete_one({"_id": ObjectId(user_data["_id"])})
    return make_success_response({"message": "T^T"})


# Takes authentication information and returns user info
@app.route("/api/1/authenticate", methods=["POST"])
def api_authenticate():
    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    safe_user_data = get_safe_user(user_data)
    return make_success_response({"user_data": safe_user_data})


# converts a user/group name into an id
@app.route("/api/1/get_uid", methods=["GET"])
def get_uid():
    try:
        username = request.args["username"]
    except KeyError as e:
        raise DataRequired(e.args[0])

    user_data = users.find_one({"username": username.lower()}, {"_id": True})
    if not user_data:
        raise UserNotFound()

    return make_success_response({"id": str(user_data["_id"])})


# Updates users" details property.
@app.route("/api/1/update-user", methods=["POST"])
def update_user():
    try:
        new_details = request.form["new_details"]
    except KeyError as e:
        raise DataRequired(e.args[0])

    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    #   User is authed, do some stuff
    new_details = json.loads(new_details)
    update_query = {
        "$set": {
            "details": user["details"].update(new_details)
        }
    }
    if util.update_user(user["_id"], update_query):
        return make_success_response()
    else:
        raise UnknownError()
