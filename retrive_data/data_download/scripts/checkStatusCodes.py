import requests
import sqlite3
import random
import threading
import time
import concurrent.futures
import itertools


# irengdwo bei 110 requests innerhalb ein paar Sekunden  wird es akamai zu bunt
#   bei 20 sowie bei sechs threads ist da das selbe ergebniss zu beobachten
#   muss herausfinden was akamai fpr eine max an Threads/Minute verlangt
#   retry header sagt übrigens fünf sekunden aber das ist viel zu kurz, bekomme direkt wieder 429er

# 882 Urls mit 12 Threads und 30 sekunden warten geht es. Zeit total 6m35.179s
# Also 395 Sekunden und eine URL braucht also ca. 395/882 = 0.45 Sekunden pro URL
# D.h. alle ca. 360000 Artikel in 162000 Sekunden, 2700 Mins, 45 Stunden. Wenn ich über Nacht intensive Phasen von je 6 Stunden mache, 
# komme ich auf 7.5 Tage 


def connectToDb():
	global con
	try:
		con = sqlite3.connect('articles.db')
	except sqlite3.OperationalError as e:
		logger.warn("error while establishing connection to db: {e}")
		logger.warn("exiting")
		logger.warn(sys.exc_info())
		sys.exit(1)


def getCursor():
	global cur
	try:
		cur = con.cursor()
	except sqlite3.OperationalError as e:
		logger.warn("error while creating cursor for connection: {e}")
		logger.warn("exiting")
		logger.warn(sys.exc_info())
		sys.exit(1)


def download(url):

	res = requests.get('https://www.lvz.de' + url)
		
	if res.status_code == 429:
		return 'failed ' + str(res.status_code) + ',' + res.headers['Retry-After'] + ',https://www.lvz.de' + url
		time.sleep(int(res.headers["Retry-After"]) + 10)
		res = requests.get('https://www.lvz.de' + url)
	elif res.status_code != 200:
		return 'failed ' + str(res.status_code) + ',' + res.headers['Retry-After'] + ',https://www.lvz.de' + url

	return url.text



def main():
	connectToDb()
	getCursor()

	randomUrlList = []

	for _ in range(0,1000):
		randomNumber = random.randint(1,340000)
		cur.execute('select articleUrl from articles where id = ' + str(randomNumber))
		url = cur.fetchone()
			
		if url is None or len(url) == 0 or "lvz.de" in url[0]: 
			print(f"error: article not valid {url}")
			continue

		randomUrlList.append(url[0])

	print(len(randomUrlList))

	for i in range(1,11):

		with concurrent.futures.ThreadPoolExecutor(max_workers=(4+4+4+4)) as executor:
			results = [executor.submit(download, url) for url in randomUrlList[(100 * i - 100): (100*i)]]
			
			for f in concurrent.futures.as_completed(results):
				print(f.result())

		print('sleep')
		time.sleep(30)
	

if __name__ == '__main__':
	main()