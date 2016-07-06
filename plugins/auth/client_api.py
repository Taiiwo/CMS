import os
import re
import time
import json

from flask import request, jsonify, url_for

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from . import app, config as plugin_config
from .api import (
    users,
    create_user,
    check_password,
    create_session,
    get_safe_user,
    authenticate,
    gen_salt,
    hash_password,

    LoginInvalid,
    LoginRequired,
    UsernameTaken,
    UserNotFound,
    PasswordIncorrect
)
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

# Registers a new user and logs them in
@app.route("/api/plugin/auth/register", methods=["POST"])
def api_register():
    # get required fields
    try:
        username = request.form["username"]
        password = request.form["password"]
        if plugin_config["email"]["enabled"]:
            try:
                email = request.form["email"]
            except KeyError as e:
                if plugin_config["email"]["required"]:
                    # if we require the email, re-raise the exception
                    # this is caught later and dealt with
                    raise e
                else:
                    email = None
        else:
            email = None
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

    if plugin_config["email"]["enabled"] and plugin_config["email"]["are_unique"]:
        # test if email is unique
        if users.find_one({"email": email}):
            raise DataInvalid("email taken")  # make into it's own error

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
        raise UsernameTaken({"username": username})

    if plugin_config["email"]["enabled"] and plugin_config["email"]["do_verify"]:
            send_email_verification(request, user_data, email)

    # user created, log the user in
    return api_login()


# Logs in a user. Returns their authentication information
@app.route("/api/plugin/auth/login", methods=["POST"])
def api_login():
    try:
        email_login = False
        if not "username" in request.form and plugin_config["email"]["allow_login"]:
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


@app.route("/api/plugin/auth/change_password", methods=["POST"])
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
@app.route("/api/plugin/auth/delete_account", methods=["POST"])
def api_delete_account():
    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    users.delete_one({"_id": ObjectId(user_data["_id"])})
    return make_success_response({"message": "T^T"})


# Takes authentication information and returns user info
@app.route("/api/plugin/auth/authenticate", methods=["POST"])
def api_authenticate():
    user_data = authenticate()
    if not user_data:
        raise LoginRequired()

    safe_user_data = get_safe_user(user_data)
    return make_success_response({"user_data": safe_user_data})


# converts a user/group name into an id
@app.route("/api/plugin/auth/get_uid", methods=["GET"])
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
@app.route("/api/plugin/auth/update-user", methods=["POST"])
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
