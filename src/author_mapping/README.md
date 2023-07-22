# Done
## Author Mapping
* verknuepfung autoren zu autorenkuerzeln
  * fuzzy matching
  * direktes matching ueber anfangsbuchstaben des vornamens und des nachnamens vergleichen mit kürzel
  * bei beidem statitische sigifikanz maß, wenn es mehr als ein match gibt

# To be done
* verknuepfung autoren zu autorenkuerzeln
  * kürzels und atoren rauswerfen, die nur ein paar Mal vorkommen.
  * zeilich abhängies mapping wenn applying vom algorithmus, damit abbrs mehrfach vergeben werden können
    * evtl. hier "article count über Zeit"-Verteilung von autor und abbr abgleichen und diff errechnen 
  * enablen, dass es abbrs gibt ohne autor name (z.B. joka)
  * evtl. enablen, dass autoren mehr als eine abbr haben dürfen
  * könnte noch ressortzugehörigkeit einbeziehen
    * mal plotten, ob es nicht ressorts gibt, wo es fast immer nur kürzel gibt (sport). falls ja, muss ich damit umgehen
  * könnte into account taken dass wenn es schon ein matching gibt und das zeitlich nahe ist, die chance erhöt, dass die abbr wieder auf den schon gefundenen namen matched
  * auch beachten, dass keine zwei autoren auf die selbe abbr mappen können wenn zeitlich nah beieinander (und bei autor:innen threshold an geschrieben artikel reached haben)
    * könnte aber auch sein, dass die lvz einfach nur die abbr geändert hat
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

