var refreshTimer = null;

var refreshImage = function(direction) {
	var graph = $('#graph'),
		timeChoice = graph.data('time-choice');

	if(typeof timeChoice === 'undefined') {
		graph.data('time-choice', 'time1h');
		timeChoice = 'time1h';
	}

	if(typeof direction === 'undefined') {
		direction = '';
	}

	graph.attr('src', "image/"+timeChoice+"/"+direction+"?rand=" + Math.random());
}

var startImageRefresh = function() {
	refreshTimer = setInterval(refreshImage, 10000);
}

$('.timeChoice').click(function(e) {
	e.preventDefault();
	var graph = $('#graph'),
		me = $(this);

	graph.data('time-choice', me.data('time-choice'));
	refreshImage();
});

$('.btn.left').click(function(e) {
	e.preventDefault();
	refreshImage('left');
});

$('.btn.right').click(function(e) {
	e.preventDefault();
	refreshImage('right');
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
		refreshImage();
	}
});

if($('.btn.autorefresh').hasClass('active')) {
	startImageRefresh();
}

