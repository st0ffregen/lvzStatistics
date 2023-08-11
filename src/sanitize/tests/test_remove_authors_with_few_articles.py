from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from datetime import datetime
import json
from src.sanitize.tests import test_data
from src.sanitize.scripts import remove_authors_with_few_articles


class TestWriteAuthorsToDataBase(TestCase):

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL)')
        self.con.commit()

        remove_authors_with_few_articles.get_db_connection = Mock(return_value=(self.con, self.cur))
        remove_authors_with_few_articles.close_db_connection = Mock()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_remove_authors(self):
        articles = test_data.articles

        for article in articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

        remove_authors_with_few_articles.THRESHOLD = 2
        remove_authors_with_few_articles.remove_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array, ar.author_is_abbreviation FROM articles ar').fetchall()

        # check author_array was correctly modified
        self.assertEqual((0, '["Mark Daniel"]', '[false]'), (authors[0]))
        self.assertEqual((1, '["Mark Daniel"]', '[false]'), (authors[1]))
        self.assertEqual((2, '["Theresa Moosmann", "md"]', '[false, true]'), (authors[2]))
        self.assertEqual((3, '["tm"]', '[true]'), (authors[3]))
        self.assertEqual((4, '["lvz"]', '[true]'), (authors[4]))
        self.assertEqual((5, '["md", "tm"]', '[true, true]'), (authors[5]))
        self.assertEqual((6, '["lvz"]', '[true]'), (authors[6]))
        self.assertEqual((7, '["lvz"]', '[true]'), (authors[7]))
        self.assertEqual((8, '["Theresa Moosmann"]', '[false]'), (authors[8]))
        self.assertEqual((9, '["lvz"]', '[true]'), (authors[9]))
        self.assertEqual((10, '["lvz"]', '[true]'), (authors[10]))
        self.assertEqual((11, '["lvz"]', '[true]'), (authors[11]))
        self.assertEqual((12, '["lvz"]', '[true]'), (authors[12]))

    def test_remove_authors_under_threshold_authors_in_one_author_array(self):
        articles = [
            {'id': 0, 'url': 'test', 'organization': 'lvz', 'author_array': ["Mark Daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-01-01T00:00:00+00:00'},
            {'id': 1, 'url': 'test', 'organization': 'lvz', 'author_array': ["Mark Daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-02-01T00:00:00+00:00'},
            {'id': 2, 'url': 'test', 'organization': 'lvz', 'author_array': ["Theresa Moosmann", "Hannah Suppa"],
             'author_is_abbreviation': [False, True], 'published_at': '2010-03-01T00:00:00+00:00'}
        ]

        for article in articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

        remove_authors_with_few_articles.THRESHOLD = 2
        remove_authors_with_few_articles.remove_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array, ar.author_is_abbreviation FROM articles ar').fetchall()

        # check author_array was correctly modified
        self.assertEqual((0, '["Mark Daniel"]', '[false]'), (authors[0]))
        self.assertEqual((1, '["Mark Daniel"]', '[false]'), (authors[1]))
        self.assertEqual((2, '["lvz"]', '[true]'), (authors[2]))


    def test_remove_authors_different_casing_remove_all(self):
        articles = [
            {'id': 0, 'url': 'test', 'organization': 'lvz', 'author_array': ["Mark Daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-01-01T00:00:00+00:00'},
            {'id': 1, 'url': 'test', 'organization': 'lvz', 'author_array': ["mark daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-02-01T00:00:00+00:00'},
            {'id': 2, 'url': 'test', 'organization': 'lvz', 'author_array': ["Theresa Moosmann", "Hannah Suppa"],
             'author_is_abbreviation': [False, True], 'published_at': '2010-03-01T00:00:00+00:00'}
        ]

        for article in articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

        remove_authors_with_few_articles.THRESHOLD = 2
        remove_authors_with_few_articles.remove_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array, ar.author_is_abbreviation FROM articles ar').fetchall()

        # check author_array was correctly modified
        self.assertEqual((0, '["lvz"]', '[true]'), (authors[0]))
        self.assertEqual((1, '["lvz"]', '[true]'), (authors[1]))
        self.assertEqual((2, '["lvz"]', '[true]'), (authors[2]))

    def test_remove_authors_different_casing_keep_one(self):
        articles = [
            {'id': 0, 'url': 'test', 'organization': 'lvz', 'author_array': ["Mark Daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-01-01T00:00:00+00:00'},
            {'id': 1, 'url': 'test', 'organization': 'lvz', 'author_array': ["mark daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-02-01T00:00:00+00:00'},
            {'id': 2, 'url': 'test', 'organization': 'lvz', 'author_array': ["Mark Daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-03-01T00:00:00+00:00'}
        ]

        for article in articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

        remove_authors_with_few_articles.THRESHOLD = 2
        remove_authors_with_few_articles.remove_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array, ar.author_is_abbreviation FROM articles ar').fetchall()

        # check author_array was correctly modified
        self.assertEqual((0, '["Mark Daniel"]', '[false]'), (authors[0]))
        self.assertEqual((1, '["lvz"]', '[true]'), (authors[1]))
        self.assertEqual((2, '["Mark Daniel"]', '[false]'), (authors[2]))


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t