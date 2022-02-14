import sqlite3
import json
import re
import sys
import time
import logging
import traceback
from datetime import datetime

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


class Article:
    def __init__(self, url, context_tag, organization, author_array, author_is_abbreviation_array, genre,
                 article_namespace_array,
                 published_at, modified_at, is_free, headline, text):
        self.url = url
        self.context_tag = context_tag
        self.organization = organization
        self.author_array = author_array
        self.author_is_abbreviation_array = author_is_abbreviation_array
        self.genre = genre
        self.article_namespace_array = article_namespace_array
        self.published_at = published_at
        self.modified_at = modified_at
        self.is_free = is_free
        self.headline = headline
        self.text = text


def configureLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    file_handler = logging.FileHandler('../logs/retrieveDataFromArticle.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def loadDownloadedData(databaseName, limit, offset):
    con = sqlite3.connect(databaseName)
    cur = con.cursor()
    cur.execute('select url, contextTag from articles order by id desc limit ' + str(limit) + ' offset ' + str(offset))
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
    return [i for i in articleNamespace if i]  # remove empty strings


def getData(json, key):
    try:
        return json[key]
    except KeyError:
        return None


def removeUnwantedPunctuation(string):
    string = string.strip()

    for punctuation in punctuationBlocklist:
        if string[:-1] == punctuation:
            string = string[1:]
        if string[-1:] == punctuation:
            string = string[:-1]

    return string.strip()


def getAuthorStringSecure(articleBody, url):  # only recognize authors after schema: "Von autorName"
    lastCharacters = articleBody[-30:]

    for redaktionAbbrevation in redaktionsAuthorList:
        if lastCharacters.endswith(redaktionAbbrevation):
            return redaktionAbbrevation, False

    if 'Von' not in lastCharacters:
        # raise AuthorError(f'No \'Von\' in last characters for {url}')
        return None, None

    partAfterVon = lastCharacters.split('Von')[-1:][0]
    authorParts = partAfterVon.split(' ')
    authorName = ''

    for part in authorParts:
        authorName += ' ' + removeUnwantedPunctuation(part)

    authorName = authorName.strip()
    authorArray = []
    author_is_abbreviation_array = []

    if '/' in authorName:
        authorNameSplit = authorName.split('/')
    elif ' und ' in authorName:
        authorNameSplit = authorName.split(' und ')
    elif ' , ' in authorName:
        authorNameSplit = authorName.split(' , ')
    else:
        authorNameSplit = [authorName]



    for split in authorNameSplit:
        if ' ' not in split and len(split) > 1 and len(split) < 6:
            if split.lower() == 'lvz':
                split = 'LVZ'
            authorArray.append(split)
            author_is_abbreviation_array.append(True)
            continue

        elif re.match('\w{1}\. \w{1}\.', split): # commonly used abbreviations (e.g. "F. D.")
            authorArray.append(split)
            author_is_abbreviation_array.append(True)
            continue

        elif len(split) == 0 or len(split) > 25:
            return None, None

        else:
            authorArray.append(split)
            author_is_abbreviation_array.append(False)


    return authorArray, author_is_abbreviation_array


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



def save_to_database(articles, logger):
    con = sqlite3.connect('../data/articles_with_basic_information.db')
    cur = con.cursor()
    global failed


    for article in articles:
        if article is not None:
            try:
                updated_at = datetime.utcnow().isoformat()
                cur.execute('insert into articles values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (None, article.url, article.context_tag, article.organization, str(article.author_array),
                             str(article.author_is_abbreviation_array),
                             article.genre, str(article.article_namespace_array), article.published_at, article.modified_at,
                             article.is_free, article.headline, article.text, updated_at, updated_at))
            except sqlite3.IntegrityError as e:
                logger.warning(f'error for article {article.url} : {e}')
                failed += 1
    con.commit()



def aggregateData(article, logger):
    global success
    global failed
    global notLVZ

    try:
        jsonContent = json.loads(article['contextTag'])

        organization = jsonContent['author']['name'].lower()

        if organization != 'lvz':
            notLVZ += 1

        articleNamespace = getArticleNamespace(article['url'])
        genre = getData(jsonContent, 'genre')
        datePublished = getData(jsonContent, 'datePublished')
        dateModified = getData(jsonContent, 'dateModified')
        headline = getData(jsonContent, 'headline')
        text = getData(jsonContent, 'articleBody')
        isFree = getData(jsonContent, 'isAccessibleForFree')
        if text is not None:
            authorArray, author_is_abbreviation_array = getAuthorStringSecure(text, article["url"])
        else:
            authorArray, author_is_abbreviation_array = None, None


        article_object = Article(article['url'], article['contextTag'], organization, authorArray, author_is_abbreviation_array,
                                 genre, articleNamespace, datePublished, dateModified, isFree, headline, text)

        logger.info(f'Successfully aggregated data for {article["url"]}')
        success += 1
        return article_object
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

    for l in range(0, 53):
        offset = l * 7000
        limit = 7000
        logger.info('start run from ' + str(offset) + ' to ' + str(offset + limit))
        articles = loadDownloadedData('../data/all_downloaded_articles.db', limit, offset)
        articles_for_db = []
        for article in articles:
            articles_for_db.append(aggregateData(article, logger))

        save_to_database(articles_for_db, logger)


    print('success: ' + str(success))
    print('failed: ' + str(failed))
    print('notLVZ: ' + str(notLVZ))


if __name__ == '__main__':
    main()
