// rtm wrapper
function RTM(collection, url, _debug) {
  this.url = url || 'http://' + document.location.host + '/component';
  this.collection = collection;
  this.debug = true ? _debug : false;
  // This is just sha512(''). Don't trip, yo.
  this.blank_sha512 =
    'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce' +
    '47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e';
  
  // creates a new connection to the database
  this.new_connection = function () {
    if (typeof this.ws != "undefined"){
        this.ws.disconnect();
    }
    this.ws = io.connect(this.url);
    if (this.debug){
      this.ws.on("log", function(data){console.log(data)});
    }
    return this.ws;
  };

  this.clean_up = function(){
    for (i in window.rtm_sockets){
      window.rtm_sockets[i].disconnect();
    }
  }

  // listens to all possible messages matching `where` if specified
  this.listen = function () {// ([backlog:bool, where:obj, callback:func])
    // create a new db connection
    var connection = this.new_connection(), query = {};
    query['backlog'] = true;
    // gather arguments and build query
    for (var i in arguments){
      var argument = arguments[i];
      switch (typeof argument){
        case "function":   // callback
          connection.on("data", argument);
          break;
        case "boolean":   // backlog
          query['backlog'] = argument;
          break;
        case "object":   // where
          query['where'] = argument;
          break;
      }
    }
    // get all user auths
    query['auths'] = this.get_auth();
    // set collection
    query['collection'] = this.collection;
    // send query
    connection.emit('listen', JSON.stringify(query));
  };

  // sends data to the target collection
  this.send = function(data, sender, recipient){
    // use an already created non-blocking connection if available
    if (typeof this.send_con == "undefined"){
      this.send_con = this.new_connection();
    }
    this.send_con.emit('send', JSON.stringify({
      collection: this.collection,
      sender: typeof sender != "undefined" ? sender : $.Cookie('username'),
      auths: this.get_auth(),
      recipient: typeof recipient != "undefined" ? recipient : "Public",
      data: data
    }));
  }

  // updates target document with data
  this.update = function(document_id, data){
    // use an already created non-blocking connection if available
    if (typeof this.send_con == "undefined"){
      this.send_con = this.new_connection();
    }
    this.send_con.emit('update', JSON.stringify({
      collection: this.collection,
      auths: this.get_auth(),
      data: data,
      document_id: document_id
    }));
  }
    
  this.keys_exist = function(key_list, obj){
    for (var i in key_list){
      var key = key_list[i];
      if (obj[key] == undefined){
        return false;
      }
    }
    return true;
  }
  
  // gets all datachests the user is authenticated to see
  this.get_auth = function(){
    var auth = [[{"$uid_of": "Public"}, this.blank_sha512]];
    if (typeof user_data != "undefined"){
      auth = auth.concat(user_data.datachests);
    }
    return auth;
  }
}