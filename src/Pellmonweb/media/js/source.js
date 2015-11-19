
$(function() {
    textarea = document.getElementById("sourceview");
    var item = $("#sourceview").data('item')
    {

        editor = CodeMirror(textarea, {mode:"properties", lineWrapping:true});
        var cm = $(".CodeMirror");
        cm.css("margin-top", "20px");

        var list_items = $("#sourceview").data('list_items');
        var size_y = $("#sourceview").data('size_y');
        var filename = $("#sourceview").data('filename');

        $.get('/source/?filename='+filename, function(data) {
                jsonObject = $.parseJSON(data);
                filedata = jsonObject;
                editor.setValue(filedata.data);
                line = filedata.line
                editor.setCursor(line+40, 0);
                editor.setCursor(line-2, 0);
                $('#filename_header').html(filedata.filename);
                if (filedata.error) {
                    $('#filename_header').append('<br>'+filedata.error);
                }
        });
        
        if (size_y) {
            cm.css("height", size_y);
        } else {
            function t(){
                cm.css("height", $(window).height()-80+"px");
            }
            window.onload = t;
            window.onresize = t;
        }
    }
});

$('.savebutton').click(function(e) {
    e.preventDefault();
    $('#filename_header').html('Saving: ' + filedata.filename)
    filedata.data = editor.getValue(filedata.linesep);
    $.post('/save', {filename:filedata.filename, data:filedata.data}, function (data) {
        if (JSON.parse(data).success) {
            setTimeout(function() {
                $('#filename_header').html(filedata.filename)
            }, 800);
        }
        else {
            data = JSON.parse(data)
            $('#filename_header').html(data.error);
        }
    });
});




