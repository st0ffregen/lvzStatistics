from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from datetime import datetime
import json
from src.sanitize.tests import test_data
from src.sanitize.scripts import write_unmapped_authors_to_data_base



class TestWriteAuthorsToDataBase(TestCase):

    articles = test_data.articles

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL)')
        self.cur.execute(
            'CREATE TABLE "unmapped_authors" ( "id" INTEGER NOT NULL UNIQUE, "name" TEXT, "abbreviation" TEXT, "matching_certainty" NUMERIC, "matching_type" TEXT, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, PRIMARY KEY("id" AUTOINCREMENT))')
        self.cur.execute(
            'CREATE TABLE "unmapped_article_authors" ( "id" INTEGER NOT NULL UNIQUE, "article_id" INTEGER NOT NULL, "author_id" INTEGER NOT NULL, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, UNIQUE("article_id","author_id"), PRIMARY KEY("id" AUTOINCREMENT))')
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

    def test_match_author_to_abbreviation(self):
        write_unmapped_authors_to_data_base.get_db_connection = Mock(return_value=(self.con, self.cur))
        write_unmapped_authors_to_data_base.chunk_size = 1

        write_unmapped_authors_to_data_base.write_authors_to_database()

        article_author_abbreviation = self.cur.execute('SELECT ar.id, au.name, au.abbreviation FROM articles ar join unmapped_article_authors aa on ar.id=aa.article_id join unmapped_authors au on aa.author_id=au.id ').fetchall()

        # check if the correct author was matched
        self.assertTrue((0, "Mark Daniel", None) in article_author_abbreviation)
        self.assertTrue((1, "Mark Daniel", None) in article_author_abbreviation)
        self.assertTrue((1, "Hannah Suppa", None) in article_author_abbreviation)
        self.assertTrue((2, "Theresa Moosmann", None) in article_author_abbreviation)
        self.assertTrue((2, None, "md") in article_author_abbreviation)
        self.assertTrue((3, None, "tm") in article_author_abbreviation)
        self.assertTrue((3, None, "has") in article_author_abbreviation)


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t