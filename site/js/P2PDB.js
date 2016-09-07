function P2PDB(peers) {
  this.peers = peers;
  // Listen method that prioritises using WebRTC to steam data from peers
  this.listen = function(query) {
    for (var peer in peers) {
      if (query == peer.query){
        var rtm = new RTM(peer.host);
        if (rtm) {
          break;
        }
      }
    }
    if (!rtm) {
      var rtm = new RTM();
    }
    rtm.listen({
      collection: query.collection,
      recipient_pairs: query.recipient_pairs,
      sender_pair: query.sender_pair,
      backlog: query.backlog
    });
  }
}

window.p2pdb = false;
site.api(
  "get-peers",
  {},
  function (peers){
    window.p2pdb = new P2PDB(peers);
    $(p2pdb).trigger('ready');
  }
);
