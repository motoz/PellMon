var getParam = function(param) {
	$.get('/getparam/' + param,
		function(data) {
			setParam(param, data.value);
		}
	);
};

var setParam = function(param, value) {
	$('#' + param + '-value').text(value);
};

$('.editable').on('click', function(e) {
	e.preventDefault();
	
        var me = $(this);

	if(me.is('dt')) {
		var container = me.next();
	} else {
		var container = me.closest('dd');
	}

	var details = $('.details.hidden', container),
		others = $('.details').not(details);

	details.removeClass('hidden');
	others.addClass('hidden');
	
});

$(".save").on('submit', function(e) {
	e.preventDefault();

	var form = $(this),
	btn = $('input[type=submit]', form),
	textfield = $('input[type=text]', form),
	name = textfield.attr('name'),
	value = textfield.val();

	if(value == '') {
		textfield.addClass('error');
		return;
	}

	textfield.removeClass('error');

	btn.button('loading');

	$.post(
		'/setparam/' + name,
		{
			data: value
		},
		function(data) {
			if(data.value === 'OK') {
				btn.button('reset');
				setParam(name, value);
				textfield.val('');
			} else {
				textfield.addClass('error');
			}
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
