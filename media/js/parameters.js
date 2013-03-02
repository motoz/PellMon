var getParam = function(param) {
	$.get('/getparam/' + param,
		function(data) {
			$('#' + param + '-text').val(data.value);
		}
	);
};

$(".set").on('click', function(e) {
	e.preventDefault();

	var me = $(this),
	form = me.closest('form'),
	textfield = $('input[type=text]', form);

	$.post(
		'/setparam/' + textfield.attr('name'),
		{
			data: textfield.val()
		},
		function(data) {
			textfield.val(data.value);
			setTimeout(function() {
				getParam(textfield.attr('name'));
			}, 2000);
		});
});

$(".get").on('click', function(e) {
	e.preventDefault();

	var me = $(this),
	form = me.closest('form'),
	textfield = $('input[type=text]', form);

	getParam(textfield.attr('name'));
});

$('.param').each(function(i, param) {
	getParam($(param).attr('name'));
});
