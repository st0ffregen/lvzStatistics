# Done
## DB Sanitation
* delete links which do not start with http(s)?://(www.)?lvz.de/
* strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* remove not unique urls

# To be done
* delete articles who not belong to lvz (via key-value-pair in context tag)
* alle artikel nochmal runterladen um autor anhand von kursiv geschriebenen text zu filtern
    * autor erstmal anhand von securen schema "Von abc" herausfinden um Menge zu verkleinern
    * mit dem kursiv schema koennen keine lvz plus artikel erkannt werden, muss manuell gemacht werden (oder per benutzer, aber lieber nicht)!
    * damit warten, falls ich nochmal was runterladen muss

# other
* what replaceUrls.py does can probably be archived in sql too
* analyzeDataAndMoveToElastic can probably be removed


## infos ueber skript (retrieveDataFromArticle.py)
* notLVZ sollte mit "nicht lvz" des datensatzes uebereinstimmen
* "nicht frei und lvz" - notFreeAndLVZ = teilmenge1 von failed
* "frei und lvz" - success = teilmenge2 von failed
* teilmenge1 + teilmenge2 = failed
* Sucessrate fuer -5.db ca. 96%
* Sucessrate fuer -1.db ca. 2,5%