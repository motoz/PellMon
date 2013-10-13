function getLog() {
	var container = $('#lines');

	$.get(
		'/logview/getlines?linenum='+container.data('lines'),
		function(data) {
            container.append(data)
		}
	);
}

getLog();