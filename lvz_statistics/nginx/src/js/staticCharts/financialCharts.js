var DateTime = luxon.DateTime;

function convertFinancialDataDerivative(data, label, color = '#ff6384', hidden = 0) {

    let dataset = [];

    for (const date of data) {
        dataset.push({t: DateTime.fromISO(date['date'].split(' ')[0]).valueOf(), y: date['count']});
    }

    return [
        {
            label: label,
            borderColor: color,
            data: dataset,
            type: 'line',
            pointRadius: 0,
            fill: false,
            lineTension: 0,
            borderWidth: 2,
            hidden: hidden
        }
    ];
}

function convertFinancialData(data, label, color = '#ff6384', hidden = 0) {
    let dataset = [];
    let summedUpCount = 0;

    for (const row of data) {
        //summedUpCount += parseInt(date['count']);
        dataset.push({t: row['key'], y: row['doc_count']});
    }

    return [
        {
            label: label,
            borderColor: color,
            data: dataset,
            type: 'line',
            pointRadius: 0,
            fill: false,
            lineTension: 0,
            borderWidth: 2,
            hidden: hidden
        }
    ];
}

function financialChart(chartElement, data, tooltipFormat, chartFontSize) {

    let configForFinancialCharts = {
        data: {
            datasets: data
        },
        options: {
            animation: {
                duration: 0
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    distribution: 'linear',
                    offset: true,
                    time: {
                        'tooltipFormat': tooltipFormat
                    },
                    ticks: {
                        major: {
                            enabled: true,
                            fontStyle: 'bold'
                        },
                        source: 'auto',
                        autoSkip: true,
                        autoSkipPadding: 75,
                        maxRotation: 0,
                        sampleSize: 100,
                        maxTicksLimit: 7,
                    },
                    afterBuildTicks: function (scale, ticks) {
                        if (ticks != null) {
                            let majorUnit = scale._majorUnit;
                            let firstTick = ticks[0];
                            let i, ilen, val, tick, currMajor, lastMajor;

                            val = DateTime.fromISO(ticks[0].value);
                            if ((majorUnit === 'minute' && val.second === 0)
                                || (majorUnit === 'hour' && val.minute === 0)
                                || (majorUnit === 'day' && val.hour === 9)
                                || (majorUnit === 'month' && val.day <= 3 && val.weekday === 1)
                                || (majorUnit === 'year' && val.month === 0)) {
                                firstTick.major = true;
                            } else {
                                firstTick.major = false;
                            }
                            lastMajor = val.get(majorUnit);

                            for (i = 1, ilen = ticks.length; i < ilen; i++) {
                                tick = ticks[i];
                                val = DateTime.fromISO(tick.value);
                                currMajor = val.get(majorUnit);
                                tick.major = currMajor !== lastMajor;
                                lastMajor = currMajor;
                            }
                            return ticks;
                        }
                    }
                }],
                yAxes: [{}]
            },
            hover: {
                mode: 'nearest',
                intersect: false
            },
            tooltips: {
                mode: 'nearest',
                intersect: false
            },
            legend: {

                labels: {
                    fontFamily: "'Helvetica', 'Arial', sans-serif",
                    fontColor: '#555',
                    fontSize: chartFontSize
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    };

    const newGraph = new Chart(chartElement.getContext('2d'), configForFinancialCharts);
    allCharts.push(newGraph);
}
