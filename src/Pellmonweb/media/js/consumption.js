
var baroptions = {
     series: {
         bars: {
             show: true,
             barWidth: 3000000*24*30, 
             align: 'center'
         },
     },
     yaxes: {
         min: 0
     },
     xaxis: {
         mode: 'time',
         //timeformat: "%y",
         //tickSize: [1, "year"],
         //autoscaleMargin: .10 // allow space left and right
     }
 };

var drawConsumption = function() {
    $.get(
        'flotconsumption1y',
        function(jsondata) {
            data = JSON.parse(jsondata);
            plot = $.plot($('#consumption1y'), [data], baroptions);
        })
}

drawConsumption();

