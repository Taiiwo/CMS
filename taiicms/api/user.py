import os
import re
import time
import json

from flask import request, jsonify
from flask.ext.socketio import emit, send

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from .. import app, socketio, config
from . import util, make_error_response, make_success_response

users = util.get_collection("users", db=util.config["auth_db"])
users.create_index("username", unique=True)

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


def create_user(username, password, details={}, session_salt=None, is_datachest=False):
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
    print(session_salt)

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
    except KeyError as e:
        return make_error_response("data_required", e.args[0])

    # get optional fields
    try:
        details = request.form["details"]
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            return make_error_response("json_invalid")
    except KeyError:
        details = {}


    # validate the username and password
    if not (4 <= len(username) <= 140):
        return make_error_response("data_invalid", "username")
    if not (6 <= len(password)):
        return make_error_response("data_invalid", "password")

    # create the user object
    user_data = create_user(username, password, details)
    try:
        # store the user
        users.insert(user_data)
    except DuplicateKeyError: # if username is not unique
        return make_error_response("username_taken")

    # user created, log the user in
    return api_login()


# Logs in a user. Returns their authentication information
@app.route("/api/1/login", methods=["POST"])
def api_login():
    try:
        username = request.form["username"]
        password = request.form["password"]
    except KeyError as e:
        return make_error_response("data_required", e.args[0])

    # find the user in the collection
    user_data = users.find_one({"username": username.lower()})
    if user_data is None:
        return make_error_response("login_invalid")

    # check their password
    if not check_password(user_data, password):
        return make_error_response("login_invalid")

    # don"t create dynamic session keys for datachests
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
        return make_error_response("data_required", e.args)

    # Make sure the user is logged in
    user_data = authenticate()
    if not user_data:
        return make_error_response("login_required")

    # check if the old password matches the current password
    # it should be, but just in case they're cookie stealing
    if not check_password(user_data, cur_password):
        return make_error_response("password_incorrect")

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
        return make_error_response("login_required")

    users.delete_one({"_id": ObjectId(user_data["_id"])})
    return make_success_response({"message": "T^T"})


# Takes authentication information and returns user info
@app.route("/api/1/authenticate", methods=["POST"])
def api_authenticate():
    user_data = authenticate()
    if not user_data:
        return make_error_response("login_required")

    safe_user_data = get_safe_user(user_data)
    return make_success_response({"user_data": safe_user_data})


# converts a user/group name into an id
@app.route("/api/1/get_uid", methods=["GET"])
def get_uid():
    try:
        username = request.args["username"]
    except KeyError as e:
        return make_error_response("data_required", e.args)

    user_data = users.find_one({"username": username.lower()}, {"_id": True})
    if not user_data:
        return make_error_response("user_not_found")

    return make_success_response({"id": str(user_data["_id"])})


# Updates users" details property.
@app.route("/api/1/update-user", methods=["POST"])
def update_user():
    try:
        new_details = request.form["new_details"]
    except KeyError as e:
        return make_error_response("missing_data", e.args)

    user_data = authenticate()
    if not user_data:
        return make_error_response("login_required")

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
        return make_error_response("unknown_error")

@app.route("/api/1/join-paid-datachest")
def join_paid_datachest():
    try:
        query = {
            'orderid'
            'orderdescription'
            'shipping'
            'ipaddress'
            'tax'
            'ponumber'
            'firstname'
            'lastname'
            'company'
            'address1'
            'address2'
            'city'
            'state'
            'zip'
            'country'
            'phone'
            'fax'
            'email'
            'website'
        }
    except KeyError as e:
        return make_error_response("data_required", e.args)

# SocketIO handlers that allow limited database access to the front end

# Object that represents a socket connection
class Socket:
    def __init__(self, sid, query):
        self.sid = sid
        self.query = query
        self.connected = True
        self.recipient_sender = query["recipient_sender"] \
                if "recipient_sender" in query else False
        self.where_recipient = query["where_recipient"]\
                if "where_recipient" in query else False,
        self.where_sender = query["where_sender"]\
                if "where_sender" in query else False

    # Emits data to a socket"s unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid)

live_sockets = {"senders": {}, "recipients": {}}
all_listeners = {}

@socketio.on("listen", namespace="/component")
def listen_handler(data):
    request_data = json.loads(data)
    if not util.keys_exist([
                "backlog", "sender_pair", "collection", "recipient_pairs"
            ], request_data) or \
            len(request_data["sender_pair"]) != 2:
        emit("error", "Invalid params")
        return "0"
    # convert usernames to ids if requested
    recipientID_type = request_data["recipientID_type"] if "recipientID_type"\
            in request_data else "id"
    if recipientID_type == "username":
        # convert recipient usernames to ids
        users = util.get_collection("users", db=util.config["auth_db"])
        for pair in request_data["recipient_pairs"]:
            recipient = users.find_one({"user": pair[0]})
            if recipient and len(recipient) > 0:
                pair[0] = str(recipient["_id"])
            else:
                emit("error", "Recipient username not found")
                return "0"
    senderID_type = request_data["senderID_type"] if "senderID_type" \
            in request_data else "id"
    # send the user backlogs if requested
    if senderID_type == "username":
        # convert sender usernames to ids
        users = util.get_collection("users", db=util.config["auth_db"])
        sender = users.find_one({"user": request_data["sender_pair"][0]})
        if len(sender) > 0:
            request_data["sender_pair"][0] = str(recipient["_id"])
        else:
            emit("error", "Sender username not found")
            return "0"
    recipient_senders = []
    if "recipient_senders" in request_data:
        for sender in request_data["recipient_senders"]:
            recipient_senders.append(
                str(users.find_one({"user": sender})["_id"])
            )
        request_data["recipient_senders"] = recipient_senders
    # authenticate the request_data (and get a sneaky recipients list)
    auth, recipients = util.auth_listen(request_data)
    if not auth:
        return "0"
    # replace id searches with object id searches
    if "where_sender" in request_data:
        for clause in request_data["where_sender"]:
            if clause == "_id":
                request_data["where_sender"][clause] = ObjectId(
                    request_data["where_sender"][clause]
                )
    if "where_recipient" in request_data:
        for clause in request_data["where_recipient"]:
            if clause == "_id":
                request_data["where_recipient"][clause] = ObjectId(
                    request_data["where_recipient"][clause]
                )
    # send the user backlogs if requested
    if "backlog" in request_data and request_data["backlog"]:
        # get previously sent documents
        senders_log, recipients_log = util.get_documents(
            request_data["sender_pair"][0],
            recipients,
            request_data["collection"],
            time_order=True,
            recipient_senders=recipient_senders if recipient_senders else False,
            recipientID_type=recipientID_type,
            where_recipient=request_data["where_recipient"]\
                    if "where_recipient" in request_data else False,
            where_sender=request_data["where_sender"]\
                    if "where_sender" in request_data else False
        )
        for document in senders_log:
            if document["visible"]:
                document_tidy = {
                    "sender": document["sender"],
                    "recipient": document["recipient"],
                    "data": document["data"],
                    "id": str(document["_id"]),
                    "ts": document["ts"]
                }
                emit("data_sent", document_tidy)
        for document in recipients_log:
            if document["visible"]:
                document_tidy = {
                    "sender": document["sender"],
                    "recipient": document["recipient"],
                    "data": document["data"],
                    "id": str(document["_id"]),
                    "ts": document["ts"]
                }
                emit("data_received", document_tidy)
    # add socket to dict of sockets to keep updated
    # (Choosing speed over memory here)
    # create a socket object to represent us
    socket = Socket(request.sid, request_data)
    # add us to a list of all listener sockets
    live_sockets[socket.sid] = socket
    # make sure the list exists first
    if not request_data["sender_pair"][0] in live_sockets["senders"]:
        live_sockets["senders"][request_data["sender_pair"][0]] = []
    # append us to the list of senders subscribed to changes
    live_sockets["senders"][request_data["sender_pair"][0]].append(socket)
    # append us to a list of subscribers for each recipient we"re following
    for recipient in recipients:
        if not recipient in live_sockets["recipients"]:
            live_sockets["recipients"][recipient] = []
        live_sockets["recipients"][recipient].append(socket)

@socketio.on("send", namespace="/component")
def send_handler(data):
    request = json.loads(data)
    # validate request
    if not "sender_pair" in request or not "recipient" in request or \
            not "collection" in request or not "data" in request:
        emit("error", "Invalid Arguments")
        return False
    sender_pair = request["sender_pair"]
    recipient = request["recipient"]
    collection = request["collection"]
    message = request["data"]
    if "senderID_type" in request and request["senderID_type"] == "username":
        users = util.get_collection("users", db=util.config["auth_db"])
        user = users.find_one({"user": sender_pair[0]})
        if user:
            sender_pair[0] = str(user["_id"])
        else:
            emit("error", "Sender username does not exist")
            return False
    if "recipientID_type" in request and request["recipientID_type"] == \
            "username":
        users = util.get_collection("users", db=util.config["auth_db"])
        user = users.find_one({"user": recipient})
        if user:
            recipient = str(user["_id"])
            request["recipient"] = recipient
        else:
            emit("error", "Recipient username does not exist")
            return False
    # store document
    document = util.send(message, sender_pair, recipient, collection)
    if not document:
        return False
    # send Updates
    document_tidy = {
        "sender": document["sender"],
        "recipient": document["recipient"],
        "data": document["data"],
        "id": str(document["_id"]),
        "ts": document["ts"]
    }
    if not util.emit_to_relevant_sockets(request, document_tidy, live_sockets):
        emit("error", "Recipient or sender not found")

@socketio.on("disconnect")
def disconnect():
    # if socket is listening
    if request.sid in all_listeners:
        # remove from listeners
        all_listeners[request.sid].connected = False
        del all_listeners[request.sid]
