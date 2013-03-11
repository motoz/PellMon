var refreshTimer = null;

var refreshImage = function() {
	img = document.getElementById("graph");
	img.src="image?rand=" + Math.random();
}

var startImageRefresh = function() {
	refreshTimer = setInterval(refreshImage, 10000);
}

$('.btn.left').click(function(e) {
	e.preventDefault();
	$.post('/left', {}, function(data) {
		refreshImage();
	});
	//refreshImage();
});

$('.btn.right').click(function(e) {
	e.preventDefault();
	$.post('/right', {}, function(data) {
		refreshImage();
	});
	//refreshImage();
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

