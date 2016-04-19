TaiiCMS - The Non-Standard Content Management System
====================================================

TaiiCMS is a content management system written using `WSGI` and
`mongodb` in Python. It provides a simple way to manage and develop a
webpage. TaiiCMS attempts to provide the basic features required by most
projects in a non-intrusive, all front end way.

TaiiCMS relies on 3 main procedures. The Authentication API, the
Component API (previously known as real time mongo), and the Pagination
system.

The Authentication API
----------------------

The Authentication API provides an AJAX/JSON interface to
authentication. Use the Authentication API to register users, log them
in, and look up other users.

Pagination
----------

Traditional CMSs save pages inside a database, allowing it to be
retrieved using templating systems. TaiiCMS stores none of your pages in
databases and instead stores it in traditional HTML files. The
distiction between the method used by TaiiCMS and the traditional method
of storing content inside individual files is that TaiiCMS stores it's
content within webcomponent-compatible elements using the Polymer
framework, then lazy-loads them using app-router.

Component API
-------------

Features in TaiiCMS are added with Polymer Webcomponents in modular
fasion. The component API is another javascript API inline with the
Authenticaion API that can be used inside these Polymer Elements giving
them access to central database in real time, all from the front end!

The security conscious amung you will be wondering if a database that is
interfaced with entirely on the front end is secure. The Component API
gives database records (documents) only to those who are authenticated
to see them. Each document has a sender and a recipient field, and you
may only see the document if you are able to authenticate as one of
them.

In order to make this layout more flexible, DataChests were created. A
DataChest is a special type of user that cannot be logged into. The
one-time authentication information is given out to a group of users
that are permitted to access the DataChest. A DataChest can be the
sender or recipient of a document, and an optional author field will be
verified if submitted (Not implemented yet). All users are added to the
'Public' DataChest by default, allowing for public and/or anonymous
broadcasts.

How to Use TaiiCMS
------------------

### Configuration

Configuration options for mongodb can be found in `config.json`. Other
than that, the configuration of modules are added along with their
inclusion on the desired page.

### Creating or Editing a Page

In order to edit or create a page, one must do so within the `/pages`
directory. Here you must construct a valid polymer element that will be
displayed in the main content section of the page.

You must then add an element within the `<app-router>` section of
`index.html` that represents your page. Then you will be able to use
`site.route('/desination');` to navigate to your new page, or simply
navigate to `#/desitnation` in the URI.

More complex routes are possible. It is possible to pass attributes to
the page's Polymer element via the route path, allowing you to have
effective dynamic URLs. More info on this can be found in the app-router
documentation: [Data Binding](https://erikringsmuth.github.io/app-router/#/databinding/1337?queryParam1=Routing%20with%20Web%20Components!)

Tutorials
---------

### Creating a new page

Add the following page skeleton to a new file inside the `/pages`
directory; or you can simply duplicate the template page:
`/pages/template-page.html`.

```html
<dom-module id="template-page">
    <template>
        <style>
            /*
            CSS goes here
            */
        </style>
        <div class="container">
            <!--
            Page content goes here
            -->
        </div>
    </template>
</dom-module>
<script>
    Polymer({
        is: "template-page",
        attached: function() {
            // JavaScript goes here
        }
    });
</script>
```

To make your page accessible via URL, add the following to the
`<app-router>` section of `index.html`:

```html
<app-route path="/desired/path" import="pages/my-page.html"></app-route>
```

Where "/desired/path" is your desired path, and "my-page.html" is the
name of your page. You can now visit your new page by going to
`localhost:8080/#/desired/path`. The `#` is important.

### Interfacing with TaiiCMS with Your New Page

The JavaScript library `js/site.js` creates the `site` object. `site`
controls many of the features of TaiiCMS, and it is recommended that it
is kept, as long as you are still using TaiiCMS's Features.

The JavaScript library 'js/rtm.js' creates the 'RTM' object, and allows
you to make connections to the Component API.
