from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from ..scripts import connect_author_to_abbreviation

class TestConnectAuthorToAbbreviation(TestCase):

    window_articles = [
        {'id': 0, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Mark Daniel\']',
                        'author_is_abbreviation': '[False]', 'published_at': '2010-01-01T00:00:00+00:00'},
        {'id': 1, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Mark Daniel\', \'Hannah Suppa\']',
                        'author_is_abbreviation': '[False, False]', 'published_at': '2010-02-01T00:00:00+00:00'},
        {'id': 2, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Theresa Moosmann\', \'md\']',
                        'author_is_abbreviation': '[False, True]', 'published_at': '2010-03-01T00:00:00+00:00'},
        {'id': 3, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'tm\', \'has\']',
                        'author_is_abbreviation': '[True, True]', 'published_at': '2010-04-01T00:00:00+00:00'},
        {'id': 4, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'mad\', \'lvz\']',
                        'author_is_abbreviation': '[True, True]', 'published_at': '2010-04-05T00:00:00+00:00'},
        {'id': 5, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'md\', \'tm\']',
                        'author_is_abbreviation': '[True, True]', 'published_at': '2010-04-10T00:00:00+00:00'},
        {'id': 6, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Tilmann Prüfer\']',
                        'author_is_abbreviation': '[False]', 'published_at': '2010-04-20T00:00:00+00:00'},
        {'id': 7, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Tim Meyer\']',
                        'author_is_abbreviation': '[False]', 'published_at': '2010-04-30T00:00:00+00:00'},
        {'id': 8, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Theresa Moosmann\']',
                        'author_is_abbreviation': '[False]', 'published_at': '2010-05-01T00:00:00+00:00'},
        {'id': 9, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'lvz\']',
                        'author_is_abbreviation': '[True]', 'published_at': '2010-05-10T00:00:00+00:00'},
        {'id': 10, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'Jan Armin-Döbeln\']',
                        'author_is_abbreviation': '[False]', 'published_at': '2010-05-10T00:00:00+00:00'},
        {'id': 11, 'url': 'test', 'organization': 'lvz', 'author_array': '[\'jad\']',
                        'author_is_abbreviation': '[True]', 'published_at': '2010-05-10T00:00:00+00:00'},
    ]

    authors_with_frequency = {
        'mark daniel': 2, 'hannah suppa': 1, 'theresa moosmann': 2, 'tilmann prüfer': 1, 'tim meyer': 1,
        'jan armin-döbeln': 1
    }

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

        for article in self.window_articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization) VALUES (?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], article['author_array'], article['author_is_abbreviation'],
                 article['published_at'], article['organization']))

        self.con.commit()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_match_author_to_abbreviation(self):
        connect_author_to_abbreviation.get_db_connection = Mock(return_value=(self.con, self.cur))
        connect_author_to_abbreviation.batch_size = 1

        connect_author_to_abbreviation.match_author_to_abbreviation()

        article_authors = self.cur.execute('SELECT ar.id, au.abbreviation FROM articles ar join article_authors aa on ar.id=aa.article_id join authors au on aa.author_id=au.id ').fetchall()
        author_abbreviations = self.cur.execute('select name, abbreviation from authors').fetchall()
        article_ids = [row[0] for row in article_authors]

        # articles without entries because they have abbreviations
        self.assertFalse(self.window_articles[0]['id'] in article_ids)
        self.assertFalse(self.window_articles[1]['id'] in article_ids)
        self.assertFalse(self.window_articles[6]['id'] in article_ids)
        self.assertFalse(self.window_articles[7]['id'] in article_ids)
        self.assertFalse(self.window_articles[8]['id'] in article_ids)
        self.assertFalse(self.window_articles[10]['id'] in article_ids)

        # check if the correct author was matched
        self.assertTrue((2, eval(self.window_articles[2]['author_array'])[1]) in article_authors)
        self.assertTrue((3, eval(self.window_articles[3]['author_array'])[0]) in article_authors)
        self.assertTrue((3, eval(self.window_articles[3]['author_array'])[1]) in article_authors)
        self.assertTrue((4, eval(self.window_articles[4]['author_array'])[0]) in article_authors)
        self.assertTrue((4, eval(self.window_articles[4]['author_array'])[1]) in article_authors)
        self.assertTrue((5, eval(self.window_articles[5]['author_array'])[0]) in article_authors)
        self.assertTrue((5, eval(self.window_articles[5]['author_array'])[1]) in article_authors)
        self.assertTrue((9, eval(self.window_articles[9]['author_array'])[0]) in article_authors)

        # check if authors got the right mapping to their abbreviation
        self.assertTrue(('mark daniel', 'md') in author_abbreviations)
        self.assertTrue(('mark daniel', 'mad') in author_abbreviations)
        self.assertTrue(('hannah suppa', 'has') in author_abbreviations)
        self.assertTrue(('theresa moosmann', 'tm') in author_abbreviations)
        self.assertTrue(('jan armin-döbeln', 'jad') in author_abbreviations)
        self.assertTrue(('lvz', 'lvz') in author_abbreviations)

    def test_search_for_full_name_article_0(self):
        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[0], self.authors_with_frequency)

        self.assertEqual(None, result)

    def test_search_for_full_name_article_1(self):
        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[1], self.authors_with_frequency)

        self.assertEqual(None, result)

    def test_search_for_full_name_article_2(self):
        matches_for_focused_article = [
            {'abbreviation': 'md', 'author': 'mark daniel', 'certainty': 0.8}  # direct match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[2], self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_3(self):
        matches_for_focused_article = [
            {'abbreviation': 'tm', 'author': 'theresa moosmann', 'certainty': 0.9},  # direct match
            {'abbreviation': 'has', 'author': 'hannah suppa', 'certainty': 0.6}  # direct match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[3], self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_4(self):
        matches_for_focused_article = [
            {'abbreviation': 'lvz', 'author': 'lvz', 'certainty': 1},  # direct organization match
            {'abbreviation': 'mad', 'author': 'mark daniel', 'certainty': 0.9}  # fuzzy match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[4],
                                                                     self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_5(self):
        matches_for_focused_article = [
            {'abbreviation': 'md', 'author': 'mark daniel', 'certainty': 0.8},  # direct match
            {'abbreviation': 'tm', 'author': 'theresa moosmann', 'certainty': 0.9}  # direct match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[5],
                                                                     self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_9(self):
        matches_for_focused_article = [
            {'abbreviation': 'lvz', 'author': 'lvz', 'certainty': 1},  # direct organization match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[9],
                                                                     self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_11(self):
        matches_for_focused_article = [
            {'abbreviation': 'jad', 'author': 'jan armin-döbeln', 'certainty': 0.8},  # direct match
        ]

        result = connect_author_to_abbreviation.search_for_full_name(self.window_articles[11],
                                                                     self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_add_article_id(self):
        focused_article = self.window_articles[0]
        matches = [{'abbreviation': 'test', 'author': 'author_0', 'certainty': 0}]

        connect_author_to_abbreviation.add_article_id(focused_article, matches)

        self.assertEqual(0, matches[0]['article_id'])

    def test_get_authors_with_frequency(self):
        authors_with_frequency = connect_author_to_abbreviation.get_authors_with_frequency(self.window_articles)

        self.assertEqual(self.authors_with_frequency, authors_with_frequency)

    def test_at_least_one_author_is_abbreviated(self):
        self.assertTrue(connect_author_to_abbreviation.at_least_one_author_is_abbreviated(self.window_articles[2]))
        self.assertFalse(connect_author_to_abbreviation.at_least_one_author_is_abbreviated(self.window_articles[0]))

    def test_at_least_one_author_is_an_organization(self):
        self.assertTrue(connect_author_to_abbreviation.at_least_one_author_is_abbreviated(self.window_articles[4]))
        self.assertFalse(connect_author_to_abbreviation.at_least_one_author_is_abbreviated(self.window_articles[0]))

    def test_get_abbreviations(self):
        author_abbreviations = ['tm', 'has']

        result = connect_author_to_abbreviation.get_abbreviations(self.window_articles[3])

        self.assertEqual(author_abbreviations, result)

    def test_add_organization_matches(self):
        expected_direct_matches = [{'abbreviation': 'lvz', 'author': 'lvz', 'certainty': 1}]
        expected_result_remaining_author_is_abbreviation = [True]
        expected_result_remaining_authors = ['mad']

        direct_matches = []
        result_remaining_author_is_abbreviation, result_remaining_authors = connect_author_to_abbreviation.add_organization_matches(direct_matches, self.window_articles[4])

        self.assertEqual(expected_result_remaining_author_is_abbreviation, result_remaining_author_is_abbreviation)
        self.assertEqual(expected_result_remaining_authors, result_remaining_authors)
        self.assertEqual(expected_direct_matches, direct_matches)

    def test_ordered_abbreviation_chars_match_name(self):
        author = 'theresa moosmann'
        abbreviation = 'tm'

        self.assertTrue(connect_author_to_abbreviation.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'theresa moosmann'
        abbreviation = 'has'

        self.assertTrue(connect_author_to_abbreviation.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'nils inker'
        abbreviation = 'in'

        self.assertTrue(connect_author_to_abbreviation.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'horst albrecht'
        abbreviation = 'has'

        self.assertFalse(connect_author_to_abbreviation.ordered_abbreviation_chars_match_name(author, abbreviation))