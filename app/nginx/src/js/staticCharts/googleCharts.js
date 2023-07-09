function googleTimeline(container, dataArrayAttr) {

	google.charts.load("current", {packages:["timeline"]});
	google.charts.setOnLoadCallback(drawChart);
	let dataArray = dataArrayAttr;

	function drawChart() {

		let chart = new google.visualization.Timeline(container);
		let dataTable = new google.visualization.DataTable();
		dataTable.addColumn({ type: 'string', id: 'Term' });
		dataTable.addColumn({ type: 'string', id: 'Name' });
		dataTable.addColumn({ type: 'date', id: 'Start' });
		dataTable.addColumn({ type: 'date', id: 'End' });

		for(let i=0;i<dataArray.length;i++) {

			dataTable.addRows([["", dataArray[i]['name'], new Date(dataArray[i]['min']), new Date(dataArray[i]['max'])]]);

		}

		let options = {
			timeline: { 
				showRowLabels: false 
			},
			backgroundColor: '#eee'
		};

		chart.draw(dataTable, options);
	}
}