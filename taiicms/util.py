import os
import json
import time
import pymongo
import hashlib
from bson.objectid import ObjectId

class Util:
    def __init__(self, config):
        self.config = config

        # Connect to MongoDB
        self.connect()
        try:
            self.mongo.server_info()  # force a test of server connection
        except pymongo.errors.ServerSelectionTimeoutError:
            print("Could not connect to mongodb at %s:%s.\nMake sure the mongo server is running and the TaiiCMS config file is correct." % [config["host"], config["port"]])
            raise SystemExit()
        self.db = self.mongo[self.config['default_db']]

    def connect(self):
        self.mongo = pymongo.MongoClient(
            self.config['host'],
            self.config['port']
        )

    # Shorthand for sha512 sum
    def sha512(self, data):
        if type(data) is str:
            return hashlib.sha512(data.encode('utf-8')).hexdigest()
        elif type(data) is bytes:
            return hashlib.sha512(data).hexdigest()

    def auth(self, user_id, session):
        # get user deets
        db = self.get_collection('users', db=self.config['auth_db'])
        # find user in db
        user = db.find_one({'_id': ObjectId(user_id)})
        # check if the session is legit
        if user and session == self.sha512(
                (user['session_salt'] + user['passw']).encode('utf-8')
                ):
            return user
        else:
            return False

    def auth_request(self, request):
        try:
            session = request.form['session']
            user_id = request.form['user_id']
        except:
            return False

        print(session, user_id)

        return self.auth(user_id, session)

    # Authenticates a listen request
    def auth_listen(self, request):
        if not self.auth(request['sender_pair'][0], request['sender_pair'][1]):
            return False, False
        recipients = []
        for recipient in request['recipient_pairs']:
            if not self.auth(recipient[0], recipient[1]):
                return False, False
            recipients.append(recipient[0])
        return True, recipients

    def update_user(self, userID, update):
        users = self.get_collection('users', db=self.config['auth_db'])
        userID = ObjectId(userID) if type(userID) != ObjectId else userID
        return users.update({
            "_id": userID
        },
            update
        )

    # emits document to all sockets subscibed to request
    def emit_to_relevant_sockets(self, request, document, socket_subscribers):
        if request['sender_pair'][0] in socket_subscribers['senders']:
            for socket in socket_subscribers['senders'][request['sender_pair'][0]]:
                # check for dead sockets
                if socket.connected == False:
                    socket_subscribers['senders'][
                        request['sender_pair'][0]
                    ].remove(socket)
                matches = True
                if socket.where_recipient != (False,):
                    for clause in socket.where_recipient:
                        if document[clause] != socket.where_recipient[clause]:
                            matches = False
                if matches:
                    socket.emit('data_sent', document)
        if 'recipient' in request and request['recipient']\
                in socket_subscribers['recipients']:
            for socket in \
                    socket_subscribers['recipients'][request['recipient']]:
                # check for dead sockets
                if socket.connected == False:
                    socket_subscribers['recipients'][
                        request['recipient']
                    ].remove(socket)
                matches = True
                if socket.where_sender != (False,):
                    for clause in socket.where_sender:
                        if document[clause] != socket.where_sender[clause]:
                            matches = False
                if socket.recipient_sender\
                        and document.sender == socket.recipient_sender:
                    if matches:
                        socket.emit('data_received', document)
                elif not socket.recipient_sender:
                    if matches:
                        socket.emit('data_received', document)
        return True

    # Stores information in the specified collection
    def store(self, data, collection, visible=False, db=False):
        collection = self.get_collection(collection, db=db)
        # Note: If the user stores data with key='visible', it will be
        # overwritten here for security reasons.
        # Note: Documents with visible=True can be read by the front end
        # which includes the user! So no password hashes. No sensitive info
        # unless it's their own.
        data['visible'] = visible
        return collection.insert_one(data).inserted_id

    ### This section of the library is for generating documents that can   ###
    ### only be read by the desired recipient, using networking, not       ###
    ### cryptography. Note: A recipient is not limited to a person, and    ###
    ### may also be, say, a channel, room, or group. Anything that         ###
    ### represents something that has access to documents that not         ###
    ### _everyone_ should have access to.                                  ###

    # Adds data to a collection, but so that only the recipients can recieve
    # it using the recieve_stream method
    def send(self, data, sender_pair, recipient, collection):
        # authenticate the sender
        sender = self.auth(sender_pair[0], sender_pair[1])
        # die if the sender was not found
        if not sender: return False
        data = {
            "data": data,
            "sender": sender_pair[0],
            "recipient": recipient,
            "ts": time.time()
        }
        # store the message
        self.store(
            data,
            collection,
            visible=True
        )
        return data

    def update_document(self, document, sender_pair, document_id, collection):
        # authenticate the sender
        sender = self.auth(sender_pair[0], sender_pair[1])
        # die if the sender was not found
        if not sender: return False
        # get the old data
        cursor = self.get_collection(collection)
        old_document = cursor.find_one({
            "_id": ObjectId(document_id)
        })
        document_update = {
            "$set": {
                "data": document,
                "ts": time.time()
            },
            "$push": {
                "revisions": old_document['data']
            }
        }
        new_document = cursor.update_one(old_document, document_update)
        print (new_document)
        return cursor.find_one({
            "_id": ObjectId(document_id)
        })

    def get_collection(self, name, db=False):# Gets a collection from mongo-db
        if db:
            dbc = self.mongo[db]
        else:
            dbc = self.db
        return dbc[name]

    # Grabs a cursor for messages directed to a list of recipients
    # To call this method, you must be the sender, and
    # This is so that nobody can request messages that they are not cleared to
    # see. Note: By "being the recipients", that could either mean that you
    # were the individual recipient, or that you were the a member of that
    # channel or group etc.
    def get_documents(self, sender, recipients, collection, time_order=False,
                        recipient_senders=False, recipientID_type='id',
                        where_recipient=False, where_sender=False):
        # return a stream of messages directed towards the keys specified
        sender_query = {'sender': str(sender)}
        if where_sender:
            sender_query.update(where_sender)
        senders = self.get_collection(collection).find(sender_query)
        # Specify recipient sender to only receive documents from a set of
        # senders
        if recipient_senders:
            query = {
                'recipient': {"$in": recipients},
                'sender': {"$in": recipient_senders}
            }
        else:
            query = {'recipient': {"$in": recipients}}
        if where_recipient:
            query.update(where_recipient)
        recipients = self.get_collection(collection).find(query)
        if time_order:
            for col in (senders, recipients):
                col.sort([('ts', pymongo.ASCENDING)])
        return senders, recipients

    # Makes a new datachest account. A datachest is a user that represents a
    # storage space for multiple users.
    # Example use:
    # Group to user/group: Send a message as group with user/group with group as
    # the sender and recipient as the recipient
    # Group/user to public: Same as above but the recipient is the public group
    # Private group message / private info: Group/user sends message to itsself.
    # A group member signs their message to prove ownership if needed.
    def new_datachest(self, name, public=False):
        # build datachest document
        datachest = {
            "username": name,
            "passw": '' if public else self.sha512(os.urandom(512)),
            "session_salt": '' if public else self.sha512(os.urandom(512)),
            "is_datachest": True
        }
        # build an auth key
        session_key = self.sha512(datachest['session_salt'] + datachest['passw'])
        # check if DataChest exists
        users = self.get_collection('users', db=self.config['auth_db'])
        if users.find_one({'username': datachest['username']}):
            return False
        # store document, creating the datachest user
        self.store(
            datachest,
            "users",
            visible=False,
            db=self.config['auth_db']
        )
        return session_key

    def keys_exist(self, keys, dicti):
        for key in keys:
            if key not in dicti:
                return False
        return True

    def generate_import_html(self, plugin_name):
        return '<!-- %s -->\n' % plugin_name + \
            '<link ' + \
            'rel="import" ' + \
            'href="../plugins/%s/components.html"' % plugin_name + \
            ' />\n' + \
            '<!-- /%s -->\n' % plugin_name
