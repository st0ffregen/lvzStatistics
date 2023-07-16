from unittest import TestCase
from unittest.mock import Mock
import sqlite3
from collections import defaultdict
import json
from src.sanitize.tests import test_data
from src.sanitize.scripts import write_authors_to_database
from src.sanitize.scripts.write_authors_to_database import AuthorRow, MatchingType


class TestWriteAuthorsToDataBase(TestCase):

    articles = test_data.articles

    authors_with_frequency = defaultdict(int, {
        'Mark Daniel': 2, 'Hannah Suppa': 1, 'Theresa Moosmann': 2, 'Tilmann Prüfer': 1, 'Tim Meyer': 1,
        'Jan Armin-Döbeln': 1
    })

    def setUp(self):
        # Create a temporary in-memory SQLite database for testing
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        # simplified tables for testing
        self.cur.execute(
            'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "published_at" TEXT NOT NULL)')
        self.cur.execute(
            'CREATE TABLE "authors" ( "id" INTEGER NOT NULL UNIQUE, "name" TEXT, "abbreviation" TEXT, "matching_certainty" NUMERIC, "matching_type" TEXT, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, PRIMARY KEY("id" AUTOINCREMENT))')
        self.cur.execute(
            'CREATE TABLE "article_authors" ( "id" INTEGER NOT NULL UNIQUE, "article_id" INTEGER NOT NULL, "author_id" INTEGER NOT NULL, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, UNIQUE("article_id","author_id"), PRIMARY KEY("id" AUTOINCREMENT))')
        self.con.commit()

        for article in self.articles:
            self.cur.execute(
                'INSERT INTO articles (id, url, author_array, author_is_abbreviation, published_at, organization) VALUES (?, ?, ?, ?, ?, ?)',
                (article['id'], article['url'], json.dumps(article['author_array']), json.dumps(article['author_is_abbreviation']),
                 article['published_at'], article['organization']))

        self.con.commit()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_match_author_to_abbreviation(self):
        write_authors_to_database.get_db_connection = Mock(return_value=(self.con, self.cur))
        write_authors_to_database.batch_size = 1
        write_authors_to_database.database_batch_size = 1

        write_authors_to_database.write_author_to_database()

        article_authors_abbreviations = self.cur.execute('SELECT ar.id, au.abbreviation FROM articles ar join article_authors aa on ar.id=aa.article_id join authors au on aa.author_id=au.id ').fetchall()
        author_abbreviations = self.cur.execute('select name, abbreviation from authors').fetchall()
        article_ids = [row[0] for row in article_authors_abbreviations]

        # check if the correct author was matched
        self.assertTrue((2, self.articles[2]['author_array'][1]) in article_authors_abbreviations)
        self.assertTrue((3, self.articles[3]['author_array'][0]) in article_authors_abbreviations)
        self.assertTrue((3, self.articles[3]['author_array'][1]) in article_authors_abbreviations)
        self.assertTrue((4, self.articles[4]['author_array'][0]) in article_authors_abbreviations)
        self.assertTrue((4, self.articles[4]['author_array'][1]) in article_authors_abbreviations)
        self.assertTrue((5, self.articles[5]['author_array'][0]) in article_authors_abbreviations)
        self.assertTrue((5, self.articles[5]['author_array'][1]) in article_authors_abbreviations)
        self.assertTrue((9, self.articles[9]['author_array'][0]) in article_authors_abbreviations)
        self.assertTrue((12, self.articles[12]['author_array'][0]) in article_authors_abbreviations)

        # check if authors got the right mapping to their abbreviation
        self.assertTrue(('Mark Daniel', 'md') in author_abbreviations)
        self.assertTrue(('Mark Daniel', 'mad') in author_abbreviations)
        self.assertTrue(('Hannah Suppa', 'has') in author_abbreviations)
        self.assertTrue(('Theresa Moosmann', 'tm') in author_abbreviations)
        self.assertTrue(('Jan Armin-Döbeln', 'jad') in author_abbreviations)
        self.assertTrue(('lvz', 'lvz') in author_abbreviations)
        self.assertTrue((None, 'qxy') in author_abbreviations)

    def test_search_for_full_name_article_with_one_author(self):
        result = write_authors_to_database.search_for_full_name(self.articles[0], self.authors_with_frequency)

        self.assertEqual([AuthorRow("Mark Daniel", None, None, MatchingType.IS_FULL_NAME)], result)

    def test_search_for_full_name_article_with_two_authors(self):
        result = write_authors_to_database.search_for_full_name(self.articles[1], self.authors_with_frequency)

        self.assertEqual([
            AuthorRow("Mark Daniel", None, None, MatchingType.IS_FULL_NAME),
            AuthorRow("Hannah Suppa", None, None, MatchingType.IS_FULL_NAME)
        ], result)

    def test_search_for_full_name_article_with_abbreviation_and_full_name(self):
        matches_for_focused_article = [
            AuthorRow("Theresa Moosmann", None, None, MatchingType.IS_FULL_NAME),
            AuthorRow("Mark Daniel", "md", 0.8, MatchingType.DIRECT_MATCH)
        ]

        result = write_authors_to_database.search_for_full_name(self.articles[2], self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_3(self):
        matches_for_focused_article = [
            AuthorRow("Theresa Moosmann", "tm", 0.9, MatchingType.DIRECT_MATCH),
            AuthorRow("Hannah Suppa", "has", 0.6, MatchingType.FUZZY_MATCH)
        ]

        result = write_authors_to_database.search_for_full_name(self.articles[3], self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_4(self):
        matches_for_focused_article = [
            AuthorRow("lvz", "lvz", 1, MatchingType.ORGANIZATION_MATCH),
            AuthorRow("Mark Daniel", "mad", 0.9, MatchingType.FUZZY_MATCH)
        ]

        result = write_authors_to_database.search_for_full_name(self.articles[4],
                                                                self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_5(self):
        matches_for_focused_article = [
            AuthorRow("Mark Daniel", "md", 0.8, MatchingType.DIRECT_MATCH),
            AuthorRow("Theresa Moosmann", "tm", 0.9, MatchingType.DIRECT_MATCH)
        ]

        result = write_authors_to_database.search_for_full_name(self.articles[5],
                                                                self.authors_with_frequency)

        self.assertTrue(compare_dict_lists(matches_for_focused_article, result))

    def test_search_for_full_name_article_9(self):
        matches_for_focused_article = [
            AuthorRow("lvz", "lvz", 1, MatchingType.ORGANIZATION_MATCH),
        ]

        result = write_authors_to_database.search_for_full_name(self.articles[9],
                                                                self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_search_for_full_name_article_11(self):
        matches_for_focused_article = [AuthorRow("Jan Armin-Döbeln", "jad", 0.8, MatchingType.DIRECT_MATCH)]

        result = write_authors_to_database.search_for_full_name(self.articles[11],
                                                                self.authors_with_frequency)

        self.assertEqual(matches_for_focused_article, result)

    def test_add_article_id(self):
        focused_article = self.articles[0]
        matches = [AuthorRow("author_0", "test", 0, MatchingType.IS_FULL_NAME)]

        write_authors_to_database.add_article_id(focused_article, matches)

        self.assertEqual(0, matches[0].article_id)

    def test_get_authors_with_frequency(self):
        authors_with_frequency = write_authors_to_database.get_authors_with_frequency(self.articles)

        self.assertEqual(self.authors_with_frequency, authors_with_frequency)

    def test_at_least_one_author_is_full_name(self):
        self.assertTrue(write_authors_to_database.at_least_one_author_is_full_name(self.articles[2]))
        self.assertTrue(write_authors_to_database.at_least_one_author_is_full_name(self.articles[0]))
        self.assertFalse(write_authors_to_database.at_least_one_author_is_full_name(self.articles[4]))

    def test_at_least_one_author_is_an_organization(self):
        self.assertTrue(write_authors_to_database.at_least_one_author_is_an_organization(self.articles[4]))
        self.assertFalse(write_authors_to_database.at_least_one_author_is_an_organization(self.articles[0]))

    def test_get_abbreviations(self):
        author_abbreviations = {'tm', 'has'}

        result = write_authors_to_database.get_abbreviations(self.articles[3])

        self.assertEqual(author_abbreviations, result)

    def test_add_organization_matches(self):
        expected_direct_matches = [AuthorRow("lvz", "lvz", 1, MatchingType.ORGANIZATION_MATCH)]
        expected_result_remaining_author_is_abbreviation = [True]
        expected_result_remaining_authors = ['mad']

        direct_matches, result_remaining_author_is_abbreviation, result_remaining_authors = write_authors_to_database.add_organization_matches(self.articles[4])

        self.assertEqual(expected_result_remaining_author_is_abbreviation, result_remaining_author_is_abbreviation)
        self.assertEqual(expected_result_remaining_authors, result_remaining_authors)
        self.assertEqual(expected_direct_matches, direct_matches)

    def test_ordered_abbreviation_chars_match_name(self):
        author = 'theresa moosmann'
        abbreviation = 'tm'

        self.assertTrue(write_authors_to_database.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'theresa ,oosmann'
        abbreviation = 'has'

        self.assertTrue(write_authors_to_database.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'nils inker'
        abbreviation = 'in'

        self.assertTrue(write_authors_to_database.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'horst albrecht'
        abbreviation = 'has'

        self.assertFalse(write_authors_to_database.ordered_abbreviation_chars_match_name(author, abbreviation))


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t