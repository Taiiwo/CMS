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
from flask.ext.socketio import emit, send
from .api import util, make_error_response, make_success_response

# SocketIO handlers that allow limited database access to the front end

# Object that represents a socket connection
class Socket:
    def __init__(self, sid, query):
        self.sid = sid
        self.query = query
        self.connected = True
        auths = query['auths']
        self.ids = list(ObjectId(auth[0]) for auth in auths)
        self.where = query['where'] if "where" in query else False

    # Emits data to a socket"s unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid)

live_sockets = {}
all_sockets = {}

@socket.on("listen", namespace="/component")
def listen_handler(data):
    request_data = json.loads(data)
    if not util.keys_exist(["collection", "auths"], request_data):
        emit("log", "Missing Arguments")
        return "0"
    # check all authentications
    users = util.get_collection('users', db=util.config['auth_db'])
    auths = util.escape_user_query(request_data['auths'])
    for pair in auths:
        if not util.auth(pair[0], pair[1]):
            emit("log", "A supplied username was not found")
            return "0"
    if "where" in request_data:
        request_data['where'] = util.escape_user_query(request_data['where'])
    # send the user backlogs if requested
    if "backlog" in request_data and request_data["backlog"]:
        # get previously sent documents
        backlog = util.get_documents(
            request_data['auths'],
            request_data["collection"],
            time_order=True,
            where=request_data['where'] if "where" in request_data else False
        )
        # send each document separately
        for document in backlog:
            # make sure it's a client document
            if document["visible"]:
                document_tidy = {
                    "sender": document["sender"],
                    "recipient": document["recipient"],
                    "data": document["data"],
                    "id": str(document["_id"]),
                    "ts": document["ts"],
                    "update": False
                }
                emit("data", document_tidy)
    # add socket to dict of sockets to keep updated
    # (Choosing speed over memory here)
    # create a socket object to represent us
    socket = Socket(request.sid, request_data)
    # add us to a list of all listener sockets
    if not request_data["collection"] in live_sockets:
        live_sockets[request_data["collection"]] = []
    live_sockets[request_data["collection"]].append(socket)
    all_sockets[socket.sid] = socket

@socket.on("send", namespace="/component")
def send_handler(data):
    request = json.loads(data)
    print(request)
    # validate request
    if not util.keys_exist(
            ["sender", "recipient", "auths", "collection", "data"],
            request):
        emit("log", "Missing Arguments")
        return "0"
    # find the auth pair of the desired sender
    users = util.get_collection("users", db=util.config["auth_db"])
    sender = users.find_one({"username": request['sender']});
    sender_pair = False
    for auth in request['auths']:
      if auth[0] == str(sender["_id"]):
        sender_pair = auth
    if not sender_pair:
        emit("log", "Sender authentication not found")
        return "0"
    # authenticate sender
    sender = util.auth(sender_pair[0], sender_pair[1])
    if not sender:
        emit("log", "Failed to authenticate sender")
        return "0"
    # find recipient
    recipient = users.find_one({"username": request['recipient']})
    if not recipient:
        emit("log", "Recipient username does not exist")
        return False
    # store document
    document = util.send(request['data'], str(sender["_id"]),
                         str(recipient["_id"]), request['collection'])
    if not document:
        emit('log', make_error(
            'unknown_error',
            "Data was not added to the DB for some reason"
        ))
        return "0"
    # send Updates
    document_tidy = {
        "sender": document["sender"],
        "recipient": document["recipient"],
        "data": document["data"],
        "id": str(document["_id"]),
        "ts": document["ts"],
        "update": False
    }
    util.emit_to_relevant_sockets(request, document, live_sockets)
    emit("log", "Data was sent")
  
@socket.on("update", namespace="/component")
def update_handler(data):
    request = json.loads(data)
    # validate request
    if not util.keys_exist(
            ["auths", "collection", "data", "document_id"],
            request):
        emit("log", "Missing Arguments")
        return "0"
    # find document
    coll = util.get_collection(request['collection'])
    document = coll.find_one({"_id": ObjectId(request['document_id'])})
    # authenticate update
    authenticated = False
    for auth in request['auths']:
        if auth[0] == document['sender']:
            if util.auth(auth[0], auth[1]): 
                authenticated = True
                sender = auth[0]
                break
            else:
                # don't allow more than one invalid request to prevent
                # server-side password bruteforcing. Just incase.
                break
    if not authenticated:
        emit("log", "Insufficient permissions")
        return "0"
    # update document
    document = util.update_document(request['data'], request['document_id'],
                                    request['collection'])
    if not document:
        emit('log', make_error(
            'unknown_error',
            "Data was not added to the DB for some reason"
        ))
        return "0"
    # send Updates
    document_tidy = {
        "sender": document["sender"],
        "recipient": document["recipient"],
        "data": document["data"],
        "id": str(document["_id"]),
        "ts": document["ts"],
        "update": True
    }
    util.emit_to_relevant_sockets(request, document, live_sockets)
    emit("log", "Data was updated")


@socket.on("disconnect", namespace="/component")
def disconnect():
    print(len(all_sockets))
    # if socket is listening
    if request.sid in all_sockets:
        # remove from listeners
        all_sockets[request.sid].connected = False
        del all_sockets[request.sid]
