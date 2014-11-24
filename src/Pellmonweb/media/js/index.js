var refreshTimer = null,
    windowResizeTimer = null,
    params="",
    plot=null;

/**
 * Refresh/lazy load graphs at page load
 */
$(function() {
    refreshGraph();
    refreshConsumption();
    refreshSilolevel();
    plot = $.plot($('#graph'), data, options);
    svgElement = document.getElementById("systemimage");

    if ($("#systemimage").data('websocket')) 
    {
        setupWebSocket();
    }
    else 
    {
        setupPolling();
    }
});

/**
 * Refresh graphs when the window is resized
 */
$(window).on('resize', function(e) {
    if(windowResizeTimer !== null) {
    clearTimeout(windowResizeTimer);
    }

    windowResizeTimer = setTimeout(function() {
    refreshSilolevel();
    }, 100);
});

var getMaxWidth = function(name) {
    return  $(name).closest('div').innerWidth();
}

var data = []
var options = {
        series: {
                    lines: { show: true, lineWidth: 1 },
                    points: { show: false },
                    shadowSize: 0,
                },
        xaxes:  [{
                    mode: "time",       
                    position: "top",
                }],
        legend: { 
                    show: false
                },
        grid:   {
                hoverable: true,
                backgroundColor:'#f9f9f9',
                },
        zoom: {
        interactive: true
            },
            pan: {
                interactive: true
            }
    };

var baroptions = {
     series: {
         color: '#9a9afa', 
         bars: {
             show: true,
             barWidth: 3600000, 
             //align: 'center'
         },
     },
     yaxes: {
         min: 0
     },
     xaxis: {
         mode: 'time',
         //timeformat: "%y",
         //tickSize: [1, "year"],
         //autoscaleMargin: .10 // allow space left and right
     }
 };


var refreshGraph = function(getdata) {
    var getdata = typeof getdata !== 'undefined' ? getdata : true;
    var graph = getGraph();
    var offset = graph.data('offset')
    var maxWidth = getMaxWidth('#graph');

    function plotGraph() {
        var plotdata = [];
        var selected = []
        $('.lineselection').each(function() {
            if ($(this).data('selected')=='yes') {
                selected.push($( this ).text());
            }
        });
        for (series in data) {
            if ( selected.indexOf(data[series]['label']) != -1 ) {
                plotdata.push(data[series]);
            }
        }
        graph.unbind();
        graph.unbind("plothover");
        plot = $.plot($('#graph'), plotdata, options);

        function showTooltip(x, y, contents) {
            $('<div id="tooltip">' + contents + '</div>').css({
                border: "1px solid #dddddd",
                "background-color": "#f9f9f9",
                opacity: 0.80,
                position: 'absolute',
                display: 'none',
                top: y -25,
                left: x + 10,
                padding: '2px',
            }).appendTo("body").fadeIn(200);
        }

        var previousPoint = null;
        graph.bind("plothover", function (event, pos, item) {
            if (item) {
                var x = item.datapoint[0].toFixed(0),
                    y = item.datapoint[1].toFixed(1);
                var point = x+':'+y;
                if (previousPoint != point) {
                    $("#tooltip").remove();
                    previousPoint = point;
                    var tooltipX = item.pageX;
                    if (tooltipX - plot.offset().left > plot.width() - 75) {
                        tooltipX -= 150;
                    }
                    showTooltip(tooltipX, item.pageY, item.series.label + " = " + y);
                }
            }
            else {
                $("#tooltip").remove();
                previousPoint = null;
            }
        });
    }

    if (getdata) {
        $.get(
            'export'+'?width=' + maxWidth + '&timeoffset=' + offset,
            function(jsondata) {
                data = JSON.parse(jsondata);
                plotGraph();
            }
        )
    } else {
        plotGraph();
    }
    setGraphTitle();
}

var refreshConsumption = function() {
    $.get(
        'flotconsumption'+'?period=3600&bars=24',
        function(jsondata) {
            data = JSON.parse(jsondata);
            plot = $.plot($('#consumption'), [data], baroptions);
        })
}

var refreshSilolevel = function() {
    var silolevel = $('#silolevel'),
        maxWidth = getMaxWidth('#silolevel');

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
            'graphsession?timespan='+timespan,
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
            'graphsession?lines='+s,
            function(data) {
                getGraph().data('time-choice', me.data('time-choice'));
                refreshGraph(false);
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

function changeSystemImageText(name, value)
{
    var subdoc = getSubDocument(svgElement)
    if (subdoc) {
        var sub2 = subdoc.getElementById("paramname:" + name)
        rounded = +parseFloat(value).toFixed(1);
        if (isNaN(rounded)) rounded = value
        if (sub2) sub2.textContent = rounded;
    }
}

function url(s) {
    var l = window.location;
    return ((l.protocol === "https:") ? "wss://" : "ws://") + l.hostname + (((l.port != 80) && (l.port != 443)) ? ":" + l.port : "") +webroot+'/websocket' +s;
}

function setupWebSocket() {
    var subdoc = getSubDocument(svgElement)
    if (subdoc) {
        var allElements = subdoc.getElementsByTagName("text");
        for(var i = 0; i < allElements.length; i++) {
            var element = allElements[i];
            if((element.id).indexOf("paramname:") != -1) {
                if (params != "") params = params + ','
                params = params + (element.id).split(':')[1];
            }    
        }
        if (params == "") 
        {
            setTimeout(setupWebSocket, 1000)
        }
        else
        {
            websocket = url('/ws/?parameters='+ params + '&events=yes');
            if (window.WebSocket) {
                ws = new ReconnectingWebSocket(websocket);
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
                    if (obj.name == '__event__') 
                        getLog();
                    else
                        changeSystemImageText(obj.name, obj.value);
                }
            };
        }
    }
    else
    {
        setTimeout(setupWebSocket, 1000);
    }
}


function setupPolling() {
    var subdoc = getSubDocument(svgElement)
    if (subdoc) {
        var allElements = subdoc.getElementsByTagName("text");
        for(var i = 0; i < allElements.length; i++) {
            var element = allElements[i];
            if((element.id).indexOf("paramname:") != -1) {
                if (params != "") params = params + ','
                params = params + (element.id).split(':')[1];
            }    
        }
        if (params == "") 
        {
            setTimeout(setupPolling, 1000)
        }
        else
        {
            var pollParams = function(params) {
                $.get('getparamlist?parameters='+ params,
                    function(data) {
                        jsonObject = $.parseJSON(data);
                        for (i in jsonObject) {
                            obj = jsonObject[i];
                            changeSystemImageText(obj.name, obj.value);
                        }
                    }
                )
                setTimeout(pollParams, 15000);
            };
            pollParams(params);
        }
    }
    else
    {
        setTimeout(setupWebSocket, 1000);
    }
}

