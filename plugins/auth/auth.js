// TODO: Add deprecation notice to all these and move to auth.*

site.login = function(username, password, success, fail){
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
  site.plugin_api(
    "auth",
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

site.logout = function() {
  Cookies.remove('session');
  Cookies.remove('user_id');
  user_data = undefined;
  $(window).trigger('auth_changed');
  site.toast('Logged out.');
}

site.auth = function(id, session, callback){
  site.plugin_api(
    "auth",
    "authenticate",
    {
      userID: id,
      session, session
    },
    callback
  );
  $(window).trigger('auth_changed');
}

site.userAuthed = function(){
  // this is not totally secure, but it's impossible to make authenitcated
  // requests without a valid session token
  if (Cookies.get('session') == undefined) {
    return false;
  }
  else {
    return true;
  }
}

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
