import sqlite3
import json
import re
import sys
import time
import logging
import traceback
from datetime import datetime
import spacy
import regex

nlp = spacy.load('de_core_news_sm')

redaktionsAuthorList = ['Redaktion.', 'red.']
punctuation_blocklist = ['»', '-', '“', '“', '*']
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

    for punctuation in punctuation_blocklist:
        if string[:-1] == punctuation:
            string = string[1:]
        if string[-1:] == punctuation:
            string = string[:-1]

    return string.strip()


def getAuthorString(article_text):
    article_text = removeUnwantedPunctuation(article_text[-80:])

    # Case 5: Editorial abbreviation
    match = regex.search(r'\.\s+(Redaktion|red)\.', article_text, flags=re.UNICODE)
    if match:
        return ["lvz"], [True]

    # Case 3.1: Single abbreviation with "Von" prefix, separated by a period
    match = regex.search(r'Von\s+([A-Z]\.\s?[A-Z]\.)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1).replace(' ', '')], [True]

    # Case 4.1: Multiple abbreviations with "Von" prefix, separated by a slash
    match = regex.search(r'Von (?=.*\/)((?:[\w.]{2,6}\/){0,3}[\w.]{2,6})$', article_text, flags=re.UNICODE)
    if match:
        names = re.split(r'\s*/\s*', match.group(1))

        # check with spacy that names are not persons
        for name in names:
            if nlp(name)[0].ent_type_ == 'PER':
                return None, None

        return names, [True] * len(names)

    # Case 6.: No author given, texts ends with a period
    match = regex.search(r'\.$', article_text)
    if match:
        return ["lvz"], [True]

    # Case 3.2: Single abbreviation without "Von" prefix
    match = regex.search(r'\.\s+([a-z]+)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1)], [True]


    # Case 2.1: Multiple full names with "Von" prefix
    match = regex.search(r'Von\s+([\p{L}\s-]+)\s+und\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1), match.group(2)], [False, False]

    # Case 2.5: Multiple full names with "Von" prefix, separated by commas and "und"
    match = regex.search(r'Von\s+([\p{L}\s-,]+)\s+und\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        names = re.split(r'\s*,\s*', match.group(1))
        names.append(match.group(2))
        return names, [False] * len(names)

    # Case 2.6: Multiple full names with "Von" prefix, separated by commas
    match = regex.search(r'Von\s+([\p{L}\s-,]+)$', article_text, flags=re.UNICODE)
    if match:
        names = re.split(r'\s*,\s*', match.group(1))

        return names, [False] * len(names)

    # Case 2.4: Multiple full names with "Von" prefix, separated by a slash
    match = regex.search(r'Von\s+([\p{L}\s-/]+)$', article_text, flags=re.UNICODE)
    if match:
        names = re.split(r'\s*/\s*', match.group(1))
        # check with spacy that names are persons
        for name in names:
            if nlp(name)[0].ent_type_ != 'PER':
                return None, None
        return names, [False] * len(names)

    # Case 2.2: Multiple full names without "Von" prefix, separated by a period
    match = regex.search(r'\.\s+([\p{L}\s-]+)\s+und\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1), match.group(2)], [False, False]

    # Case 2.3: Multiple full names without "Von" prefix, missing period
    match = regex.search(r'([\p{L}\s-]+)\s+und\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        names = []
        for group in match.groups():
            doc = nlp(group)

            for ent in doc.ents:
                if ent.label_ == 'PER':
                    names.append(ent.text)

        if names:
            return names, [False] * len(names)

    # Case 1.1: Single full name with "Von" prefix
    match = regex.search(r'Von\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1)], [False]

    # Case 1.2: Single full name without "Von" prefix, separated by a period
    match = regex.search(r'\.\s+([\p{L}\s-]+)$', article_text, flags=re.UNICODE)
    if match:
        return [match.group(1)], [False]

    # Case 1.3: Single full name without "Von" prefix, missing period
    # in this case check if the last words are a name
    # include up to two name parts given that no middle names exists
    last_words = ' '.join(article_text.split()[-4:])
    doc = nlp(last_words)

    for ent in doc.ents:
        if ent.label_ == 'PER':
            return [ent.text], [False]


    return None, None

def getAuthorStringOld(articleBody):
    lastCharacters = articleBody[-80:]

    for redaktionAbbrevation in redaktionsAuthorList:
        if lastCharacters.endswith(redaktionAbbrevation):
            return ['lvz'], False

    if 'Von ' in lastCharacters:
        authorParts = get_author_after_von(lastCharacters)


    authorName = ''

    for part in authorParts:
        authorName += ' ' + removeUnwantedPunctuation(part)

    authorName = authorName.strip()
    authorArray = []
    author_is_abbreviation_array = []

    if '/' in authorName:
        authorNameSplit = authorName.split('/')
    elif ', ' in authorName:
        authorNameSplit = authorName.split(', ')

        if ' und ' in authorNameSplit[-1]: # recognize pattern: "a, b, c und d"
            lastElement = authorNameSplit[-1]
            lastTwoNames = lastElement.split(' und ')
            authorNameSplit = authorNameSplit[:-1]
            authorNameSplit.append(lastTwoNames[0])
            authorNameSplit.append(lastTwoNames[1])

    elif ' und ' in authorName:
        authorNameSplit = authorName.split(' und ')
    else:
        authorNameSplit = [authorName]

    for split in authorNameSplit:
        split = split.strip()
        if ' ' not in split and len(split) > 1 and len(split) < 6:
            if split.lower() == 'lvz':
                split = 'LVZ'
            authorArray.append(split)
            author_is_abbreviation_array.append(True)
            continue

        elif re.match('\w{1}\. \w{1}\.', split):  # commonly used abbreviations (e.g. "F. D.")
            authorArray.append(split)
            author_is_abbreviation_array.append(True)
            continue

        elif len(split) == 0 or len(split) > 25:
            return None, None

        else:
            authorArray.append(split)
            author_is_abbreviation_array.append(False)

    return authorArray, author_is_abbreviation_array


def get_author_after_von(lastCharacters):
    partAfterVon = lastCharacters.split('Von ')[-1:][0]
    authorParts = partAfterVon.split(' ')
    return authorParts


def save_to_database(articles, logger):
    con = sqlite3.connect('../data/articles_with_basic_information.db')
    cur = con.cursor()
    global failed


    for article in articles:
        if article is not None:
            try:
                updated_at = datetime.utcnow().isoformat()

                if article.author_array is not None:
                    article.author_array = str(article.author_array)

                if article.author_is_abbreviation_array is not None:
                    article.author_is_abbreviation_array = str(article.author_is_abbreviation_array)

                if article.article_namespace_array is not None:
                    article.article_namespace_array = str(article.article_namespace_array)

                cur.execute('insert into articles values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (None, article.url, article.context_tag, article.organization, article.author_array,
                             article.author_is_abbreviation_array,
                             article.genre, article.article_namespace_array, article.published_at, article.modified_at,
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
        if text is not None and organization == 'lvz':
            authorArray, author_is_abbreviation_array = getAuthorString(text)
            if authorArray is None:
                print(getData(jsonContent, 'articleBody')[-80:])
                print(authorArray)
                print(author_is_abbreviation_array)
                time.sleep(1)
        else:
            authorArray, author_is_abbreviation_array = None, None
        return None

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

        #save_to_database(articles_for_db, logger)


    print('success: ' + str(success))
    print('failed: ' + str(failed))
    print('notLVZ: ' + str(notLVZ))


if __name__ == '__main__':
    main()
