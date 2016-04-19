import os
import sys
from lib import util

util = util.Util()

if sys.argv[1] == "admin":
    if len(sys.argv) > 2:
        command = sys.argv[2]
        if command == "add":
            if len(sys.argv) < 4:
                quit(
                    "[E] Requires one ARG: The username of the user you want to\
                    be an admin"
                )
            users = util.get_collection('users', db=util.config['auth_db'])
            # find user
            user = users.find_one({'user': sys.argv[3]})
            if not user:
                quit("[E] User does not exist")
            util.update_user(user['_id'], {"$set": {'is_admin': True}})
            quit("[-] User given admin privs")

if sys.argv[1] == "datachest":
    if len(sys.argv) > 2:
        command = sys.argv[2]

        # Creates a new datachest
        if command == 'create':
            if len(sys.argv) < 4:
                quit("[E] Requires one argument: datachest name")
            # check if chest with that name exists
            users = util.get_collection('users', db=util.config['auth_db'])
            user_exists = users.find({'user': sys.argv[3]}).count() > 0
            if user_exists:
                quit('[E] User exists')
            public = False
            if len(sys.argv) > 4:
                if sys.argv[4] == "public":
                    public = True
            session = util.new_datachest(sys.argv[3], public=public)
            print("[-] Datachest created with session: %s" % session)

        # Adds a user to a datachest
        if command == 'invite':
            if len(sys.argv) < 5:
                quit(
                    '''[E] Requires two arguments: Username of user to add, then
                    the name of the datachest'''
                )
            username = sys.argv[3]
            datachest = sys.argv[4]
            # get user id
            user = util.get_collection(
                'users', db=util.config['auth_db']
            ).find_one(
                {'user': username}
            )
            if not user:
                quit('[E] User does not exist')
            userID = str(user['_id'])
            # get datachest session
            datachest = util.get_collection(
                'users', db=util.config['auth_db']
            ).find_one(
                {'user': datachest}
            )
            if not datachest:
                quit("[E] Datachest does not exist")
            datachest_session = util.sha512(
                datachest['session_salt'] + datachest['passw']
            )
            util.update_user(userID, {
                "$set": {
                    'datachests.' + datachest['user']: [
                        datachest['user'],
                        datachest_session
                    ]
                }
            })
            quit("[-] User added to datachest")
