function getLog() {
    var container = $('#lines');

    $.get(
        '/logview/getlines?linenum='+container.data('lines'),
        function(data) {
            container.append(data)
            $('.loglinelink').click(function(e) {
                e.preventDefault();
                var me = $(this);
                width = me.closest('div').innerWidth()-40
                $.get(
                    me.append('</br><img src='+me.data('src')+'&height=250&legends=no&width='+width+'>')
                );
            });
        }
    );
}

getLog();
