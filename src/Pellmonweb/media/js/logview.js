// Escapes special characters and returns a valid jQuery selector
function jqSelector(str)
{
return str.replace(/\?\/([;&,\.\+\*\~':"\!\^#$%@\[\]\(\)=>\|])/g, '\\$1');
}

function isTransparent(bgcolor){
    return (bgcolor=="transparent" || bgcolor.substring(0,4) == "rgba");
}

function rgb2hex(rgb) {
    rgb = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    function hex(x) {
        return ("0" + parseInt(x).toString(16)).slice(-2);
    }
    return hex(rgb[1]) + hex(rgb[2]) + hex(rgb[3]);
}

function getLog() {
    var container = $('#lines');
    $.get(
        container.data('url'),
        function(data) {
            container.html(data)
            $('.loglinelink').click(function(e) {
                e.preventDefault();
                var me = $(this);
                width = me.closest('div').innerWidth()-40
                loglink = 'loglink'
                if (me.data('has_graph') != 'yes') {
                    me.data('has_graph', 'yes')
                    bgcolor = me.css('background-color');
                    if (isTransparent(bgcolor)){
                        me.parents().each(function(){
                            if (!isTransparent($(this).css('background-color'))){
                                bgcolor = $(this).css('background-color');
                                return false;
                            }
                        });
                    }
                    graphid = (me.data('time')+Math.random()).toString().replace(/\./g, '0')
                    me.append('<div class='+loglink+'><img id='+graphid+' src="'+webroot+'/media/img/spinner.gif"/></ div>')
                    $('#'+graphid).attr('src', me.data('src')+'&width='+width+'&bgcolor='+rgb2hex(bgcolor)+'&random='+Math.random())
                }
                else
                {
                    me.data('has_graph', 'no')
                    me.children('.loglink').remove()
                }
            });
        }
    );
}

getLog();
