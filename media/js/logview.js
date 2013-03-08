

function getLog() {
	$.get(
		'/logview/getlines',
		function(data) {
            $("#lines").html(data)
		}
	);
}


getLog();
