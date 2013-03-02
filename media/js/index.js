var refreshTimer = null;

var refreshImage = function() {
	img = document.getElementById("graph");
	img.src="image?rand=" + Math.random();
}

var startImageRefresh = function() {
	refreshTimer = setInterval('refreshImage', 10000);
}

$('.btn.left').click(function(e) {
	e.preventDefault();
	$.post('/left', {}, function(data) {
		refreshImage();
	});
	refreshImage();
});

$('.btn.right').click(function(e) {
	e.preventDefault();
	$.post('/right', {}, function(data) {
		refreshImage();
	});
	refreshImage();
});

$('.btn.autorefresh').click(function(e) {
	var me = $(this),
		input = $('input.autorefresh');
	if(me.hasClass('active')) {
		clearInterval(refreshTimer);
		me.removeClass('active');
		input.attr('name', '_autorefresh');
	} else {
		startImageRefresh();
		me.addClass('active');
		input.attr('name', 'autorefresh');
	}
});

if($('input[name="autorefresh"]').val() == 1) {
	startImageRefresh();
}

