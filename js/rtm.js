function RTM(url){
    this.url = url;
    // Connect to socketserver
    this.ws = io.connect(this.url);
    this.handlers = [];

    // Tells the server to listen for database changes and send them to us
    this.listen = function(collection, sender_pair, recipient_pairs){
        var callback = callback || false;   // make callback optional
        // construct listen query
        var query = {
            collection: collection,
            sender_pair: sender_pair,
            recipient_pairs: recipient_pairs,
            backlog: true
        };
        // emit request
        this.ws.emit('listen', JSON.stringify(query));
    }

    this.send = function(data, collection, sender_pair, recipient){
        this.ws.emit('send', JSON.stringify({
            collection: collection,
            sender_pair: sender_pair,
            recipient: recipient,
            data: data
        }));
    }

    //
}
