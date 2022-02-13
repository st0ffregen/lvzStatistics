import requests
import sqlite3
import concurrent.futures
import time
import sys
from bs4 import BeautifulSoup
import logging
import traceback
from datetime import datetime

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

    file_handler = logging.FileHandler('../logs/downloadArticles-6.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def getUrls(offset, limit):
    con = sqlite3.connect('../data/articles.db')
    cur = con.cursor()
    cur.execute('select articleUrl from articles where id > 510777 limit ' + str(limit) + ' offset ' + str(offset))
    entries = cur.fetchall()
    urls = []
    for row in entries:
        urls.append(row[0])

    return urls


def getDbCursor():
    con = sqlite3.connect('../data/downloadedArticles-6.db')
    return con, con.cursor()


def downloadContextTag(url):
    response = requests.get('https://lvz.de' + url)

    if response.status_code == 429:
        time.sleep(30)
        response = requests.get('https://lvz.de' + url)
    elif response.status_code != 200:
        raise WrongHttpResponseError('Response http error for url ' + url + ' is ' + str(response.status_code))

    soup = BeautifulSoup(response.text, 'html.parser')

    
    scripts = soup.find_all('script', {'type': 'application/ld+json'})

    try:
        contextScriptTag = scripts[1]
    except IndexError:
        raise NoContextTagError('No context tag found in url ' + url)

    if '{"@context":"http://schema.org","@type":"NewsArticle"' in str(contextScriptTag):
        contextTag = str(contextScriptTag).replace('<script type="application/ld+json">', '').replace('</script>', '').strip()
        return contextTag

    raise NoContextTagError('No context tag found in url')


def downloadArticle(url):
    try:
        contextTag = downloadContextTag(url)
        try:
            saveArticleToDb(con, cur, url, contextTag)
        except sqlite3.IntegrityError as e:
            return f"sqlite3.IntegrityError: {url}: {e}"
    except NameError:
        con, cur = getDbCursor()
        try:
            saveArticleToDb(con, cur, url, contextTag)
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


def saveArticleToDb(con, cur, url, contextTag):
    cur.execute('insert into articles values (?,?,?,?)', (None, url, contextTag, datetime.utcnow().isoformat()))
    con.commit()


def main():
    logger = configureLogger()
    logger.info('start scaper')

    for i in range(0, 77):  # 100 per run, 363,491 articles in total so 0 to 3635
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
