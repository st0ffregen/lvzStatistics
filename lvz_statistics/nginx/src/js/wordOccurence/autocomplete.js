function initWordOccurrenceAutocomplete(inputField) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    let currentFocus;
    /*execute a function when someone writes in the text field:*/
    inputField.addEventListener("input", async function (e) {
        let a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) {
            return false;
        }
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);

        const split = val.split('\u2795');
        let word = split[split.length - 1].trim();
        let firstPartOfWord = '';

        for (let i=0; i<split.length -1; i++) {
            firstPartOfWord += split[i] + ' \u2795 ';
        }

        firstPartOfWord = firstPartOfWord.toUpperCase();

        const response = await fetch('api/autocomplete?word=' + word);
        const data = await response.json();

        /*for each item in the array...*/
        for (i = 0; i < data.length; i++) {
            /*check if the item starts with the same letters as the text field value:*/
            if (data[i]['occurrence'] > 0) {
                /*create a DIV element for each matching element:*/
                b = document.createElement("DIV");
                /*make the matching letters bold:*/
                //unterteilen der zahl mit punkten
                let numberString = data[i]['occurrence'].toLocaleString("de-DE");

                b.innerHTML = "<strong>" + firstPartOfWord + data[i]['word'].substr(0, val.length) + "</strong>"; //
                b.innerHTML += data[i]['word'].substr(val.length) + "<span class=\"autocomplete-occurrence\">" + numberString + "</span>";
                /*insert a input field that will hold the current array item's value:*/
                b.innerHTML += "<input type='hidden' value='" + firstPartOfWord + data[i]['word'] + "'>";
                /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function (e) {
                    /*insert the value for the autocomplete text field:*/
                    addDataToWordOccurrenceChart(this.getElementsByTagName("input")[0].value);
                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    inputField.value = "";
                    inputField.placeholder = "Geben Sie einen Begriff ein";
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
    });

    /*execute a function presses a key on the keyboard:*/
    inputField.addEventListener("keydown", function (e) {
        let x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            addDataToWordOccurrenceChart(this.value);
            inputField.value = "";
            closeAllLists();
        }
    });

    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (let i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }

    function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        let x = document.getElementsByClassName("autocomplete-items");
        for (let i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inputField) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}