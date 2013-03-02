refreshImage = function() {
	img = document.getElementById("graph");
	img.src="image?rand=" + Math.random();
}

$("#left").submit(function(e) {
	e.preventDefault();
	$.post('/left', {}, function(data) {
		refreshImage();
	});
	refreshImage();
});

$("#right").submit(function(e) {
	e.preventDefault();
	$.post('/right', {}, function(data) {
		refreshImage();
	});
	refreshImage();
});

if($('input[name="autorefresh"]:checked').length === 1) {
	setInterval('refreshImage', 10000);
}