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
    me.addClass('selected')
    $('h4.graphtitle').text(me.data('title-text')+'...');
    getGraph().data('title', me.data('title-text'));
    timespan =  me.data('time-choice');
    getGraph().data('timespan', timespan);
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


$('.btn.left').click(function(e) {
	e.preventDefault();
	offset = getGraph().data('offset')
    offset = parseInt(offset, 10)
    timespan = getGraph().data('timespan')
    offset = offset + timespan
	getGraph().data('offset', offset.toString());
	refreshGraph();
});

$('.btn.right').click(function(e) {
	e.preventDefault();
	offset = getGraph().data('offset')
    offset = parseInt(offset, 10)
    timespan = getGraph().data('timespan')
    offset = offset - timespan
    if (offset < 0) {offset = 0}
	getGraph().data('offset', offset.toString());
	refreshGraph();
});

$('.btn.autorefresh').click(function(e) {
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

	if(me.hasClass('active')) {
		me.removeClass('active');
		setAutorefresh('no', function() {
			clearInterval(refreshTimer);
		});
	} else {
		me.addClass('active');
		setAutorefresh('yes', function() {
			startImageRefresh();
		});
		refreshGraph();
	}
});

if($('.btn.autorefresh').hasClass('active')) {
	startImageRefresh();
}

$('#graph').load(function() {
    $('h4.graphtitle').text(getGraph().data('title'));
});

