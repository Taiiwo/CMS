TaiiCMS - The Non-Standard Content Management System
====================================================

TaiiCMS is a content management system written using `flask` and
`mongodb` in Python and JavaScript. It provides a simple way to develop and manage a
webpage. TaiiCMS attempts to provide the basic features required by most
projects in a non-intrusive, all front end way.

TaiiCMS is split into the core, and the plugins. The plugins add features and
functionality to you webpage, whereas the core provide the procedures for
loading the plugins efficiently.

Plugins
-------
If you're interested in adding features to TaiiCMS, you're most likely going to
be developing them in the form of plugins. Each plugin has it's own folder in
the `/plugins` folder, and within it are the various files that provide the
functionality to your plugin. Below is a breakdown of each file, and what it is
used for. Note: The only required file is the `plugin.json` file.

## File list
### plugins.json
This file represents your plugins settings, and is how you tell the core how to
use your plugin in a site. The file is a JSON formatted text file. Below is each
key, and the purpose of it's value.

#### "author", "description", "website"
These are all meta tags that display who made the plugin, what it does, and
where it came from.

#### "depends"
This key's value is an array of the string names of each plugin that is required
for the plugin to function properly.

#### "conflicts"
This key's value is an array of the string names of each plugin that is known to
break this plugin. As such, the plugin will not be installed if any of it's
conflicts are installed prior.

#### "pages"
Pages is the most important key. It is what the core uses to generate your site
routes. The value is an object of objects. The key is the page route. The value
must contain either "element" or "file_path". "element" defines the name of the
element that will be loaded at the route. "file_path" defines the file path of
an element to load, and place at the route.

### default_config.json
This file contains a JSON object of settings that will be appended to the main
config.json in `/`. You can use this for the definition of API keys and other
such sensitive information.

### components.html
This file can be used to import scripts elements and CSS globally. Use it
sparingly. Note: You can import scripts elements and CSS at the top of your
Polymer elements.

### \__init__.py
This file should be avoided as much as possible. It should only be used if there
is no way to complete the task using JavaScript and the existing APIs provided.
Note: It is entirely possible to request and store data using the existing APIs.
The only reason to use this file is if you're dealing with some other method of
authentication, such as some kind of external exchange (money, bitcoin, etc).

## Polymer Elements - HTML format explained
TaiiCMS uses a webcomponent library called Polymer. Polymer allows you to create
your own HTML elements that will be expanded when they are 'attached' to the
page. TaiiCMS uses these elements to load in pages dynamically.

### Example:

```html
<!-- import an element from the layout plugin -->
<link rel="import" href="../layout/json-to-form.html" />
<!-- It is mandatory to change this id to the name that is defined in
plugin.json! Don't forget! Don't forget the other one, too! (below) -->
<dom-module id="element-name">
    <template>
        <style>
            /*
              We can put our own custom CSS here. It is better to use this than
              an external file.
            */
        </style>
        <div class="container">
          <!-- This element takes a JSON object and turns it into a form -->
          <json-to-form form-title="Enter Some Information!">
            {
              "first_name": "Please enter your first name",
              "last_name": "Please enter your last name",
              "email_updates": true
            }
          </json-to-form>
        </div>
    </template>
</dom-module>
<script>
    // here we define our polymer object
    Polymer({
        // It is mandatory to change this to the name that is defined in
        // plugin.json! Don't forget! Don't forget the other one, too! (above)
        is: "element-name",
        // this is how you define public methods for our element so people can
        // call them just like we call `form.serialize()`
        our_public_method: function(string){
          console.log(string);
        },
        // This is our main JavaScript block. All the JavaScript here will
        // execute only when all the HTML above has been loaded to the page.
        // `this` refers to our polymer element, so we can call our own methods
        // with `this.our_public_method("test")`
        attached: function() {
          // make sure the user is logged in
          if (!site.userAuthed()) {
            // if the user isn't logged in, send them to the login page
            site.route('/login');
            // send the user a message to show why they were redirected
            site.toast('Authentication required');
            // stop execution of the current element
            return false;
          }
          // select the form and store it
          var form = $('json-to-form')[0];
          // set the onsubmit callback
          form.onsubmit = function(event){
            // place the information in a database
            rtm.send({
                // choose the collection to store the information
                collection: 'random_information',
                // specify that we're sending usernames, not user IDs
                senderID_type: 'username',
                recipientID_type: 'username',
                // send our keys to authenticate as a public user
                sender_pair: user_data.datachests['Public'],
                // send it so that only editors can read it
                recipient: "Editors",
                // serialize the form data into a json object
                data: form.serialize()
            });
          };
        }
    });
</script>
```

The above code will generate a page that looks something like this:
![Screenshot](http://i.imgur.com/KmRw3Tm.png)

Provided APIs
-------------
TaiiCMS provides several HTTP APIs that can be used from your elements via AJAX,
or through our complete set of API wrappers.

## site.js
`site.js` creates the global `site` object, and can be used to access various
utility functions, as well as to interface with the APIs. Below is a
comprehensive list of all methods of the `site` object, and it's function.

### site.toast(string)
Creates a subtle popup notification that displays a short message for 4 seconds.

### site.api(action:string, data:object, callback:function)
A shorthand function for sending an AJAX function to the back end. See the
API documentation for more information on what possible "methods" are available.

### site.markdown(selector:string)
Changes the content of the selected element from markdown text to formatted
HTML. Note: You can use use the taii-markdown element from the layout plugin.

### site.route(path:string)
Redirects the user to the route at `path`.

### site.userAuthed()
Returns `true` if the user is authed, and `false` if the user has not yet
authenitcated. Note: API requests that require authentication will simply not
work without it. This function is just to stop the user from getting access
denied responses.

### site.notify(title:string, body:html, buttons:array[array[text:string, colour:string, callback:function], ...])
Used to setup a modal notification. Think of it like a prettier `prompt` from
JS. The modal uses `title` as the title, `body` as the body of the modal, and
each button in the `buttons` array will be placed at the bottom. Where `button`
is each element of `buttons`, `button[0]` is the text inside the button,
`button[1]` is colour of the button(Just applies it as a class and Materialize
does the rest), and `button[2]` is the callback function for when the button is
clicked.

### site.notify_toggle()
Toggles the visibility of the modal defined above

### site.auth(userID:string, session:string, callback:function)
Authenticates the user with the core and sends the user information to the
callback function.

### site.append_stack(callback:function, num_times:number)
Gets around some JavaScript quirks for when something is not loading because
other elements on the page haven't finished loading yet. takes the supplied
function and appends it to the end of the JavaScript execution stack
(JavaScript runs in a single thread). Num_times, is the number of times you want
it to stick it to the end of the stack. If you're using this, you're probably
doing something wrong, it's there if you really need it.

### site.login(username:string, password:string, success:function, fail:function)
Uses the core APIs to authenticate a user with no current session. Executes
`success` on success and `fail` on fail.

### site.logout()
logs out the current user from their session and destroys all relevant cookies.

## rtm.js

RTM stands for "real-time-mongo", and is a document storage method that allows
you to not only get constantly updated streams of data instead of stagnant
static responses, but it also gives you full confidence that you data will not
be seen by anyone to is not authenticated to do so. As each user only has
information that they are authenticated to see, it is fully compatible with a
P2P style distribution, where new content can be echoed from user to user
instead of having a bajillion connection streams to the DB.

As for using RTM, it's quite simple. `rtm.js` defines the global `RTM` class.
You can instantiate this class to begin your session with the server.

Each document in the database lists the sender and recipient of the document,
and only those who can authenticate as either of these can read the information.

### rtm.listen(conf{collection:string, sender_pair:array[username:string, session:string], recipient_pairs:array[array[username:string, session:string],...], backlog:bool})
Starts listening to the specified stream of data. `collection` is the collection
to read from, `sender_pair` is the username and session token of the sender(you),
`recipient_pairs` is an array of arrays of usernames and session IDs of the recipients that you are claiming to be.

### rtm.send(collection:string, sender_pair:array, recipient:string, data:\*)
Sends data to a specified recipient, posting in `collection`.
