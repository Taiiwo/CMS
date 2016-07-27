import os
import json
import time
import pymongo
import hashlib
import mongoquery
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

    def update_user(self, userID, update):
        users = self.get_collection('users', db=self.config['auth_db'])
        userID = ObjectId(userID) if type(userID) != ObjectId else userID
        return users.update({
            "_id": userID
        },
            update
        )

    # emits document to all sockets subscibed to request
    def emit_to_relevant_sockets(self, request, document, live_sockets):
        if not request['collection'] in live_sockets\
                or len(live_sockets[request['collection']]) < 1:
            return False
        # for each listener in this collection
        for socket in live_sockets[request['collection']]:
            # remove disconnected sockets
            if not socket.connected:
                live_sockets[request['collection']].remove(socket)
                continue
            # is the listener is waiting for sender/recipient of document
            if mongoquery.Query({"$or": [{"sender": {"$in": socket.ids}},
                                         {"recipient": {"$in": socket.ids}}
                    ]}).match(document):
                # check user defined query
                if mongoquery.Query(socket.where).match(document):
                    # document matches this users specifications. Send document
                    socket.emit("data", document)

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
    def send(self, data, sender_id, recipient_id, collection):
        data = {
            "data": data,
            "sender": sender_id,
            "recipient": recipient_id,
            "ts": time.time()
        }
        # store the message
        self.store(
            data,
            collection,
            visible=True
        )
        return data

    def update_document(self, data, document_id, collection):
        # get the old data
        cursor = self.get_collection(collection)
        old_document = cursor.find_one({
            "_id": ObjectId(document_id)
        })
        document_update = {
            "$set": {
                "data": data,
                "ts": time.time()
            },
            "$push": {
                "revisions": old_document
            }
        }
        new_document = cursor.update_one({
          "_id": ObjectId(document_id)
        }, document_update)
        return cursor.find_one({
            "_id": ObjectId(document_id)
        })
    
    def escape_user_query(self, query):
        users = False
        if isinstance(query, list) or isinstance(query, tuple):
            for i in range(len(query)):
                query[i] = self.escape_user_query(query[i])
        elif isinstance(query, dict):
            for key, value in query.items():
                if key == "$uid_of":
                    if not users:
                        users = self.get_collection("users",
                                                    db=self.config['auth_db'])
                    uid = str(users.find_one({"username": value})['_id'])
                    return uid
                elif key == "$oid":
                    return ObjectId(value)
                else:
                    query[key] = self.escape_user_query(query[key])

        return query

    def get_collection(self, name, db=False):# Gets a collection from mongo-db
        if db:
            dbc = self.mongo[db]
        else:
            dbc = self.db
        return dbc[name]

    # Grabs a cursor for messages directed to or from a dict of auths
    # This restriction is so that nobody can request messages that they are
    # not authed to see. 
    def get_documents(self, auths, collection, time_order=False, where=False):
        ids = list(auth[0] for auth in auths)
        # return a stream of messages directed towards the keys specified
        query = {"$and": [
            {"$or": [
                {"sender": {"$in": ids}},
                {"recipient": {"$in": ids}}
            ]}
        ]}
        if where:
            # Note: Appending an and means that no matter what where clause
            # the user adds contains, it will always have to pass the first
            # test also
            query["$and"].append(where)
        return self.get_collection(collection).find(query)

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
    
    def get_uid(self, username):
        users = self.get_collection('users', db=self.config['auth_db'])
        return str(users.find_one({'username': username})['_id'])

    def generate_import_html(self, plugin_name):
        return '<!-- %s -->\n' % plugin_name + \
            '<link ' + \
            'rel="import" ' + \
            'href="../plugins/%s/components.html"' % plugin_name + \
            ' />\n' + \
            '<!-- /%s -->\n' % plugin_name
