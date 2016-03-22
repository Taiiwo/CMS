import pymongo
import json
import hashlib
from bson.objectid import ObjectId

class Util:
    def __init__(self):
        # Read config
        self.config = json.load(open('config.json', 'r'))
        # Connect to MongoDB
        self.mongo = pymongo.MongoClient(self.config['mongo_host'], self.config['mongo_port'])
        self.db = self.mongo[self.config['mongo_database']]

    # Shorthand for sha512 sum
    def sha512(self, data):
        if type(data) is str:
            return hashlib.sha512(data.encode('utf-8')).hexdigest()
        elif type(data) is bytes:
            return hashlib.sha512(data).hexdigest()

    def get_collection(self, name, db=False):# Gets a collection from mongo-db
        if db:
            dbc = self.mongo[db]
        else:
            dbc = self.db
        return dbc[name]

    def auth(self, userID, session):
        # get user deets
        db = self.get_collection('users')
        # find user in db
        user = db.find_one({'_id': ObjectId(userID)})
        # check if the session is legit
        if user and session == self.sha512(
                (user['session_salt'] + user['passw']).encode('utf-8')
                ):
            return user
        else:
            return False

    def auth_request(self, request):
        if not "session" in request.form or not "userID" in request.form:
            return False
        session = request.form['session']
        userID = request.form['userID']
        return self.auth(userID, session)

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
        users = self.get_collection('users')
        userID = ObjectId(userID) if type(userID) != ObjectId else userID
        return users.update({
            "_id": userID
        },
        {
            "$set": update
        })

    # emits document to all sockets subscibed to request
    def emit_to_relevant_sockets(self, request, document, socket_subscribers):
        request_key = json.dumps(request)
        for socket in socket_subscribers['senders'][request['sender_pair'][0]]:
            # check for dead sockets
            if socket.connected == False:
                socket_subscribers['senders'][
                    request['sender_pair'][0]
                ].remove(socket)
            socket.emit('data_sent', document)
        for socket in socket_subscribers['recipients'][request['recipient']]:
            # check for dead sockets
            if socket.connected == False:
                socket_subscribers['senders'][
                    request['sender_pair'][0]
                ].remove(socket)
            socket.emit('data_received', document)
