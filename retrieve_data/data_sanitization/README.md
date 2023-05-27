# Done
## DB Sanitation
* delete links which do not start with http(s)?://(www.)?lvz.de/
* strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* remove not unique urls
* artikel vor 2010 loeschen, dann habe ich genau 12 Jahre LVZ
* alle artikel in articles_with_basic_information ueberfuehren
* bessere autoren recognition in articles_with_basic_information_improved_author_recognition
  * success: 367705
  * failed: 12
  * notLVZ: 166612
  * select count(*) from articles where organization = 'lvz' and author_array is Null --> 11194

# To be done
* verknuepfung autoren zu autorenkuerzeln
  * fuzzy matching (idee noch nciht ausgereif)
  * direktes matching ueber anfangsbuchstaben des vornamens und des nachnamens vergleichen mit kürzel
  * bei beidem statitische sigifikanz maß, wenn es mehr als ein match gibt
  * könnte noch ressortzugehörigkeit einbeziehen
  * könnte into account taken dass wenn es schon ein matching gibt und das zeitlich nahe ist, die chance erhöt, dass die abbr wieder auf den schon gefundenen namen matched
  * auch beachten, dass keine zwei autoren auf die selbe abbr mappen können wenn zeitlich nah beieinander (und bei autor:innen threshold an geschrieben artikel reached haben)
    * könnte aber auch sein, dass die lvz einfach nur die abbr geändert hat
  * am ende alle abbr und ihr match collecten und dann nochmal gewichten (wenn abbr mehrfach vorkommt, dann wohl wichtiger als eine, die nur einmal vorkommt, aber eine höhere certainty hat)

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

# evtl. noch machen
* autor:innen von aelteren Artikel nachtragen, durch abgleichen vorhandener autor:innen in neueren artikeln
* alle artikel nochmal runterladen um autor anhand von kursiv geschriebenen text zu filtern
    * autor erstmal anhand von securen schema "Von abc" herausfinden um Menge zu verkleinern
    * mit dem kursiv schema koennen keine lvz plus artikel erkannt werden, muss manuell gemacht werden (oder account anlegen)!
    * damit warten, falls ich nochmal was runterladen muss
    * schwierig, weil lvz alles vor 2015 gelöscht hat (Update vom 27.05.23)
         * und es vor allem eh um die alten artikel geht