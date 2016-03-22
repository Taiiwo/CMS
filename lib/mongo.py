import pymongo
import util
import time
import websockets
import asyncio

util = util.Util()
# Class representing the mongodb connection
class MongoConnection:

    db = util.db
    # Stores information in the specified collection
    def store(self, data, collection, visible=False):
        collection = util.get_collection(collection)
        # Note: If the user stores data with key='visible', it will be
        # overwritten here for security reasons.
        # Note: Documents with visible=True can be read by the front end
        # which includes the user! So no password hashes. No sensitive info
        # unless it's their own.
        data['visible'] = visible
        collection.insert(data)


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
        sender = util.auth(sender_pair[0], sender_pair[1])
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

    # Grabs a stream for messages directed to a list of recipients
    # To call this method, you must be the sender, and all of the recipients.
    # This is so that nobody can request messages that they are not cleared to
    # see. Note: By "being the recipients", that could either mean that you
    # were the individual recipient, or that you were the a member of that
    # channel or group etc.
    def get_documents(self, sender, recipients, collection):
        # return a stream of messages directed towards the keys specified
        senders = self.db[collection].find(
            {'sender': str(sender)}
        )
        recipients = self.db[collection].find(
            {'recipient': {"$in": recipients}}
        )
        return senders, recipients
