#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
import logging
import sqlite3
import sys

baseUrl = 'https://www.lvz.de/Archiv/'
totalArticleCount = 0
logger = None
con = None
cur = None

def connectToDb():
	global con
	try:
		con = sqlite3.connect('../data/articles.db')
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

def configureLogger():
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)

	formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

	file_handler = logging.FileHandler('../logs/scrapeArchive.log')
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)

	return logger


def writeArticleListToDb(articleDivs):
	for article in articleDivs:
		linkToArticle = article.find('a', {'class': 'pdb-full-newsticker-teaser-breadcrumb-headline-title-link'})['href']
		try:
			cur.execute('insert into articles values (?,?)', (None, linkToArticle))
		except sqlite3.IntegrityError as e:
			logger.warn("error while inserting values: {e}")

def scrapeSinglePage(year, month, day):
	global totalArticleCount
	url = baseUrl + str(year) + '/' + str(month).zfill(2) + '/' + str(day).zfill(2)
	logger.info('scrape ' + url)

	try:
		soup = BeautifulSoup(urlopen(url).read(), 'html.parser')
	except HTTPError as e:
		logger.warn("Http Error occurred! {e}")
		return

	articleDivs = soup.find_all('div', {'class': 'pdb-full-newsticker-teaser'})
	articleCount = len(articleDivs)
	totalArticleCount += articleCount
	logger.info('found ' + str(articleCount) + ' on ' + str(day) + '.' + str(month) + '.' + str(year))

	if articleCount > 0:
		writeArticleListToDb(articleDivs)

def scrapeArchive():
	for year in range(2021, 2022):
		for month in range(1, 13):
			for day in range(1, 32):
				if year == 2021 and month < 10:
					continue
				scrapeSinglePage(year, month, day)

			con.commit()

	con.commit()
	logger.info('total article count ' + str(totalArticleCount))

def main():
	global logger
	logger = configureLogger()

	logger.info('Start scraper')
	connectToDb()
	getCursor()

	scrapeArchive()

	cur.close()
	con.close()
	logger.info('Terminate scraper')


if __name__ == '__main__':
	main()