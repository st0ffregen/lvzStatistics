import sqlite3
import json
import re
import sys
import time
import logging
import traceback


redaktionsAuthorList = ['Redaktion.', 'red.']
punctuationBlocklist = ['»', '-', '“', '“']
success = 0
failed = 0
notLVZ = 0


class AuthorError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'AuthorError, {0} '.format(self.message)
        else:
            return 'AuthorError has been raised'


def configureLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    file_handler = logging.FileHandler('logs/retrieveDataFromArticle.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def loadDownloadedData(databaseName, limit, offset):
	con = sqlite3.connect(databaseName)
	cur = con.cursor()
	cur.execute('select url, contextTag from articles limit ' + str(limit) + ' offset ' + str(offset))
	entries = cur.fetchall()
	articles = []
	for row in entries:
		articles.append({'url': row[0], 'contextTag': row[1]})

	return articles


def getArticleNamespace(url):
	matches = re.findall('(.*\/){1,7}(?=.{4,})', url)

	if len(matches) != 1:
		raise Exception(f'two many/few matches for {url}: {matches}')

	articleNamespace = matches[0].split('/')
	return [i for i in articleNamespace if i] # remove empty strings


def getData(json, key):
	return json[key]


def removeUnwantedPunctuation(string):

	string = string.strip()

	for punctuation in punctuationBlocklist:
		if string[:-1] == punctuation:
			string = string[1:]
		if string[-1:] == punctuation:
			string = string[:-1]

	return string.strip()


def getAuthorStringSecure(articleBody, url): # only recognize authors after schema: "Von autorName"
	lastCharacters = articleBody[-30:]

	for redaktionAbbrevation in redaktionsAuthorList:
		if lastCharacters.endswith(redaktionAbbrevation):
			return redaktionAbbrevation, False

	if 'Von' not in lastCharacters:
		raise AuthorError(f'No \'Von\' in last characters for {url}')


	partAfterVon = lastCharacters.split('Von')[-1:][0]
	authorParts = partAfterVon.split(' ')
	authorName = ''

	for part in authorParts:
		authorName += ' ' + removeUnwantedPunctuation(part)

	authorName = authorName.strip()

	if ' ' not in authorName and len(authorName) > 1 and len(authorName) < 6:
		return authorName, True

	if (len(authorName) < 6 or len(authorName) > 25) and '/' not in authorName:
		raise AuthorError(f'Too long/short author name for {url}: {authorName}')

	return authorName, False


# def getAuthorString(articleBody, url):
# 	lastCharacters = articleBody[-25:]

# 	for redaktionAbbrevation in redaktionsAuthorList:
# 		if lastCharacters.endswith(redaktionAbbrevation):
# 			return redaktionAbbrevation, False

# 	authorParts = lastCharacters.split('.')[-1:][0].split(' ')
# 	authorName = ''

# 	for part in authorParts:
# 		authorName += ' ' + removeUnwantedPunctuation(part)

# 	authorName = authorName.strip()
	
# 	if authorName.startswith('Von'):
# 		authorName = authorName[3:].strip()

# 	if ' ' not in authorName and len(authorName) > 1 and len(authorName) < 6:
# 		return authorName, True

# 	if (len(authorName) < 6 or len(authorName) > 20) and '/' not in authorName:
# 		raise AuthorError(f'Too long/short author name for {url}: {authorName}')

# 	return authorName, False


def getAuthors(articleBody, url):
	authorString, isAbbreviation = getAuthorStringSecure(articleBody, url)
	return authorString.split('/'), isAbbreviation
	

def aggregateData(article, logger):
	global success
	global failed
	global notLVZ

	try:
		jsonContent = json.loads(article['contextTag'])

		orgaAuthor = jsonContent['author']['name'].lower()

		if orgaAuthor != 'lvz':
			logger.info(f'Author is {orgaAuthor} not lvz. Skip. {article["url"]}')
			notLVZ += 1
			return

		articleNamespace = getArticleNamespace(article['url'])
		genre = getData(jsonContent, 'genre')
		datePublished = getData(jsonContent, 'datePublished')
		dateModified = getData(jsonContent, 'dateModified')
		headline = getData(jsonContent, 'headline')
		text = getData(jsonContent, 'articleBody')
		authorArray, isAbbreviation = getAuthors(text, article["url"])
		isFree = getData(jsonContent, 'isAccessibleForFree')
		
		logger.info(f'Successfully aggregated data for {article["url"]}')
		success += 1
	except AuthorError as e:
		logger.warning(f'Something went wrong for {article["url"]}: {e}')
		logger.warning(traceback.format_exception(*sys.exc_info()))
		authorArray = None
		isAbbreviation = None
		failed += 1
		return


	except Exception as e:
		logger.warning(f'Something went wrong for {article["url"]}: {e}')
		logger.warning(traceback.format_exception(*sys.exc_info()))
		failed += 1
		return


def main():
	logger = configureLogger()

	for i in range(3, 4):
		for l in range(0, 17):
			offset = l * 7000
			limit = 7000
			articles = loadDownloadedData('results/downloadedArticles-' + str(i) + '.db', limit, offset)
			for article in articles:
				aggregateData(article, logger)
			
		

	print('success: ' + str(success))
	print('failed: ' + str(failed))
	print('notLVZ: ' + str(notLVZ))


if __name__ == '__main__':
	main()
