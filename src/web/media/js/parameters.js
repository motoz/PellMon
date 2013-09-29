var getParam = function(param) {
	$.get('/getparam/' + param,
		function(data) {
			$('#' + param + '-value').text(data.value);
		}
	);
};

$('.editable').on('click', function(e) {
        var me = $(this);
		par = me.parent(),
		details = $('.details.hidden', par),
		others = $('.details').not(details);

	details.removeClass('hidden');
	others.addClass('hidden');
	
});

$(".set").on('submit', function(e) {
	e.preventDefault();

	var form = $(this),
	btn = $('input[type=submit]', form),
	textfield = $('input[type=text]', form);

	btn.button('loading');

	$.post(
		'/setparam/' + textfield.attr('name'),
		{
			data: textfield.val()
		},
		function(data) {
			setTimeout(function() {
				btn.button('reset');
				getParam(textfield.attr('name'));
			}, 1000);
		});
});

$(".command").on('click', function(e) {
	e.preventDefault();

	var me = $(this),
	name = me.data('name');

	$.post(
		'/setparam/' + name,
		{
			data: '0'
		}
	);
});

var params = $('.param'),
	count = params.length;

function getParams() {
	$.get(
		'/getparams/',
		function(data) {
            	for (var param in data) {
			var container = $('#' + param + '-value');
			if(container.length > 0) {
				container.html(data[param]);
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

$('.set').button();
