from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from datetime import datetime
import json
from src.sanitize.tests import test_data
from src.sanitize.scripts import remove_authors_with_few_articles


class TestWriteAuthorsToDataBase(TestCase):

    articles = test_data.articles

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL)')
        self.con.commit()

        for article in self.articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization'], datetime.utcnow().isoformat()))

        self.con.commit()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_remove_authors(self):
        remove_authors_with_few_articles.get_db_connection = Mock(return_value=(self.con, self.cur))
        remove_authors_with_few_articles.THRESHOLD = 2

        remove_authors_with_few_articles.remove_authors()

        authors = self.cur.execute('SELECT ar.id, ar.author_array FROM articles ar').fetchall()

        # check if the correct author was matched
        self.assertEqual((0, '["Mark Daniel"]'), (authors[0]))
        self.assertEqual((1, '["Mark Daniel"]'), (authors[1]))
        self.assertEqual((2, '["Theresa Moosmann", "md"]'), (authors[2]))
        self.assertEqual((3, '["tm"]'), (authors[3]))
        self.assertEqual((4, '["lvz"]'), (authors[4]))
        self.assertEqual((5, '["md", "tm"]'), (authors[5]))
        self.assertEqual((6, '["lvz"]'), (authors[6]))
        self.assertEqual((7, '["lvz"]'), (authors[7]))
        self.assertEqual((8, '["Theresa Moosmann"]'), (authors[8]))
        self.assertEqual((9, '["lvz"]'), (authors[9]))
        self.assertEqual((10, '["lvz"]'), (authors[10]))
        self.assertEqual((11, '["lvz"]'), (authors[11]))
        self.assertEqual((12, '["lvz"]'), (authors[12]))


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t