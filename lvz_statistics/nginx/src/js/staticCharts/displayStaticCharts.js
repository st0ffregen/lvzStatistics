let currentGraphContentDate = new Date();
const allCharts = [];


async function displayMinAuthor() {
    let data = await fetchApi('minAuthor');

    if (data.length === 0) return;

    document.getElementById("authorP").innerHTML = "Nur Autor*innen mit mehr als " + data['minAuthor'] + " Artikeln miteinbezogen";
}

async function displayMinRessort() {
    let data = await fetchApi('minRessort');

    if (data.length === 0) return;

    document.getElementById("ressortP").innerHTML = "Nur Ressorts mit mehr als " + data['minRessort'] + " Artikeln miteinbezogen";
}

async function displayDate() {
    let data = await fetchApi('date');

    if (data.length === 0) return;

    let date = new Date(data['date']);
    document.getElementById("dateP").innerHTML = "Zuletzt aktualisiert: " + date.toLocaleString();
}

async function displayArticlesTimeline(date, chartFontSize) {
    let fetchedData = await fetchApi('test');
    console.log(fetchedData)
    if (fetchedData.includes('error')) return;

    let articlesTimelineChart = document.getElementById('articlesTimelineChart');
    let chartData = convertFinancialData(fetchedData, 'Anzahl Artikel');
    financialChart(articlesTimelineChart, chartData, 'MMM yyyy', chartFontSize);
}

async function displayArticlesTimelineDerivative(date, chartFontSize) {
    let fetchedData = await fetchApi('articlesTimeline', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let articlesTimelineDerivativeChart = document.getElementById('articlesTimelineDerivativeChart');
    let chartData = convertFinancialDataDerivative(fetchedData, 'Anzahl Artikel pro Monat');
    financialChart(articlesTimelineDerivativeChart, chartData, 'MMM yyyy', chartFontSize);
}

async function displayActiveMembers(date, chartFontSize) {
    let fetchedData = await fetchApi('activeMembers', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let activeMembersChart = document.getElementById('activeMembersChart');
    let chartData = convertFinancialDataDerivative(fetchedData, 'Aktive Autor*innen pro Quartal');
    financialChart(activeMembersChart, chartData, 'q yyyy', chartFontSize);
}

async function displayActiveMembersWithFourArticles(date, chartFontSize) {
    let fetchedData = await fetchApi('activeMembersWithFourArticles', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let activeMembersWithFourArticlesChart = document.getElementById('activeMembersWithFourArticlesChart');
    let chartData = convertFinancialDataDerivative(fetchedData, 'Aktive mit mind. 4 Artikeln in dem Quartal');
    financialChart(activeMembersWithFourArticlesChart, chartData, 'q yyyy', chartFontSize);
}

async function displayGoogleAuthorTimelineChart(date) {
    let fetchedData = await fetchApi('authorTimeline', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let authorTimelineChart = document.getElementById('authorTimelineChart');
    googleTimeline(authorTimelineChart, fetchedData);
}

async function displayAuthorTopListChart(date, chartFontSize) {
    let fetchedData = await fetchApi('authorTopList', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let authorTopListChart = document.getElementById('authorTopListChart');
    barChart(authorTopListChart, fetchedData, 'bar', 'Artikel pro Autor*in', chartFontSize, true);
}

async function displayAuthorAverageChart(date, chartFontSize) {
    let fetchedData = await fetchApi('authorAverage', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let authorAverageChart = document.getElementById('authorAverageChart');
    barChart(authorAverageChart, fetchedData, 'bar', 'Ø Zeichen pro Autor*in', chartFontSize, true);
}

async function displayMostArticlesPerTimeChart(date, chartFontSize) {
    let fetchedData = await fetchApi('mostArticlesPerTime', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let mostArticlesPerTimeChart = document.getElementById('mostArticlesPerTimeChart');
    barChart(mostArticlesPerTimeChart, fetchedData, 'bar', 'Zeit zwischen zwei Artikeln in Tagen', chartFontSize, true);
}

async function displayAverageCharactersPerDayChart(date, chartFontSize) {
    let fetchedData = await fetchApi('averageCharactersPerDay', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let averageCharactersPerDayChart = document.getElementById('averageCharactersPerDayChart');
    barChart(averageCharactersPerDayChart, fetchedData, 'bar', 'Ø Zeichen pro Tag', chartFontSize, true);
}

async function displayGoogleRessortTimelineChart(date) {
    let fetchedData = await fetchApi('ressortTimeline', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let ressortTimelineChart = document.getElementById('ressortTimelineChart');
    googleTimeline(ressortTimelineChart, fetchedData);
}

async function displayTopAuthorsPerRessortChart(date, chartFontSize) {
    let fetchedDataTopAuthorsPerRessort = await fetchApi('topAuthorsPerRessort', 'dateBackInTime', date);

    if (fetchedDataTopAuthorsPerRessort.length === 0) return;

    let fetchedDataRessortTopList = await fetchApi('ressortTopList', 'dateBackInTime', date);

    if (fetchedDataRessortTopList.length === 0) return;

    let ressortTopListChart = document.getElementById('ressortTopListChart');
    let tooltipFunctionToDisplayTopAuthors = customTooltip(fetchedDataTopAuthorsPerRessort);
    barChart(ressortTopListChart, fetchedDataRessortTopList, 'bar', 'Artikel pro Ressort', chartFontSize, false, tooltipFunctionToDisplayTopAuthors);
}

function displayRessortArticlesTimelineDerivativeChart(colorArray, fetchedData, firstRessortToBeDisplayed, secondRessortToBeDisplayed, chartFontSize) {
    let ressortArticlesTimelineDerivativeChart = document.getElementById('ressortArticlesTimelineDerivativeChart');

    let datasets = [];
    for (let i = 0; i < fetchedData.length; i++) {
        if (i === firstRessortToBeDisplayed || i === secondRessortToBeDisplayed) {
            let newDataset = convertFinancialDataDerivative(fetchedData[i]['articles'], fetchedData[i]['ressort'], colorArray[i], 0);
            datasets.push(newDataset[0]);
        } else {
            let newDataset = convertFinancialDataDerivative(fetchedData[i]['articles'], fetchedData[i]['ressort'], colorArray[i], 1);
            datasets.push(newDataset[0]);
        }
    }

    financialChart(ressortArticlesTimelineDerivativeChart, datasets, 'q yyyy', chartFontSize);
}

function displayRessortArticlesTimelineChart(colorArray, fetchedData, firstRessortToBeDisplayed, secondRessortToBeDisplayed, chartFontSize) {
    let ressortArticlesTimelineChart = document.getElementById('ressortArticlesTimelineChart');
    let datasets = [];
    for (let i = 0; i < fetchedData.length; i++) {

        if (i === firstRessortToBeDisplayed || i === secondRessortToBeDisplayed) {
            let newDataset = convertFinancialData(fetchedData[i]['articles'], fetchedData[i]['ressort'], colorArray[i], 0);
            datasets.push(newDataset[0]);
        } else {
            let newDataset = convertFinancialData(fetchedData[i]['articles'], fetchedData[i]['ressort'], colorArray[i], 1);
            datasets.push(newDataset[0]);
        }

    }
    financialChart(ressortArticlesTimelineChart, datasets, 'MMM yyyy', chartFontSize);
}

async function displayRessortArticlesTimelineCharts(date, chartFontSize) {

    chartFontSize = chartFontSize - 1; // many labels

    let fetchedData = await fetchApi('ressortArticlesTimeline', 'dateBackInTime', date);
    let fetchedDerivativeData = await fetchApi('ressortArticlesTimelineDerivative', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let colorArray = getRandomHexColorArray(fetchedData.length);

    let firstRessortToBeDisplayed = Math.floor(Math.random() * fetchedData.length);
    let secondRessortToBeDisplayed = 0;

    do { //verhindern dass das selbe ressort random ausgewaehlt wird
        secondRessortToBeDisplayed = Math.floor(Math.random() * fetchedData.length);
    } while (firstRessortToBeDisplayed === secondRessortToBeDisplayed);

    displayRessortArticlesTimelineChart(colorArray, fetchedData, firstRessortToBeDisplayed, secondRessortToBeDisplayed, chartFontSize);
    displayRessortArticlesTimelineDerivativeChart(colorArray, fetchedDerivativeData, firstRessortToBeDisplayed, secondRessortToBeDisplayed, chartFontSize);
}

async function displayRessortAverageChart(date, chartFontSize) {
    let fetchedData = await fetchApi('ressortAverage', 'dateBackInTime', date);

    if (fetchedData.includes('error')) return;

    let ressortAverageChart = document.getElementById('ressortAverageChart');
    barChart(ressortAverageChart, fetchedData, 'bar', 'Ø Zeichen pro Ressort', chartFontSize, true);
}

function generateGraphs(date, chartFontSize) {

    showLoader();
    destroyAllExistingCharts();
    displayArticlesTimeline(date, chartFontSize);
/**
    displayMinAuthor();
    displayMinRessort();
    displayDate();

    displayArticlesTimelineDerivative(date, chartFontSize);
    displayActiveMembers(date, chartFontSize);
    displayActiveMembersWithFourArticles(date, chartFontSize);
    displayGoogleAuthorTimelineChart(date);
    displayAuthorTopListChart(date, chartFontSize);
    displayAuthorAverageChart(date, chartFontSize);
    displayMostArticlesPerTimeChart(date, chartFontSize);
    displayAverageCharactersPerDayChart(date, chartFontSize);
    displayGoogleRessortTimelineChart(date);
    displayTopAuthorsPerRessortChart(date, chartFontSize);
    displayRessortArticlesTimelineCharts(date, chartFontSize).then(r => removeLoader()); // not the most beautiful way
    displayRessortAverageChart(date, chartFontSize);
**/

}


function displayGraphContent(direction, step) {
    let chartFontSize = calculateChartFontSize();
    currentGraphContentDate = calculateDateToGetDataFor(direction, step, currentGraphContentDate);
    writeDateToDomElement('go-back-in-time-date-graph-content', currentGraphContentDate);
    generateGraphs(currentGraphContentDate.toISOString().slice(0, -14), chartFontSize);
}

function destroyAllExistingCharts() {
    for (const chart of allCharts) {
        chart.destroy();
    }
}


window.onresize = function() { //traffic aufwending
    let date = currentGraphContentDate.toISOString().slice(0, -14);
	displayGoogleAuthorTimelineChart(date);
	displayGoogleRessortTimelineChart(date);
}
