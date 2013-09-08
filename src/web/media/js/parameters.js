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

$(".command").on('click', function(e) {
	e.preventDefault();

	var me = $(this),
	form = me.closest('form'),
	textfield = $('input[type=hidden]', form);

	$.post(
		'/setparam/' + textfield.attr('name'),
		{
			data: '0'
		},
		function(data) {
			textfield.val(data.value);
			setTimeout(function() {
				getParam(textfield.attr('name'));
			}, 2000);
		});
});

var params = $('.param'),
	count = params.length;

function getParams() {
	$.get(
		'/getparams/',
		function(data) {
            for (var param in data) {
				var textfield = $('#' + param + '-text');
				if(textfield.length > 0) {
					textfield.val(data[param]);
					count = count-1;
				}
            }

			if (count > 0) {
				getParams();
			}
		}
	);
}

getParams();
