TaiiCMS - The Non-Standard Content Management System
====================================================

TaiiCMS is a content management system written for `WSGI` and `mongodb`
in Python. It provides a simple way to manage and develop a webpage.
TaiiCMS attempts to provide the basic features required by most projects
in a non-intrusive way.

TaiiCMS is broken up into two parts: API, and pagination.

The API
-------

The API services included within TaiiCMS provide a simple JSON interface
to the front end, allowing each page to execute server-side functions,
as simply as possible. By using this method for authentication, it is
possible to completely redesign your site, while still allowing the
front end to authenticate and perform actions on the user. The design
that comes with TaiiCMS is simply a material design base.

Pagination
----------

This is where TaiiCMS becomes non-standard. Traditional CMSs save
content inside a database, allowing it to be retrieved using templating
systems. TaiiCMS stores none of your content in databases and instead
stores it in traditional HTML files. The distiction between the method
used by TaiiCMS and the traditional method of storing content inside
individual files is that TaiiCMS stores it's content within
webcomponent-compatible elements using the Polymer framework.

The Polymer framework allows developers to import Polymer Elements in
the form of HTML files, and place them on the page. TaiiCMS uses a
combination of Polymer Elements to load pages from the `/pages`
directory, and switches between them using JavaScript.

How to Use TaiiCMS
------------------

### Configuration

While TaiiCMS is widely configurable in that it is open to modification,
any configuration options provided by the default installation can be
found in `js/main.js`, for front-end configuration; and `config.py`, for
configuration of the back-end. (Although no options currently exist)

### Creating or Editing a Page

In order to edit or create a page, one must do so within the `/pages`
directory. Here you must construct a valid polymer element that will be
displayed in the main content section of the page.

If you are creating a new page, you will need to import and include it
within `index.html`. You must add an element within the `<app-router>`
section of `index.html`. Then you will be able to use
`site.router('/desination');` to navigate to your new page, or simply
navigate to `#/desitnation` in the URI.

More complex routes are possible. It is possible to pass attributes to
the page's Polymer element via the route path, allowing you to have
effective dynamic URLs. More info on this can be found in the app-router
documentation: [Data Binding](https://erikringsmuth.github.io/app-router/#/databinding/1337?queryParam1=Routing%20with%20Web%20Components!)

### The API

The JavaScript library `js/site.js` creates the `site` object. `site`
controls many of the features of TaiiCMS, and it is recommended that it
is kept, as long as you are still using TaiiCMS's Features.

`site.js` has the method `api`, allowing you to make shorthand AJAX
requests to the Python backend.
