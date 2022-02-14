# Done
## DB Sanitation
* delete links which do not start with http(s)?://(www.)?lvz.de/
* strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* remove not unique urls
* artikel vor 2010 loeschen, dann habe ich genau 12 Jahre LVZ
* alle artikel in articles_with_basic_information ueberfuehren

# To be done
* alle artikel nochmal runterladen um autor anhand von kursiv geschriebenen text zu filtern
    * autor erstmal anhand von securen schema "Von abc" herausfinden um Menge zu verkleinern
    * mit dem kursiv schema koennen keine lvz plus artikel erkannt werden, muss manuell gemacht werden (oder account anlegen)!
    * damit warten, falls ich nochmal was runterladen muss
* verknuepfung autoren zu autorenkuerzeln

# other
* analyzeDataAndMoveToElastic.log can probably be removed

## infos ueber datensatz (all_downloaded_articles.db)
* free: 296903
* not free: 65718
* from lvz: 197532
* not from lvz: 165089

## infos ueber skript (retrieveDataFromArticle.py)
* notLVZ sollte mit "nicht lvz" des datensatzes uebereinstimmen
* "nicht frei und lvz" - notFreeAndLVZ = teilmenge1 von failed
* "frei und lvz" - success = teilmenge2 von failed
* teilmenge1 + teilmenge2 = failed
* Sucessrate fuer -5.db ca. 96%
* Sucessrate fuer -1.db ca. 2,5%