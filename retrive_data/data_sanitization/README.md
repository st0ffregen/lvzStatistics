# Done
## DB Sanitation
* delete links which do not start with http(s)?://(www.)?lvz.de/
* strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* remove not unique urls

# To be done
* erkenntlich machen der  articles from other creators via contextTag not like '"author":{"@type":"Organization","name":"LVZ"}'
* alle artikel nochmal runterladen um autor anhand von kursiv geschriebenen text zu filtern
    * autor erstmal anhand von securen schema "Von abc" herausfinden um Menge zu verkleinern
    * mit dem kursiv schema koennen keine lvz plus artikel erkannt werden, muss manuell gemacht werden (oder per benutzer, aber lieber nicht)!
    * damit warten, falls ich nochmal was runterladen muss

# other
* analyzeDataAndMoveToElastic can probably be removed

# infos ueber datensatz (all_downloaded_articles.db)
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