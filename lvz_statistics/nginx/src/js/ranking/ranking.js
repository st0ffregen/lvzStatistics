let currentRankingDate = new Date();

async function rankingFunction(direction, step = null) {
    showLoader();
    currentRankingDate = calculateDateToGetDataFor(direction, step, currentRankingDate);
    prepareSiteForRanking();

    const response = await fetch('api/ranking?dateBackInTime=' + currentRankingDate.toISOString().slice(0, -14)); //slices T02:02:21.400Z
    const fetchedData = await response.json();

    let newRankingInnerHTML = processRankingData(fetchedData);
    writeChangesToDom(newRankingInnerHTML);
    writeDateToDomElement('go-back-in-time-date-ranking', currentRankingDate);
    removeLoader();
}




function prepareSiteForRanking() {
    let rankingDiv = document.getElementsByClassName('ranking')[0];
    let rankingSectionDiv = rankingDiv.getElementsByClassName('rankingSection')[0];
    rankingSectionDiv.innerHTML = '';
    rankingDiv.style.display = "block";

    //delete arrow and footer
    let arrow = document.getElementsByClassName('upArrowButtonDiv')[0];
    let footer = document.getElementsByClassName('footer')[0];
    arrow.style.display = 'none';
    footer.style.display = 'none';
}


function writeChangesToDom(newRankingInnerHTML) {
    let rankingDiv = document.getElementsByClassName('ranking')[0];
    let rankingSectionDiv = rankingDiv.getElementsByClassName('rankingSection')[0];
    rankingSectionDiv.innerHTML = newRankingInnerHTML;
    let arrow = document.getElementsByClassName('upArrowButtonDiv')[0];
    let footer = document.getElementsByClassName('footer')[0];
    arrow.style.display = 'block';
    footer.style.display = 'block';
}


function processRankingData(fetchedData) {
    let newRankingInnerHTML = '';
    let authorArray = [];

    for (let i = 0; i < fetchedData.length; i++) {

        let diff = fetchedData[i]['rankingScoreDiff'];
        let description = '';
        let color = '';

        if (diff >= 50) {
            description = 'rising';
            color = "#32CD32";
        } else if (diff >= 10) {
            description = 'ascending';
            color = "#6B8E23";
        } else if (diff < 10 && diff > -10) {
            description = 'stagnating';
            color = "#FFA500";
        } else if (diff <= -50) {
            description = 'falling';
            color = "#FF0000";
        } else if (diff <= -10) {
            description = 'decending';
            color = "#8B0000";
        }

        if (diff > -1) {
            diff = "+" + diff.toString();
        }

        authorArray.push({
            'name': fetchedData[i]['name'],
            'score': fetchedData[i]['rankingScore'].toString(),
            'color': color,
            'description': description,
            'diff': diff
        });
    }

    authorArray.sort(function (a, b) {
        return b.score - a.score;
    });

    let scoreOfLastDataIndex = 0;

    for (let i = 0; i < authorArray.length; i++) {

        if (i !== 0 && authorArray[i]['score'] < 0 && scoreOfLastDataIndex >= 0) { //put danger zone
            newRankingInnerHTML += '<hr><h1 class="danger-zone">!!!DANGER ZONE!!!</h1><div class=\"danger\">';
        }

        newRankingInnerHTML += '<div class="ranks"><span class="rankName">' + authorArray[i]['name'] + '</span><span class="rankDescription">' + authorArray[i]['score'] + '</span><span class="rankAdjective" style="color: ' + authorArray[i]['color'] + ';">' + authorArray[i]['description'] + '</span><span class="rankDiff">' + authorArray[i]['diff'] + ' </span></div>';
        scoreOfLastDataIndex = authorArray[i]['score'];
    }

    newRankingInnerHTML += '</div>'; //end danger zone div
    return newRankingInnerHTML;
}


function showRanking() {

    document.getElementsByClassName("graphContent")[0].style.display = "none";
    topFunction();
    rankingFunction('today');

}


function hideRanking() {
    document.getElementsByClassName("ranking")[0].style.display = "none";
    document.getElementsByClassName("graphContent")[0].style.display = "block";
    topFunction();
}

