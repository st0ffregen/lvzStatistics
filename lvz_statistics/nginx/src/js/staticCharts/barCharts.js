
function customTooltip(data) {
    return function(tooltip) {
        let displayData = [];
        let displayLabel = [];
        let colorArray = [];

        //parse data to data array
        for (let i = 0; i < data.length; i++) {
            if (data[i]['ressort'] === tooltip.title[0]) {

                for (let k = 0; k < data[i]['authors'].length; k++) {
                    colorArray.push(getSingleRandomColor(alpha));
                    displayData.push(data[i]['authors'][k]['count']);
                    //split name
                    let split = data[i]['authors'][k]['name'].split(" ");
                    let firstName = "";

                    for (let l = 0; l < split.length - 1; l++) {
                        firstName += split[l] + " ";

                    }

                    let name = firstName + split[split.length - 1].charAt(0) + ".";
                    displayLabel.push(name);
                }
                break;
            }
        }

        // Tooltip Element
        let tooltipEl = document.getElementById('chartjs-tooltip');

        // Hide if no tooltip
        if (tooltip.opacity === 0) {
            tooltipEl.style.opacity = 0;
            return;
        }

        while (tooltipEl.firstChild) {
            tooltipEl.removeChild(tooltipEl.firstChild);
        }

        let label = document.createElement('p');
        let canvasHolder = document.createElement('div');
        canvasHolder.classList.add('small-canvas-container');


        if (displayData.length > 0) {
            label.innerHTML = tooltip.title[0] + ": " + tooltip.dataPoints[0].yLabel + "; Top Autor*innen:";
            label.className = "chartjs";
            label.classList.add('small-canvas-label');
            tooltipEl.appendChild(label);


            tooltipEl.appendChild(canvasHolder);

            let child = document.createElement('canvas');
            child.id = 'tooltipChart';
            canvasHolder.appendChild(child);
        } else {
            label.innerHTML = tooltip.title[0] + ": " + tooltip.dataPoints[0].yLabel;
            tooltipEl.appendChild(label);
        }

        // Set caret Position
        tooltipEl.classList.remove('above', 'below', 'no-transform');
        if (tooltip.yAlign) {
            tooltipEl.classList.add(tooltip.yAlign);
        } else {
            tooltipEl.classList.add('no-transform');
        }

        // Set Text
        if (tooltip.body && displayData.length > 0) {

            let chart = canvasHolder.children[0].getContext('2d');
            // For a pie chart
            let newChart = new Chart(chart, {
                type: 'bar',
                data: {
                    datasets: [{
                        data: displayData,
                        label: displayLabel,
                        borderWidth: 1,
                        fill: false,
                        backgroundColor: colorArray,
                    }],
                    labels: displayLabel,


                }, options: {
                    tooltips: {
                        enabled: false
                    },
                    legend: false,
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                precision: 0
                            }
                        }]
                    },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            allCharts.push(newChart);
        }

        let positionY = this._chart.canvas.offsetTop;
        let positionX = this._chart.canvas.offsetLeft + 50; //+50 so the most left chart wont be cut of by the computer screen

        // Display, position, and set styles for font
        tooltipEl.style.opacity = 1;
        tooltipEl.style.left = positionX + tooltip.caretX + 'px';
        tooltipEl.style.top = positionY + tooltip.caretY + 'px';
        tooltipEl.style.fontFamily = tooltip._bodyFontFamily;
        tooltipEl.style.fontSize = tooltip.bodyFontSize + 'px';
        tooltipEl.style.fontStyle = tooltip._bodyFontStyle;
        tooltipEl.style.padding = tooltip.yPadding + 'px ' + tooltip.xPadding + 'px';
    };
}

function barChart(chartElement, data, type, label, chartFontSize, tooltipBoolean, customTooltip) {

	let colorArray = [];
	let nameArray = [];
	let valueArray = [];

	for(let i=0;i<data.length;i++) {
		nameArray.push(data[i]['name']);
		valueArray.push(data[i]['count']);
		colorArray.push(getSingleRandomColor(alpha));
	}

	let barChartConfig = {
		type: type,
		data: {
			labels: nameArray,
			datasets: [{
				backgroundColor: colorArray,
				fill: false,
				data: valueArray,
				label: label,
				borderWidth: 1,
			}]
		},
		options: {
			tooltips: {
  			// Disable the on-canvas tooltip
	  		enabled: tooltipBoolean,
	  		mode: 'index',
	  		position: 'nearest',
	  		custom: customTooltip,
	  		},
		  	scales: {
		  		yAxes: [{
		  			ticks: {
		  				precision: 0
		  			}
		  		}]
		  	},
		  	animations: {
		  		duration: 1000,
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

	const newGraph = new Chart(chartElement.getContext('2d'), barChartConfig);
    allCharts.push(newGraph);
}

