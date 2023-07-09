# Done
## DB Sanitation
* delete links which do not start with http(s)?://(www.)?lvz.de/
* strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* remove not unique urls
* artikel vor 2010 loeschen, dann habe ich genau 12 Jahre LVZ
* alle artikel in articles_with_basic_information ueberfuehren
* autoren recognition in articles_with_author_mapping
  * success: 367710
  * failed: 7
  * notLVZ: 166612
  * select count(*) from articles where organization = 'lvz' and author_array is Null --> 6822

## Author Mapping
* verknuepfung autoren zu autorenkuerzeln
  * fuzzy matching
  * direktes matching ueber anfangsbuchstaben des vornamens und des nachnamens vergleichen mit kürzel
  * bei beidem statitische sigifikanz maß, wenn es mehr als ein match gibt

# To be done
* die author recognition Fälle mit kleinen "v" in "von ..." behandeln
* eineheitliche groß und kleinschreibung bei autoren (zurzeit die mit abbr=null groß geschrieben)
* verknuepfung autoren zu autorenkuerzeln
  * könnte noch ressortzugehörigkeit einbeziehen
  * könnte into account taken dass wenn es schon ein matching gibt und das zeitlich nahe ist, die chance erhöt, dass die abbr wieder auf den schon gefundenen namen matched
  * auch beachten, dass keine zwei autoren auf die selbe abbr mappen können wenn zeitlich nah beieinander (und bei autor:innen threshold an geschrieben artikel reached haben)
    * könnte aber auch sein, dass die lvz einfach nur die abbr geändert hat
  * am ende alle abbr und ihr match collecten und dann nochmal gewichten (wenn abbr mehrfach vorkommt, dann wohl wichtiger als eine, die nur einmal vorkommt, aber eine höhere certainty hat)
  * sql: erstmal alle abbr zu full names mapping in die tabelle, dabei schon articles zu den abbrs connecten
    * dann articles tabelle das unique bei row rausnehmen (evtl. unique row + author_id) um verschiedene autoren pro artikel zuzulassen
    * verknuepfung artikel-autor muss wohl ueber n:m tabelle realisiert werden, weil ich wahrscheinlich erstmal meherer einträge pro autor in autor tabelle habe durch doppelte abbrs
      * ein artikel mit nem full name soll dann auf all diese rows mappen (artikel mit abbrs können 1:m mappen)
  * evtl. pro abbr die top 1-3 autoren nehmen und dann sodoku mäßig vergleichen
  * fehlererkennung: wie viele distinct abbrs gibt es mehr als distinct authors (kann natürlich auch sein, dass es tat. mehr abbrs als 1 pro autor gibt, aber das ist wahrscheinlich die minderheit)
  * alle full names in die db schreiben, auf einen entry der authors table mappen
  * dann auswahl welche abbr, name pairs bleiben sollen und alle einträge der article_authors tabelle entsprechend umbiegen 
  * beim retrievel nochmal checken ob es zwischen Groß und Kleinschreibung unterscheidt (evtl. Benachteiligung adeliger)
  * checken ob die namen signifikant kürzer in der autorenlandschaft vertreten sind als das kürzel --> dann wahrscheinlich kein mapping

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