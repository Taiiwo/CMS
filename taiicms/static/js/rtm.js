function RTM(url){
    this.url = url || 'http://'+ document.location.host +'/component';
    // Connect to socketserver
    this.ws = io.connect(this.url);
    this.handlers = [];
    // This is just sha512(''). Don't trip, yo.
    this.blank_sha512 =
    'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce'+
    '47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e';

    this.keys_exist = function(keys, obj){
        for (var i in keys){
            var key = keys[i];
            if (obj[key] == undefined){
                return false;
            }
        }
        return true;
    }

    // Tells the server to listen for database changes and send them to us
    this.listen = function(conf){
        if (!this.keys_exist([
                    'collection', 'sender_pair', 'recipient_pairs', 'backlog'
                ], conf)){
            return false;
        }
        // emit request
        this.ws.emit('listen', JSON.stringify(conf));
    }

    this.send = function(conf){
        if (!this.keys_exist([
                    'collection', 'sender_pair', 'recipient', 'data'
                ], conf)){
            return false;
        }
        this.ws.emit('send', JSON.stringify(conf));
    }

    //
}
