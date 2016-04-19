import os
import re
import json
import time
import hashlib
from lib import util
from flask.ext.cors import CORS
from flask import Flask, request
from bson.objectid import ObjectId
from flask.ext.socketio import SocketIO, emit, send

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'Hardcoded Temporary Key'
socketio = SocketIO(app)
util = util.Util()

@app.route('/')
def index():
    return 'index'

# Registers a new user and logs them in
@app.route('/register', methods=['POST'])
def register():
    user = request.form['user']
    passw = request.form['passw']
    if 'details' in request.form:
        details = request.form['details']
        details = json.loads(details)
    else:
        details = False
    # get the users collection
    users = util.get_collection('users', db=util.config['auth_db'])
    # construct user model
    userData = {
        'user': user,
        'passw': util.sha512(user + passw),   # Effective permanent salt
        'details': details,
        'session_salt': False,
        'is_datachest': False,
        'datachests': {'public': ['public', util.sha512('')]}   # add public session
    }
    # make sure user is not already registered
    if users.find({'user': user}).count() > 0:
        return 'userTaken'
    # validate the username and password
    elif len(user) < 140 and len(passw) >= 6 and len(passw) < 140:
        # insert the user into the database and return their id
        users.insert(userData)
        # log the user in
        return login()
    else:
        # Only broken clients will recieve this error
        return 'error'

# Logs in a user. Returns their authentication information
@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    passw = request.form['passw']
    # get user collection
    users = util.get_collection('users', db=util.config['auth_db'])
    # find the user in the collection
    user_data = users.find_one({'user': user})
    # if the login details match up '
    if user_data and user_data['passw'] == util.sha512(user + passw):
        # don't create dynamic session keys for datachests
        if not user_data['is_datachest']:
            # create a salt so the same session key is only valid once
            session_salt = util.sha512(os.urandom(512))
            # add the salt to the database so we can verify it later
            util.update_user(user_data['_id'], {
                "$set": {'session_salt': session_salt}
            })
            # construct a session key from the salt
            session_key = util.sha512(session_salt + user_data['passw'])
        userID = str(user_data['_id'])
        del user_data['_id']# delete sensitive variables
        del user_data['passw']# ^^^^^^^^^^^^^^^^^^^^^^^^
        del user_data['session_salt']# ^^^^^^^^^^^^^^^^^
        # User logged in. Gibbe (session) cookies
        return json.dumps({
            'session': session_key,
            'userID': userID,
            'details': user_data
        })
    else:
        return '0'

### Here starts the auth-only functions. Make sure you check their session cookies!

# Changes a user's password
@app.route('/change_password', methods=['POST'])
def change_password():
    if request.method == 'POST':
        passw = request.form['passw']
        new_passw = request.form['new_passw']
    else:
        return False
    # Make sure the user is legit
    user = util.auth_request(request)
    if user:
        # check if the old password matches the current password
        # it should be, but just in case they're cookie stealing
        if util.sha512(user['user'] + passw) == user['passw']:
            return util.update_user(
                userID,
                {'passw': util.sha512(user['user'] + new_passw)}
            )
        else:
            return 'incorrect password'
    else:
        return 'invalid user'

# Completely deletes a user's account
@app.route('/delete_account', methods=['POST'])
def delete_account():
    user = util.auth_request(request)
    if user:
        users = get_collection('users', db=util.config['auth_db'])
        users.remove({'_id': ObjectId(userID)}, 1)
    else:
        return "0"

# Takes authentication information and returns user info
@app.route('/authenticate', methods=['POST'])
def authenticate():
    user = util.auth_request(request)
    if user:
        del user['passw']
        del user['session_salt']
        del user['_id']
        return json.dumps(user)
    return "0"

# converts a user/group name into an id
@app.route('/get-uid', methods=['POST'])
def get_uid():
    if not 'user' in request:
        return "0"
    users = util.get_collection('users', db=util.config['auth_db'])
    user = users.find({'user': request['user']})
    return str(user['_id'])

# Updates users' details property.
@app.route('/update-user', methods=['POST'])
def update_user():
    userID = request.form['userID']
    session = request.form['session']
    new_details = request.form['new_details']
    user = util.auth(userID, session)
    if user: #   User is authed, do some stuff
        new_details = json.loads(new_details)
        update_query = {
            "$set": {
                'details': user['details'].update(new_details)
            }
        }
        if util.update_user(user['_id'], update_query):
            return 'success'
        else:
            return 'error'

# SocketIO handlers that allow limited database access to the front end

# Object that represents a socket connection
class Socket:
    def __init__(self, sid, query):
        self.sid = sid
        self.query = query
        self.connected = True
        self.recipient_sender = query['recipient_sender'] \
                if 'recipient_sender' in query else False
        self.where_recipient = query['where_recipient']\
                if 'where_recipient' in query else False,
        self.where_sender = query['where_sender']\
                if 'where_sender' in query else False

    # Emits data to a socket's unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid)

live_sockets = {'senders': {}, 'recipients': {}}
all_listeners = {}

@socketio.on('listen', namespace='/component')
def listen_handler(data):
    request_data = json.loads(data)
    if not util.keys_exist([
                'backlog', 'sender_pair', 'collection', 'recipient_pairs'
            ], request_data) or \
            len(request_data['sender_pair']) != 2:
        emit('error', 'Invalid params')
        return "0"
    # convert usernames to ids if requested
    recipientID_type = request_data['recipientID_type'] if "recipientID_type"\
            in request_data else 'id'
    if recipientID_type == "username":
        # convert recipient usernames to ids
        users = util.get_collection('users', db=util.config['auth_db'])
        for pair in request_data['recipient_pairs']:
            recipient = users.find_one({'user': pair[0]})
            if len(recipient) > 0:
                pair[0] = str(recipient['_id'])
            else:
                emit('error', 'Recipient username not found')
                return "0"
    senderID_type = request_data['senderID_type'] if "senderID_type" \
            in request_data else 'id'
    # send the user backlogs if requested
    if senderID_type == "username":
        # convert sender usernames to ids
        users = util.get_collection('users', db=util.config['auth_db'])
        sender = users.find_one({'user': request_data['sender_pair'][0]})
        if len(sender) > 0:
            request_data['sender_pair'][0] = str(recipient['_id'])
        else:
            emit('error', 'Sender username not found')
            return "0"
    recipient_senders = []
    if 'recipient_senders' in request_data:
        for sender in request_data['recipient_senders']:
            recipient_senders.append(
                str(users.find_one({'user': sender})['_id'])
            )
        request_data['recipient_senders'] = recipient_senders
    # authenticate the request_data (and get a sneaky recipients list)
    auth, recipients = util.auth_listen(request_data)
    if not auth:
        return "0"
    # replace id searches with object id searches
    if 'where_sender' in request_data:
        for clause in request_data['where_sender']:
            if clause == '_id':
                request_data['where_sender'][clause] = ObjectId(
                    request_data['where_sender'][clause]
                )
    if 'where_recipient' in request_data:
        for clause in request_data['where_recipient']:
            if clause == '_id':
                request_data['where_recipient'][clause] = ObjectId(
                    request_data['where_recipient'][clause]
                )
    # send the user backlogs if requested
    if 'backlog' in request_data and request_data['backlog']:
        # get previously sent documents
        senders_log, recipients_log = util.get_documents(
            request_data['sender_pair'][0],
            recipients,
            request_data['collection'],
            time_order=True,
            recipient_senders=recipient_senders if recipient_senders else False,
            recipientID_type=recipientID_type,
            where_recipient=request_data['where_recipient']\
                    if 'where_recipient' in request_data else False,
            where_sender=request_data['where_sender']\
                    if 'where_sender' in request_data else False
        )
        for document in senders_log:
            if document['visible']:
                document_tidy = {
                    'sender': document['sender'],
                    'recipient': document['recipient'],
                    'data': document['data'],
                    'id': str(document['_id']),
                    'ts': document['ts']
                }
                emit('data_sent', document_tidy)
        for document in recipients_log:
            if document['visible']:
                document_tidy = {
                    'sender': document['sender'],
                    'recipient': document['recipient'],
                    'data': document['data'],
                    'id': str(document['_id']),
                    'ts': document['ts']
                }
                emit('data_received', document_tidy)
    # add socket to dict of sockets to keep updated
    # (Choosing speed over memory here)
    # create a socket object to represent us
    socket = Socket(request.sid, request_data)
    # add us to a list of all listener sockets
    live_sockets[socket.sid] = socket
    # make sure the list exists first
    if not request_data['sender_pair'][0] in live_sockets['senders']:
        live_sockets['senders'][request_data['sender_pair'][0]] = []
    # append us to the list of senders subscribed to changes
    live_sockets['senders'][request_data['sender_pair'][0]].append(socket)
    # append us to a list of subscribers for each recipient we're following
    for recipient in recipients:
        if not recipient in live_sockets['recipients']:
            live_sockets['recipients'][recipient] = []
        live_sockets['recipients'][recipient].append(socket)

@socketio.on('send', namespace='/component')
def send_handler(data):
    request = json.loads(data)
    # validate request
    if not 'sender_pair' in request or not 'recipient' in request or \
            not 'collection' in request or not 'data' in request:
        emit('error', 'Invalid Arguments')
        return False
    sender_pair = request['sender_pair']
    recipient = request['recipient']
    collection = request['collection']
    message = request['data']
    if 'senderID_type' in request and request['senderID_type'] == 'username':
        users = util.get_collection('users', db=util.config['auth_db'])
        user = users.find_one({'user': sender_pair[0]})
        if user:
            sender_pair[0] = str(user['_id'])
        else:
            emit('error', 'Sender username does not exist')
            return False
    if 'recipientID_type' in request and request['recipientID_type'] == \
            'username':
        users = util.get_collection('users', db=util.config['auth_db'])
        user = users.find_one({'user': recipient})
        if user:
            recipient = str(user['_id'])
            request['recipient'] = recipient
        else:
            emit('error', 'Recipient username does not exist')
            return False
    # store document
    document = util.send(message, sender_pair, recipient, collection)
    if not document:
        return False
    # send Updates
    document_tidy = {
        'sender': document['sender'],
        'recipient': document['recipient'],
        'data': document['data'],
        'id': str(document['_id']),
        'ts': document['ts']
    }
    if not util.emit_to_relevant_sockets(request, document_tidy, live_sockets):
        emit('error', 'Recipient or sender not found')

@socketio.on('disconnect')
def disconnect():
    # if socket is listening
    if request.sid in all_listeners:
        # remove from listeners
        all_listeners[request.sid].connected = False
        del all_listeners[request.sid]

### Here starts the admin-only functions. Make sure you check user['isAdmin']!



### Here ends the admin-only functions. Make sure you check user['isAdmin']!

### Here ends the auth-only functions. Make sure you check their session cookies!

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True, host='0.0.0.0')
