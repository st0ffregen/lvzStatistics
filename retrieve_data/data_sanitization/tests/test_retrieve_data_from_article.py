import unittest
from ..scripts import retrieveDataFromArticle

class TestBot(unittest.TestCase):
    # cases are listed in the wiki: https://github.com/st0ffregen/lvzStatistics/wiki/Author-Recognition
    def test_get_author_string_single_full_name_with_von(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Von Mark Daniel')
        )

    def test_get_author_string_single_full_name_with_von_and_author_has_dash(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Manuela Engelmann-Bunk'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Von Manuela Engelmann-Bunk')
        )

    def test_get_author_string_single_full_name_without_von_with_period(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Mark Daniel')
        )

    def test_get_author_string_single_full_name_without_von_missing_period(self):
        # Case 1.3
        # Single full name without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text Mark Daniel')
        )

    def test_get_author_string_multiple_full_names_with_von(self):
        # Case 2.1
        # Multiple full names with "Von" prefix
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_without_von_with_period(self):
        # Case 2.2
        # Multiple full names without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some Text. Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_without_von_missing_period(self):
        # Case 2.3
        # Multiple full names without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_with_von_slash(self):
        # Case 2.4
        # Multiple full names with "Von" prefix, separated by a slash
        self.assertEqual(
            (
                ['Regina Katzer', 'Mathias Wöbking', 'Mark Daniel'],
                [False, False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von Regina Katzer / Mathias Wöbking / Mark Daniel')
        )

    def test_get_author_string_multiple_full_names_with_von_commas_und(self):
        # Case 2.5
        # Multiple full names with "Von" prefix, separated by commas and "und"
        self.assertEqual(
            (
                ['Kay Würker', 'Jens Rosenkranz', 'Thomas Haegeler', 'Ellen Paul', 'Dana Weber'],
                [False, False, False, False, False]
            ),
            retrieveDataFromArticle.getAuthorString(
                'Some text. Von Kay Würker, Jens Rosenkranz, Thomas Haegeler, Ellen Paul und Dana Weber')
        )

    def test_get_author_string_multiple_full_names_with_von_commas(self):
        # Case 2.6
        # Multiple full names with "Von" prefix, separated by commas
        self.assertEqual(
            (
                ['Kay Würker', 'Jens Rosenkranz', 'Thomas Haegeler', 'Ellen Paul', 'Dana Weber'],
                [False, False, False, False, False]
            ),
            retrieveDataFromArticle.getAuthorString(
                'Some text. Von Kay Würker, Jens Rosenkranz, Thomas Haegeler, Ellen Paul, Dana Weber')
        )

    def test_get_author_string_single_abbreviation_with_von(self):
        # Case 3.1
        # Single abbreviation with "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['F.D.'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von F.D.')
        )

    def test_get_author_string_single_abbreviation_with_von_with_white_space(self):
        # Case 3.1
        # Single abbreviation with "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['F.D.'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von F. D.')
        )

    def test_get_author_string_single_abbreviation_without_von(self):
        # Case 3.2
        # Single abbreviation without "Von" prefix
        self.assertEqual(
            (
                ['ast'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. ast')
        )

    def test_get_author_string_multiple_abbreviations_with_von_slash(self):
        # Case 4.1
        # Multiple abbreviations with "Von" prefix, separated by a slash
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von LVZ/lg')
        )
        self.assertEqual(
            (
                ['DAZ', 'T.S.'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von DAZ/T.S.')
        )
        self.assertEqual(
            (
                ['DAZ', 'T.S.', 'abc', 'ABCD'],
                [True, True, True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von DAZ/T.S./abc/ABCD')
        )

    def test_fail_on_get_author_string_multiple_abbreviations_with_von_slash_because_abbreviation_to_long(self):
        # Case 4.1
        # Multiple abbreviations with "Von" prefix, separated by a slash
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von DAZ/tooooooLong')
        )

    def test_get_author_string_editorial_abbreviation(self):
        # Case 5
        # Editorial abbreviation
        self.assertEqual(
            (
                ['lvz'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Redaktion.')
        )

        self.assertEqual(
            (
                ['lvz'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. red.')
        )

    def test_get_author_string_no_author(self):
        # Case 6
        # No author
        self.assertEqual(
            (
                ["lvz"],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text.')
        )