from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from datetime import datetime
import json
from src.sanitize.tests import test_data
from src.sanitize.scripts import update_authors_with_different_casing


class TestWriteAuthorsToDataBase(TestCase):

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL)')
        self.con.commit()

        update_authors_with_different_casing.get_db_connection = Mock(return_value=(self.con, self.cur))
        update_authors_with_different_casing.close_db_connection = Mock()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_update_authors(self):
        articles = [
            {'id': 0, 'url': 'test', 'organization': 'lvz', 'author_array': ["mark daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-01-01T00:00:00+00:00'},
            {'id': 1, 'url': 'test', 'organization': 'lvz', 'author_array': ["mark daniel"],
             'author_is_abbreviation': [False], 'published_at': '2010-02-01T00:00:00+00:00'},
            {'id': 2, 'url': 'test', 'organization': 'lvz', 'author_array': ["Theresa Moosmann", "Mark Daniel"],
             'author_is_abbreviation': [False, True], 'published_at': '2010-03-01T00:00:00+00:00'}
        ]

        for article in articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

        update_authors_with_different_casing.update_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array FROM articles ar').fetchall()

        # check author_array was correctly modified
        self.assertEqual((0, '["mark daniel"]'), (authors[0]))
        self.assertEqual((1, '["mark daniel"]'), (authors[1]))
        self.assertEqual((2, '["Theresa Moosmann", "mark daniel"]'), (authors[2]))


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t