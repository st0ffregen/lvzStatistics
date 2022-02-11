# this scripts changes urls like https://www.lvz.de/blablabla to format /blablabla
import csv
import sqlite3
cur = None
con = None

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


def replace():
	with open('articleBeginningWithWWW_LVZ_DE.csv', mode ='r') as file:
		csvFile = csv.DictReader(file)
		for lines in csvFile:
			print(lines['id'] + ' ' + lines['articleUrl'])
			url = lines['articleUrl'].replace('http://www.lvz.de','')
			print('update articles set articleUrl = "' + url + '" where articleUrl = "' + lines['articleUrl'] + '" and id = ' + lines['id'])
			cur.execute('update articles set articleUrl = "' + url + '" where articleUrl = "' + lines['articleUrl'] + '" and id = ' + lines['id'])
			if cur.rowcount != 1:
				con.rollback()
				print('errorr!!1')
			else:
				print('updated: ' + str(cur.rowcount))

		con.commit()


def main():
	connectToDb()
	getCursor()

	replace()

	cur.close()
	con.close()


if __name__ == '__main__':
	main()