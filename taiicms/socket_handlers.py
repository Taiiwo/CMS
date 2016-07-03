import os
import re
import time
import json

from flask import request, jsonify

from binascii import b2a_hex, a2b_hex
from hashlib import sha512

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

from . import app, config, socket
from flask_socketio import emit, send
from .api import util, make_error_response, make_success_response, make_error

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

@socket.on("listen", namespace="/component")
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
            recipient = users.find_one({"username": pair[0]})
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
        sender = users.find_one({"username": request_data["sender_pair"][0]})
        if len(sender) > 0:
            request_data["sender_pair"][0] = str(recipient["_id"])
        else:
            emit("error", "Sender username not found")
            return "0"
    recipient_senders = []
    if "recipient_senders" in request_data:
        for sender in request_data["recipient_senders"]:
            recipient_senders.append(
                str(users.find_one({"username": sender})["_id"])
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

@socket.on("send", namespace="/component")
def send_handler(data):
    print(data)
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
        user = users.find_one({"username": sender_pair[0]})
        if user:
            sender_pair[0] = str(user["_id"])
        else:
            emit("error", "Sender username does not exist")
            return False
    if "recipientID_type" in request and request["recipientID_type"] == \
            "username":
        users = util.get_collection("users", db=util.config["auth_db"])
        user = users.find_one({"username": recipient})
        if user:
            recipient = str(user["_id"])
            request["recipient"] = recipient
        else:
            emit("error", "Recipient username does not exist")
            return False
    # store document
    document = util.send(message, sender_pair, recipient, collection)
    if not document:
        emit('error', make_error(
            'unknown_error',
            "Data was not added to the DB for some reason"
        ))
        return False
    # send Updates
    document_tidy = {
        "sender": document["sender"],
        "recipient": document["recipient"],
        "data": document["data"],
        "id": str(document["_id"]),
        "ts": document["ts"],
        "update": False
    }
    util.emit_to_relevant_sockets(request, document_tidy, live_sockets)
    emit("data_sent", "Data was sent")

@socket.on("update", namespace="/component")
def update_handler(data):
    print(data)
    request = json.loads(data)
    # validate request
    if not "sender_pair" in request or not "document_id" in request or \
            not "collection" in request or not "data" in request:
        emit("error", "Invalid Arguments")
        return False
    sender_pair = request["sender_pair"]
    document_id = request["document_id"]
    collection = request["collection"]
    document = request["data"]
    # convert usernames to ids
    if "senderID_type" in request and request["senderID_type"] == "username":
        users = util.get_collection("users", db=util.config["auth_db"])
        user = users.find_one({"username": sender_pair[0]})
        if user:
            sender_pair[0] = str(user["_id"])
        else:
            emit("error", "Sender username does not exist")
            return False
    # update document
    document = util.update_document(
        document, sender_pair, document_id, collection
    )
    if not document:
        emit('error', make_error(
            'unknown_error',
            "Sender was not authenticated to make changes"
        ))
        return False
    # send Updates
    document_tidy = {
        "sender": document["sender"],
        "recipient": document["recipient"],
        "data": document["data"],
        "id": str(document["_id"]),
        "ts": document["ts"],
        "update": True
    }
    util.emit_to_relevant_sockets(request, document_tidy, live_sockets)
    emit("data_sent", "Data was updated")

@socket.on("disconnect")
def disconnect():
    # if socket is listening
    if request.sid in all_listeners:
        # remove from listeners
        all_listeners[request.sid].connected = False
        del all_listeners[request.sid]
