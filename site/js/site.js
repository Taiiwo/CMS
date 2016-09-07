function Site() {
    // Send a toast notification.
    this.toast = function(message){
        Materialize.toast(message, 4000);
    }
    // Make a call to the api.
    this.api = function(action, data, callback){
        var baseURL = document.location.origin + "/api/1/";
        $.post(
            baseURL + action,
            data,
            callback
        );
    }

    // make a call to a plugins api
    this.plugin_api = function(plugin, action, data, callback) {
        var baseURL = document.location.origin + "/api/plugin/";
        $.post(
            baseURL + [plugin, action].join("/"),
            data,
            callback
        );
    }

    // Turns an element filled with markdown into HTML
    this.markdown = function(id){
        var md = new showdown.Converter();
        var text = $(id).text();
        $(id).html(md.makeHtml(text));
    }
    this.route = function(path){
        document.querySelector('app-router').go(path);
    }
    this.userAuthed = function(){
        // this is not totally secure, but it's impossible to make authenitcated
        // requests without a valid session token
        if (Cookies.get('session') == undefined){
            return false;
        }
        else {
            return true;
        }
    }
    // Adds content to a modal notification.
    // title: the title string
    // text: The html contents of the modal
    // buttons: a list of buttons
    // button[0]: button text
    // button[1]: button colour
    // button[2]: button click callback
    this.notify = function(title, text, buttons){
        $('#notify-modal .modal-footer').empty();
        for (var i in buttons) {
            var button = buttons[i];
            $('#notify-modal .modal-footer').append(
                $('<a/>')
                    .addClass('waves-effect')
                    .addClass('waves-light')
                    .addClass('btn')
                    .addClass(button[1])
                    .text(button[0])
                    .click(button[2])
            );
        }
        $('#notify-modal .modal-content').empty();
        $('#notify-modal .modal-content').append(
            $('<h3/>')
                .text(title),
            $('<p/>')
                .html(text)
        );
    }
    this.modal_open = false;
    this.notify_toggle = function(){
        if (this.modal_open){
            $('#notify-modal').closeModal();
            this.modal_open = false;
        }
        else {
            $('#notify-modal').openModal();
            this.modal_open = true;
        }
    }
    this.auth = function(id, session, callback){
        this.api(
            'authenticate',
            {
                userID: id,
                session, session
            },
            callback
        );
        $(window).trigger('auth_changed');
    }
    // Adds callback to the end of the JS execution flow. Useful for running
    // parallel to ayncronous code with no callback
    this.append_stack = function(callback, num){
        if (typeof num != 'undefined' && num > 0){
            this.append_stack(function(){
                setTimeout(callback, 0);
            }, num - 1);
        }
        else {
            setTimeout(callback, 0);
        }
    }
    this.login = function(username, password, success, fail){
        // if the username matches a email regex, send it as 'email'
        var request = {};
        if (username.match('.*@.*')){
          // username is an email
          request.email = username;
        }
        else {
          request.username = username;
        }
        request.password = password;
        this.api(
            "login",
            request,
            function(data) {
                // if the login was successful
                if (data.success) {
                    // set the session cookies
                    Cookies.set('session', data['session']);
                    Cookies.set('user_id', data['user_id']);
                    // set a global variable for the users details
                    window.user_data = data.user_data;
                    // notify the user that the login was successful.
                    site.toast('Login Successful!');
                    // forward the user to the homepage
                    site.route('/');
                    if (success) {
                        success();
                    }
                    $(window).trigger('auth_changed');
                } else {
                    // whoops, wrong username or password
                    var error_list = [];
                    for (var i in data.errors){
                      var error = data.errors[i];
                      error_list.push(error.name);
                    }
                    console.log("Recieved errors: " + error_list.join(', '));
                    site.toast(data.errors[0].details);
                    if (fail) {
                        fail();
                    }
                }
            }
        );
    }
    this.logout = function(){
        Cookies.remove('session');
        Cookies.remove('user_id');
        user_data = undefined;
        $(window).trigger('auth_changed');
        site.toast('Logged out.');
    }

    // toggles the loading animation
    this.loading = function(toggle){
      if (toggle) {
        $("body").append(
          // loader background
          $('<div>').css({
              position: "absolute", "z-index": "10", width: 100, height: 100,
              left: 0, bottom: 0, top: 0, right: 0, "background-color": "black",
              opacity: "0.2", "border-radius": 20, margin: "auto"
            }).fadeIn('slow').attr('id', 'haze')
          ,
          // materialize loader
          $('<div/>')
            .addClass('preloader-wrapper big active')
            .css({
              position: "absolute", "z-index": 20, top: 0, left: 0, right: 0,
              bottom: 0, margin: "auto"
            }).fadeIn('slow').attr('id', "wheel").append(
              $("<div/>")
                .addClass('spinner-layer spinner-blue')
                .append($('<div/>').addClass('circle-clipper left').append(
                  $('<div/>').addClass('circle')
                )
                ,
                  $('<div/>')
                    .addClass('gap-patch')
                    .append($('<div/>').addClass('circle'))
                ,
                  $('<div/>')
                    .addClass('circle-clipper right')
                    .append($('<div/>').addClass('circle'))
                )
            ,
              $("<div/>")
                .addClass('spinner-layer spinner-red')
                .append($('<div/>').addClass('circle-clipper left').append(
                  $('<div/>').addClass('circle')
                )
                ,
                  $('<div/>')
                    .addClass('gap-patch')
                    .append($('<div/>').addClass('circle'))
                ,
                  $('<div/>')
                    .addClass('circle-clipper right')
                    .append($('<div/>').addClass('circle'))
                  )
              ,
                $("<div/>").addClass('spinner-layer spinner-yellow').append(
                    $('<div/>').addClass('circle-clipper left').append(
                        $('<div/>').addClass('circle')
                    )
                  ,
                    $('<div>').addClass('gap-patch').append(
                      $('<div>').addClass('circle')
                    )
                  ,
                    $('<div/>')
                      .addClass('circle-clipper right')
                      .append(
                        $('<div/>')
                          .addClass('circle')
                      )
                  )
              ,
                $("<div/>")
                  .addClass('spinner-layer spinner-green').append(
                    $('<div/>').addClass('circle-clipper left').append(
                      $('<div/>').addClass('circle')
                    )
                  ,
                    $('<div/>').addClass('gap-patch').append(
                        $('<div/>').addClass('circle')
                    )
                  ,
                    $('<div/>').addClass('circle-clipper right').append(
                        $('<div/>').addClass('circle')
                    )
                  )
              )
        );
        return true;
      }
      $('body > #haze').fadeOut('slow', function(){
        $('body > #haze').remove();
      });
      $('body > #wheel').fadeOut('slow', function(){
        $('body > #wheel').remove();
      });
      return false;
    }
}
window.$$ = document.querySelector;
var site = new Site();
if (Cookies.get('session') && Cookies.get('user_id')){
    // user has cookies, auth them
    site.auth(Cookies.get('user_id'), Cookies.get('session'), function(data){
        if (data.success) {
            window.user_data = data.user_data;
        } else {
            site.toast("Session Expired.");
            Cookies.remove('session');
            Cookies.remove('user_id');
        }
    });
}
