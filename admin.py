#!/bin/env python3
import os
import sys
import json
from taiicms import util
from taiicms import config

util = util.Util(config['mongo'])

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
        user = users.find_one({'username': arg[0]})
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
            users = util.get_collection('usersname', db=util.config['auth_db'])
            user_exists = users.find({'username': arg[0]}).count() > 0
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
            username = arg[0].lower()
            datachest = arg[1]
            # get user id
            user = util.get_collection(
                'users', db=util.config['auth_db']
            ).find_one(
                {'username': username}
            )
            if not user:
                quit('[E] User does not exist')
            userID = str(user['_id'])
            # get datachest session
            datachest = util.get_collection(
                'users', db=util.config['auth_db']
            ).find_one(
                {'username': datachest}
            )
            if not datachest:
                quit("[E] Datachest does not exist")
            datachest_session = util.sha512(
                datachest['session_salt'] + datachest['passw']
            )
            util.update_user(userID, {
                "$set": {
                    'datachests.' + datachest['username']: [
                        datachest['username'],
                        datachest_session
                    ]
                }
            })
            quit("[-] User added to datachest")

if command == "plugins":
    if sub_command == "install":
        # grab the top level of dirs in the plugins directory
        cwd = os.path.dirname(os.path.realpath(__file__))
        plugin_dir = cwd + '/taiicms/static/plugins/'
        for plugin in next(os.walk(plugin_dir))[1]:
            location = plugin_dir + plugin
            # build component import element
            html_import = util.generate_import_html(plugin)
            # if plugin not in plugin-components.html
            plugin_components = \
                    "/taiicms/static/components/plugin-components.html"
            if not html_import in open(cwd + plugin_components).read():
                # add components.html to be imported
                open(cwd + plugin_components, 'a').write(html_import)
                # create specified datachests in datachests.json
                if os.path.isfile(location + "/datachests.json"):
                    for chest in json.load(open(location + "/datachests.json")):
                        util.new_datachest(chest['name'], chest['public'])
                # add main.py.daily() to the daily cron job
                # add main.py.auth_*() to the authentication api

    if sub_command == "remove":
        if len(arg) < 1:
            quit("[E] Requires one argument: Plugin to remove")
        plugin = arg[0]
        html_import = util.generate_import_html(plugin)
        plugin_components = \
                "/taiicms/static/components/plugin-components.html"
        cwd = os.path.dirname(os.path.realpath(__file__))
        read = open(cwd + plugin_components).read()
        write = read.replace(html_import, "")
        open(cwd + plugin_components, 'w').write(write)
