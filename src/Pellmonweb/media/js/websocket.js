function url(s) {
    var l = window.location;
    return ((l.protocol === "https:") ? "wss://" : "ws://") + l.hostname + (((l.port != 80) && (l.port != 443)) ? ":" + l.port : "") + '/websocket' +s;
}

$(document).ready(function() {

    websocket = url('/ws/'+paramlist);
    if (window.WebSocket) {
        ws = new WebSocket(websocket);
    }
    else if (window.MozWebSocket) {
        ws = MozWebSocket(websocket);
    }
    else {
        console.log('WebSocket Not Supported');
        return;
    }

    window.onbeforeunload = function(e) {
        ws.close();
    };

    ws.onmessage = function (evt) {
        jsonObject = $.parseJSON(evt.data);
        for (i in jsonObject) {
            obj = jsonObject[i];
            container = $('#' + obj.name + '-value');
            container.html(obj.value);
     }
  };

});

