# Done
* before download: delete links which do not start with http(s)?://(www.)?lvz.de/
* before download: strip beginning of url (e.g http://lvz.de/ein-artikel to /ein-artikel) via replaceUrls.py script
* before download: remove /Sportbuzzer/HC-Leipzig/Spielberichte/HC-Leipzig-siegen-klar-gegen-TSV-Birkenau because it redirects infinitely
* before merge: check for duplicated and remove duplicates
  * url: select * from (select * from main.articles UNION select * from main2.articles) group by url having count(id) >1;
  * contextTags: select * from (select * from main.articles UNION select * from main2.articles) group by contextTag having count(id) >1;
* merged downloadedArticles-X.db to ../../data_sanitization/all_downloaded_articles.db

# To be done
* logs von -6.log checken, gab integrity errors

# other
* what replaceUrls.py does can probably be archived in sql too
* articles.db stores urls to all articles
* example_database_for_downloaded_articles is empty database with schema provided for downloading the articles
* information about download speed can be seen in checkStatusCodes.py

## infos ueber den datensatz 5 (-5.db)
* insgesamt: 63383
* nicht frei: 40658
	* nicht frei und lvz: 39768
	* nicht frei und nicht lvz: 890
* frei: 22725
	* frei und lvz: 6652
	* frei und nicht lvz: 16073
* lvz: 46420
* nicht lvz: 16963