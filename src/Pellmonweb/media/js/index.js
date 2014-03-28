var refreshTimer = null,
	windowResizeTimer = null;

/**
 * Refresh/lazy load graphs at page load
 */
$(function() {
	refreshGraph();
	refreshConsumption();
	refreshSilolevel();
});

/**
 * Refresh graphs when the window is resized
 */
$(window).on('resize', function(e) {
	if(windowResizeTimer !== null) {
		clearTimeout(windowResizeTimer);
	}

	windowResizeTimer = setTimeout(function() {
		refreshAll();
	}, 300);
});

var getMaxWidth = function() {
	return 	getGraph().closest('div').innerWidth();
}

var refreshAll = function() {
	refreshGraph();
	refreshConsumption();
	refreshSilolevel();
}

var refreshGraph = function() {
	var graph = getGraph(),
	offset = graph.data('offset')
	maxWidth = getMaxWidth();

	graph.attr('src', graph.data('src') + '?width=' + maxWidth + '&timeoffset=' + offset + '&legends=no' + '&random=' + Math.random() );
}

var refreshConsumption = function() {
	var consumption = $('#consumption'),
		maxWidth = getMaxWidth();

	consumption.attr('src', consumption.data('src') + '?random=' + Math.random() + '&maxWidth=' + maxWidth);
}

var refreshSilolevel = function() {
	var silolevel = $('#silolevel'),
		maxWidth = getMaxWidth();

	silolevel.attr('src', silolevel.data('src') + '?random=' + Math.random() + '&maxWidth=' + maxWidth);
}

var startImageRefresh = function() {
	refreshTimer = setInterval(refreshGraph, 10000);
}

var getGraph = function() {
	return $('#graph');
}

$('.timeChoice').click(function(e) {
    e.preventDefault();
    $('.timeChoice').each( function() {
        $(this).removeClass('selected')
    });
    var me = $(this);
    var graph=getGraph()
    me.addClass('selected')
    graph.data('title', me.data('title-text')+'...');
    setGraphTitle()
    graph.data('title', me.data('title-text'));

    timespan =  me.data('time-choice');
    graph.data('timespan', timespan);
    $.post(
            '/graphsession?timespan='+timespan,
            function(data) {
                refreshGraph();
            }
    )
});

$('.lineselection').click(function(e) {
	e.preventDefault();
	var me = $(this);

    a = me.data('selected')
    if (a == 'yes')
        { me.data('selected', 'no') 
          me.removeClass('selected')
        } 
    else 
        { me.data('selected', 'yes') 
          me.addClass('selected')
        } 
	var s = ''
    $('.lineselection').each(function() {
        if ($(this).data('selected')=='yes')  {
            s = s + $(this).data('linename')+',';
        }
    });

    $.post(
            '/graphsession?lines='+s,
            function(data) {
                getGraph().data('time-choice', me.data('time-choice'));
                refreshGraph();
            }
    )


});


$('.left').click(function(e) {
    var graph = getGraph()
	e.preventDefault();
	offset = graph.data('offset')
    offset = parseInt(offset, 10)
    timespan = graph.data('timespan')
    offset = offset + timespan
    ofs = offset.toString()
    graph.data('offset', ofs+'...');
    setGraphTitle();
    graph.data('offset', ofs);
    refreshGraph();
});

$('.right').click(function(e) {
	e.preventDefault();
	var graph=getGraph()
	offset = graph.data('offset')
    offset = parseInt(offset, 10)
    timespan = graph.data('timespan')
    offset = offset - timespan
    if (offset < 0) {offset = 0}
    ofs = offset.toString()
    graph.data('offset', ofs+'...');
    setGraphTitle();
    graph.data('offset', ofs);
    refreshGraph();
});

$('.autorefresh').click(function(e) {
	e.preventDefault();
	var me = $(this),
		input = $('input.autorefresh');

	var setAutorefresh = function(state, callback) {
		$.post(
			'autorefresh',
			{
				autorefresh: state
			},
			function(data) {
				me.data('processing', false);
				if(typeof callback === 'function') {
					callback();
				}
			}
		);
	};

	if(me.data('processing')) {
		return;
	}

	me.data('processing', true);

	if(me.hasClass('selected')) {
		me.removeClass('selected');
		setAutorefresh('no', function() {
			clearInterval(refreshTimer);
		});
	} else {
		me.addClass('selected');
		setAutorefresh('yes', function() {
			startImageRefresh();
		});
		refreshGraph();
	}
});

if($('.autorefresh').hasClass('selected')) {
	startImageRefresh();
}

var setGraphTitle = function() {
    var graph = getGraph()
    offset = graph.data('offset')
    if (offset == '0')
    {
        title = graph.data('title')
    }
    else
    {
        title = graph.data('title') + ' - ' + offset + 's'
    }
    $('h4.graphtitle').text(title);
}

$('#graph').load(function() {
    setGraphTitle();
});

// fetches the document for the given embedding_element
function getSubDocument(embedding_element)
{
	if (embedding_element.contentDocument) 
	{
		return embedding_element.contentDocument;
	} 
	else 
	{
		var subdoc = null;
		try {
			subdoc = embedding_element.getSVGDocument();
		} catch(e) {}
		return subdoc;
	}
}

function findSVGElements(name, value)
{
	var elms = document.querySelectorAll(".emb");
	for (var i = 0; i < elms.length; i++)
	{
		var subdoc = getSubDocument(elms[i])
		if (subdoc)
//			subdoc.getElementById("svgbar").setAttribute("fill", "lime");
			var sub2 = subdoc.getElementById("paramname_" + name)
			sub2.textContent = value;
	}
}

window.addEventListener("load", findSVGElements, false);

function url(s) {
    var l = window.location;
    return ((l.protocol === "https:") ? "wss://" : "ws://") + l.hostname + (((l.port != 80) && (l.port != 443)) ? ":" + l.port : "") + '/websocket' +s;
}

$(document).ready(function() {

    websocket = url('/ws/'+ 'boiler_temp,smoke_temp,chute_temp,magazine_contents');
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
            //container = $('#' + obj.name + '-value');
            //container.html(obj.value);
            findSVGElements(obj.name, obj.value);
     }
  };

});

