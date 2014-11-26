
var baroptions = {
     series: {
         color: '#6989b7',//#9a9afa', 
         bars: {
             show: true,
             //align: 'center',
             lineWidth: 0,
         },
     },
    // yaxes: {
    //     min: 0
    // },
     xaxis: {
         mode: 'time',
         lineWidth: 0,
         //timeformat: "%y",
         //tickSize: [1, "year"],
         //autoscaleMargin: .10 // allow space left and right
         tickColor: '#f9f9f9',

     },
    grid:   {
        hoverable: true,
        backgroundColor:'#f9f9f9',
        borderWidth: 1,
        borderColor: '#e7e7e7'
        },
 };

var drawConsumption = function(url, graph, width, totalunit, averageunit) {
    $.get(
        url,
        function(jsondata) {
            var data = JSON.parse(jsondata);
            options = baroptions;
            options.series.bars.barWidth = width * 1000;
            plot = $.plot($(graph), [data.bardata], options);
            $('<p>Total: ' + data.total.toFixed(1).toString() + totalunit + ', Average: ' + data.average.toFixed(1).toString() + averageunit + '</p>').insertAfter($(graph));
        })
}

$(function() {
    drawConsumption('flotconsumption24h', '#consumption24h', 3300, 'kg', 'kg/h');
    drawConsumption('flotconsumption7d', '#consumption7d', 3500*24, 'kg', 'kg/day');
    drawConsumption('flotconsumption1m', '#consumption1m', 3500*24*7, 'kg', 'kg/week');
    drawConsumption('flotconsumption1y', '#consumption1y', 3400*24*30, 'kg', 'kg/month');
});

