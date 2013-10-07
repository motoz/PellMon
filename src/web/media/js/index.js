var refreshTimer = null,
	windowResizeTimer = null;

/**
 * Refresh/lazy load graphs at page load
 */
$(function() {
	refreshGraph();
	refreshConsumption();
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
}

var refreshGraph = function() {
	var graph = getGraph(),
		timeChoice = graph.data('time-choice'),
		direction = graph.data('direction'),
		maxWidth = getMaxWidth();

	graph.data('direction', '');

	graph.attr('src', graph.data('src') + '/' + timeChoice + '/' + direction + '?random=' + Math.random() + '&maxWidth=' + maxWidth);
}

var refreshConsumption = function() {
	var consumption = $('#consumption'),
		maxWidth = getMaxWidth();

	consumption.attr('src', consumption.data('src') + '?random=' + Math.random() + '&maxWidth=' + maxWidth);
}

var startImageRefresh = function() {
	refreshTimer = setInterval(refreshGraph, 10000);
}

var getGraph = function() {
	return $('#graph');
}

$('.timeChoice').click(function(e) {
	e.preventDefault();
	var me = $(this);

	getGraph().data('time-choice', me.data('time-choice'));
	refreshGraph();
});

$('.btn.left').click(function(e) {
	e.preventDefault();

	getGraph().data('direction', 'left');
	refreshGraph();
});

$('.btn.right').click(function(e) {
	e.preventDefault();

	getGraph().data('direction', 'right');
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

