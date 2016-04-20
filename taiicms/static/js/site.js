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
    this.login = function(user, passw, success, fail){
        this.api(
            "login",
            {
                user: user,
                passw: passw
            },
            function(data) {
                // if the login was successful
                if (data != "0"){
                    // parse the user data
                    data = JSON.parse(data);
                    // set the session cookies
                    Cookies.set('session', data['session']);
                    Cookies.set('userID', data['userID']);
                    // set a global variable for the users details
                    window.user_data = data.details;
                    // notify the user that the login was successful.
                    site.toast('Login Successful!');
                    // forward the user to the homepage
                    site.route('/');
                    if (typeof success != 'undefined'){
                        success();
                    }
                    $(window).trigger('auth_changed');
                }
                else {
                    // whoops, wrong username or password
                    site.toast("Invalid Login.");
                    if (typeof fail != 'undefined'){
                        fail();
                    }
                }
            }
        );
    }
    this.logout = function(){
        Cookies.remove('session');
        Cookies.remove('userID');
        user_data = undefined;
        $(window).trigger('auth_changed');
        site.toast('Logged out.');
    }
}
window.$$ = document.querySelector;
var site = new Site();
if (Cookies.get('session') && Cookies.get('userID')){
    // user has cookies, auth them
    site.auth(Cookies.get('userID'), Cookies.get('session'), function(data){
        if (data != "0"){
            window.user_data = JSON.parse(data);
        }
        else {
            site.toast("Session Expired");
            Cookies.remove('session');
            Cookies.remove('userID');
        }
    });
}
