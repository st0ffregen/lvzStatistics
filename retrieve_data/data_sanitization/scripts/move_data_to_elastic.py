import sqlite3
import json
from ast import literal_eval
import re
import sys
import time
import logging
import traceback
from elasticsearch import Elasticsearch
from elasticsearch import helpers


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

    file_handler = logging.FileHandler('../logs/move_data_to_elastic.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def loadArticles(limit, offset):
    con = sqlite3.connect('../data/articles_with_basic_information_production.db')
    cur = con.cursor()
    cur.execute('select * from articles limit ' + str(limit) + ' offset ' + str(offset))
    entries = cur.fetchall()
    articles = []
    for row in entries:
        try:
            author_array, author_is_abbreviation_array, article_namespace_array = row[4], row[5], row[7]

            if author_array is not None:
                author_array = literal_eval(author_array)
            if author_is_abbreviation_array is not None:
                author_is_abbreviation_array = literal_eval(author_is_abbreviation_array)
            if article_namespace_array is not None:
                article_namespace_array = literal_eval(article_namespace_array)

            article = Article(row[1], row[2], row[3], author_array, author_is_abbreviation_array, row[6], article_namespace_array, row[8], row[9], row[10], row[11], row[12])
        except (ValueError, TypeError) as e:
            print(row[4])
            print(row[5])
            print(row[7])
            raise e
        except SyntaxError: # TODO: entfernen, wnen retrieveData nochmal gelaufen wurde
            continue
        articles.append({
            '_index': 'lvz_articles',
            #'_type': 'article',
            '_id': row[0],
            'doc': article.__dict__
        })

    return articles



def move_data_to_elastic():
    es_client = Elasticsearch('http://localhost:9200')
    es_client.indices.delete(index='lvz_articles', ignore=404)
    es_client.indices.create(index='lvz_articles', ignore=400)

    for i in range(0, 30):
        offset = i * 1000
        limit = 1000

        articles = loadArticles(limit, offset)
        print(helpers.bulk(es_client, articles))
        print(str(i) + '/30')





def main():
    move_data_to_elastic()


if __name__ == '__main__':
    main()
