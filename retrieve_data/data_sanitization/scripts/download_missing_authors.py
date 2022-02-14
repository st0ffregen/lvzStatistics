# downloads article for articles where no author is recognised by investigating context tag
# uses italic text on website for author recognition

import requests
import sqlite3
import concurrent.futures
import time
import sys
from bs4 import BeautifulSoup
import logging
import traceback
from datetime import datetime
from retrieveDataFromArticle import getAuthorString


class NoContextTagError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'NoContextTagError, {0} '.format(self.message)
        else:
            return 'NoContextTagError has been raised'


class WrongHttpResponseError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'WrongHttpResponseError, {0} '.format(self.message)
        else:
            return 'WrongHttpResponseError has been raised'


def configureLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    file_handler = logging.FileHandler('../logs/download_missing_authors.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def getUrls(offset, limit):
    con = sqlite3.connect('../data/articles_with_basic_information.db')
    cur = con.cursor()
    cur.execute('select url from articles where organization = \'lvz\' and is_free = \'True\' and author_array is NULL limit ' + str(limit) + ' offset ' + str(offset))
    entries = cur.fetchall()
    urls = []
    for row in entries:
        urls.append(row[0])

    return urls


def getDbCursor():
    con = sqlite3.connect('../data/articles_with_basic_information.db')
    return con, con.cursor()


def downloadAuthorName(url):
    response = requests.get('https://lvz.de' + url)

    if response.status_code == 429:
        time.sleep(30)
        response = requests.get('https://lvz.de' + url)
    elif response.status_code != 200:
        raise WrongHttpResponseError('Response http error for url ' + url + ' is ' + str(response.status_code))

    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        article_body = soup.find('div', {'class': 'pdb-article-body'})
        narrow_article_body = article_body.find('div', {'class': 'pdb-richtext-field'})
        article_body_paragraphs = narrow_article_body.find_all('p')
        author_paragraph = article_body_paragraphs[-1].find_all('em')[0].text

        if author_paragraph.startswith('Von '):
            author_paragraph = author_paragraph.replace('Von ', '')

        if author_paragraph.startswith('von '):
            author_paragraph = author_paragraph.replace('von ', '')

        return getAuthorString(author_paragraph, False)

    except IndexError as e:
        return None, None



def downloadArticle(url):
    author_array, author_is_abbreviation_array = downloadAuthorName(url)
    try:
        try:
            saveArticleToDb(con, cur, url, author_array, author_is_abbreviation_array)
        except sqlite3.IntegrityError as e:
            return f"sqlite3.IntegrityError: {url}: {e}"
    except NameError:
        con, cur = getDbCursor()
        try:
            saveArticleToDb(con, cur, url, author_array, author_is_abbreviation_array)
        except sqlite3.IntegrityError as e:
            return f"sqlite3.IntegrityError: {url}: {e}"
    except WrongHttpResponseError as e:
        return f"WrongHttpResponseError: {url}: {e}"
    except requests.exceptions.ConnectionError as e:
        return f"requests.exceptions.ConnectionError: {url}: {e}"
    except requests.exceptions.TooManyRedirects as e:
        return f"requests.exceptions.TooManyRedirects: {url}: {e}"
    except NoContextTagError as e:
        return f"NoContextTagError: {url}: {e}"

    return 'sucessfully downloaded ' + url


def saveArticleToDb(con, cur, url, author_array, author_is_abbreviation_array):

    if author_array is not None:
        author_array = str(author_array)

    if author_is_abbreviation_array is not None:
        author_is_abbreviation_array = str(author_is_abbreviation_array)

    cur.execute('update articles set author_array = ?, author_is_abbreviation = ?, updated_at = ? where url = ?',
                (author_array, author_is_abbreviation_array, datetime.utcnow().isoformat(), url))
    con.commit()


def main():
    logger = configureLogger()
    logger.info('start scaper')

    for i in range(0, 1):  # 100 per run, 363,491 articles in total so 0 to 3635
        offset = i * 100
        limit = 100
        logger.info('start run from ' + str(offset) + ' to ' + str(offset + limit))

        urls = getUrls(offset, limit)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = [executor.submit(downloadArticle, url) for url in urls]

            for f in concurrent.futures.as_completed(results):
                try:
                    result = f.result()
                    if 'Error' in result:
                        logger.warning(result)
                    else:
                        logger.info(result)
                except Exception as e:
                    logger.critical(f"something went wrong: {e}")
                    logger.critical(traceback.format_exception(*sys.exc_info()))
                    sys.exit(1)

        logger.info('sleep 4 seconds')
        time.sleep(4)

    logger.info('stop scraper')


if __name__ == '__main__':
    main()
