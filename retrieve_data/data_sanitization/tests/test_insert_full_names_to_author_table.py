from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from collections import defaultdict
import json
from ..tests import test_data
from ..scripts import insert_full_names_to_author_table

class TestInsertFullNamesToAuthorTable(TestCase):

    articles = test_data.articles

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL)')
        self.cur.execute(
            'CREATE TABLE "authors" ( "id" INTEGER NOT NULL UNIQUE, "name" TEXT, "abbreviation" TEXT, "matching_certainty" NUMERIC, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, PRIMARY KEY("id" AUTOINCREMENT))')
        self.cur.execute(
            'CREATE TABLE "article_authors" ( "id" INTEGER NOT NULL UNIQUE, "article_id" INTEGER NOT NULL, "author_id" INTEGER NOT NULL, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, UNIQUE("article_id","author_id"), PRIMARY KEY("id" AUTOINCREMENT))')
        self.con.commit()

        for article in self.articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization) VALUES (?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']),
                 json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization']))

        self.con.commit()

    def tearDown(self):
        self.cur.close()
        self.con.close()


    def test_retrieve_articles(self):
        articles = insert_full_names_to_author_table.retrieve_articles(self.cur)

        self.assertEqual(7, len(articles))

    def test_get_full_names(self):
        articles = [
            {'id': 1, 'author_array': ['Mark Daniel'], 'author_is_abbreviation': [ False]},
            {'id': 2, 'author_array': ['Theresa Moosmann', 'md'], 'author_is_abbreviation': [ False, True]},
        ]
        authors = insert_full_names_to_author_table.get_full_names(articles)

        self.assertEqual(2, len(authors))
        self.assertTrue('Mark Daniel' in authors.keys())
        self.assertEqual([2], authors['Theresa Moosmann'])

    def test_save_authors_to_db(self):
        authors = defaultdict(list)
        authors['Mark Daniel'] = [1, 2]
        authors['Theresa Moosmann'] = [2]
        self.cur.execute('insert into authors values (1, "Mark Daniel", "md", 1, "2018-01-01", "2018-01-01")')

        insert_full_names_to_author_table.save_authors_to_db(authors, self.con, self.cur)

        self.cur.execute('SELECT name, abbreviation FROM authors')
        authors = self.cur.fetchall()
        self.assertEqual(2, len(authors))
        self.assertEqual('Mark Daniel', authors[0][0])
        self.assertEqual('md', authors[0][1])
        self.assertEqual('Theresa Moosmann', authors[1][0])
        self.assertEqual(None, json.loads(authors[1][1]))

        self.cur.execute('SELECT article_id, author_id FROM article_authors')
        article_authors = self.cur.fetchall()
        self.assertEqual(3, len(article_authors))
        self.assertEqual(1, article_authors[0][0])
        self.assertEqual(1, article_authors[0][1])
        self.assertEqual(2, article_authors[1][0])
        self.assertEqual(1, article_authors[1][1])
        self.assertEqual(2, article_authors[2][0])
        self.assertEqual(2, article_authors[2][1])