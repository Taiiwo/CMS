import os
import sys
from lib import util

util = util.Util()

command = sub_command = False
arg = []
if len(sys.argv) > 1:
    # main command
    command = sys.argv[1]
if len(sys.argv) > 2:
    # command for the above command
    sub_command = sys.argv[2]
if len(sys.argv) > 3:
    # arguments to sub_command
    arg = sys.argv[3:]

if not command:
    # Maybe print help here
    quit('[E] Requires atleast one command')

if command == "admin":
    if sub_command and sub_command == "add":
        if len(arg) < 1:
            quit(
                "[E] Requires one ARG: The username of the user you want to\
                be an admin"
            )
        users = util.get_collection('users', db=util.config['auth_db'])
        # find user
        user = users.find_one({'user': arg[0]})
        if not user:
            quit("[E] User does not exist")
        util.update_user(user['_id'], {"$set": {'is_admin': True}})
        quit("[-] User given admin privs")

if command == "datachest":
        # Creates a new datachest
        if sub_command and sub_command == 'create':
            if len(arg) < 1:
                quit("[E] Requires one argument: datachest name")
            # check if chest with that name exists
            users = util.get_collection('users', db=util.config['auth_db'])
            user_exists = users.find({'user': arg[0]}).count() > 0
            if user_exists:
                quit('[E] User exists')
            public = False
            if len(arg) > 1:
                if arg[1] == "public":
                    public = True
            session = util.new_datachest(arg[0], public=public)
            print("[-] Datachest created with session: %s" % session)

        # Adds a user to a datachest
        if sub_command and sub_command == 'invite':
            if len(arg) < 2:
                quit(
                    '''[E] Requires two arguments: Username of user to add, then
                    the name of the datachest'''
                )
            username = arg[0]
            datachest = arg[1]
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
