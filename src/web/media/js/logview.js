

function getLog() {
	$.get(
		
		'/logview/getlines?linenum='+linecount,
		function(data) {
            $("#lines").html(data)
		}
	);
}


getLog();
