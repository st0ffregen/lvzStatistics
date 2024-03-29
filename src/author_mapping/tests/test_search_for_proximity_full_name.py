from collections import Counter
from unittest import TestCase
from unittest.mock import Mock

from src.author_mapping.scripts import search_for_proximity_full_name
from src.author_mapping.tests.utils import mock_database
from src.models.AuthorDTO import AuthorDTO
from src.models.MatchingType import MatchingType
from src.author_mapping.tests.utils import test_data_for_proximity_full_name


class TestSearchForProximityFullName(TestCase):

    articles = test_data_for_proximity_full_name.articles

    authors_with_frequency = Counter({
        'Mark Daniel': 2, 'Hannah Suppa': 1, 'Theresa Moosmann': 2, 'Tilmann Prüfer': 1, 'Tim Meyer': 1,
        'Jan Armin-Döbeln': 1
    })

    def setUp(self):
        self.con, self.cur = mock_database.fill_database(self.articles)

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_match_author_to_abbreviation(self):
        search_for_proximity_full_name.get_db_connection = Mock(return_value=(self.con, self.cur))
        search_for_proximity_full_name.batch_size = 1
        search_for_proximity_full_name.database_batch_size = 1

        search_for_proximity_full_name.search_for_proximity_full_name()

        article_authors_abbreviations = self.cur.execute('SELECT ar.id, au.abbreviation FROM articles ar join unmapped_article_authors aa on ar.id=aa.article_id join unmapped_authors au on aa.author_id=au.id ').fetchall()
        author_abbreviations = self.cur.execute('select name, abbreviation from unmapped_authors').fetchall()
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

    def test_get_authors_with_frequency(self):
        names = ['Mark Daniel', 'Hannah Suppa', 'Theresa Moosmann', 'Mark Daniel', 'Theresa Moosmann',
                 'Tilmann Prüfer', 'Tim Meyer', 'Jan Armin-Döbeln']
        names = [{"_": "_", "__": "__", "name": name} for name in names]
        authors_with_frequency = search_for_proximity_full_name.get_frequency_for_names(names)

        self.assertEqual(self.authors_with_frequency, authors_with_frequency)

    def test_get_abbreviations(self):
        author_abbreviations = {'tm', 'has'}

        result = search_for_proximity_full_name.get_abbreviations(self.articles[3])

        self.assertEqual(author_abbreviations, result)

    def test_add_organization_matches(self):
        expected_direct_matches = [AuthorDTO("lvz", "lvz", 1, MatchingType.ORGANIZATION_MATCH)]
        expected_result_remaining_author_is_abbreviation = [True]
        expected_result_remaining_authors = ['mad']

        direct_matches, result_remaining_author_is_abbreviation, result_remaining_authors = search_for_proximity_full_name.add_organization_matches(self.articles[4])

        self.assertEqual(expected_result_remaining_author_is_abbreviation, result_remaining_author_is_abbreviation)
        self.assertEqual(expected_result_remaining_authors, result_remaining_authors)
        self.assertEqual(expected_direct_matches, direct_matches)

    def test_ordered_abbreviation_chars_match_name(self):
        author = 'theresa moosmann'
        abbreviation = 'tm'

        self.assertTrue(search_for_proximity_full_name.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'theresa ,oosmann'
        abbreviation = 'has'

        self.assertTrue(search_for_proximity_full_name.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'nils inker'
        abbreviation = 'in'

        self.assertTrue(search_for_proximity_full_name.ordered_abbreviation_chars_match_name(author, abbreviation))

        author = 'horst albrecht'
        abbreviation = 'has'

        self.assertFalse(search_for_proximity_full_name.ordered_abbreviation_chars_match_name(author, abbreviation))


def compare_dict_lists(s, t):
    t = list(t)   # make a mutable copy
    try:
        for elem in s:
            t.remove(elem)
    except ValueError:
        return False
    return not t