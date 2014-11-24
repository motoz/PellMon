
var baroptions = {
     series: {
         color: '#9a9afa', 
         bars: {
             show: true,
             //align: 'center'
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
     },
    grid:   {
        hoverable: true,
        backgroundColor:'#f9f9f9',
        },
 };

var drawConsumption = function(url, graph, width) {
    $.get(
        url,
        function(jsondata) {
            data = JSON.parse(jsondata);
            options = baroptions;
            options.series.bars.barWidth = width * 1000;
            plot = $.plot($(graph), [data], options);
        })
}

$(function() {
    drawConsumption('flotconsumption24h', '#consumption24h', 3600);
    drawConsumption('flotconsumption7d', '#consumption7d', 3600*24);
    drawConsumption('flotconsumption1m', '#consumption1m', 3600*24*7);
    drawConsumption('flotconsumption1y', '#consumption1y', 3600*24*30);
});

