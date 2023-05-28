import unittest
from ..scripts import retrieveDataFromArticle

class TestRetrieveDateFromArticle(unittest.TestCase):
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

    def test_get_author_string_single_full_name_with_von_and_text_including_a_link(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('/a/link Von Mark Daniel')
        )

    def test_get_author_string_single_full_name_with_von_and_author_has_hyphen(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Manuela Engelmann-Bunk'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Von Manuela Engelmann-Bunk')
        )

    def test_get_author_string_single_full_name_with_von_and_author_has_dot(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Manuela E. Bunk'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Von Manuela E. Bunk')
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

    def test_get_author_string_single_full_name_without_von_with_quotation(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Thomas Müller'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('müssen wir dann mit unseren Kreisräten abstimmen.“ Thomas Müller')
        )

    def test_get_author_string_single_full_name_without_von_with_period_and_weird_unicode(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString(u'some text. \xa0 Mark Daniel')
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
    def test_get_author_string_single_full_name_without_von_missing_period_leading_hyper_link(self):
        # Case 1.3
        # Single full name without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Michael Dick'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('an eine große Zeit des Leipziger Fußballs. www.initiative1903.de.tl Michael Dick')
        )

    def test_get_author_string_single_full_name_with_von_and_text_keyword(self):
        # Case 1.4
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Denise Peikert'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('some text. Von Denise Peikert (Text) und André Kempner (Fotos)')
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

    def test_get_author_string_single_abbreviation_with_von_and_period(self):
        # Case 3.1
        # Single abbreviation with "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['FD'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von F.D.')
        )

    def test_get_author_string_single_abbreviation_with_von_with_white_space(self):
        # Case 3.1
        # Single abbreviation with "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['FD'],
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

    def test_get_author_string_single_abbreviation_with_von(self):
        # Case 3.3
        # Single abbreviation written together with "Von" prefix
        self.assertEqual(
            (
                ['ast'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von ast')
        )

    def test_fail_get_author_string_single_abbreviation_with_von_because_abbreviation_too_long(self):
        # Case 3.3/3.2
        # Single abbreviation without "Von" prefix
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von toooooLong')
        )

    def test_get_author_string_mix_of_abbreviations_and_full_names_with_von_slash(self):
        # Case 4.1/7
        # Mix of abbreviations and full names, separated by a slash and "Von " prefix
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von LVZ/lg')
        )
        self.assertEqual(
            (
                ['DAZ', 'TS'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von DAZ/T.S.')
        )
        self.assertEqual(
            (
                ['DAZ', 'TS', 'abc', 'ABCD'],
                [True, True, True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von DAZ/T.S./abc/ABCD')
        )
        self.assertEqual(
            (
                ['Mark Daniel', 'ABCD'],
                [False, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von Mark Daniel/ABCD')
        )
        self.assertEqual(
            (
                ['ABCD', 'Mark Daniel'],
                [True, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von ABCD/Mark Daniel')
        )
        self.assertEqual(
            (
                ['ABCD', 'Mark Tim Daniel'],
                [True, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von ABCD/Mark Tim Daniel')
        )
        self.assertEqual(
            (
                ['ht', 'art'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von ht/-art')
        )

    def test_get_author_string_mix_of_abbreviations_and_full_names_with_von_comma(self):
        # Case 4.2
        # Mix of abbreviations and full names, separated by a comma and "Von " prefix
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von LVZ, lg')
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

    def test_fail_on_get_author_string_single_full_name_with_period_randomly_placed(self):
        # Case 1.1
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von Mark. Daniel')
        )

    def test_get_author_string_editorial_abbreviation(self):
        # Case 5
        # Editorial abbreviation
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Redaktion.')
        )
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. red.')
        )
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. red')
        )

    def test_get_author_string_no_author(self):
        # Case 6
        # No author
        self.assertEqual(
            (
                ["LVZ"],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text.')
        )

    def test_get_author_string_no_author_text_ends_with_quotation_mark(self):
        # Case 6
        # No author
        self.assertEqual(
            (
                ["LVZ"],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text."')
        )

    def test_get_author_with_co_author_abbreviation(self):
        # Case 8
        # with co-author
        self.assertEqual(
            (
                ['dpa', 'mro'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von mro (mit dpa)')
        )

    def test_get_author_string_with_co_author_full_name(self):
        # Case 8
        # with co-author
        self.assertEqual(
            (
                ['Theresa Moosmann', 'Mark Daniel'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von Mark Daniel (mit Theresa Moosmann)')
        )

    def test_get_author_string_full_names_without_von_separating_slash(self):
        # general case
        self.assertEqual(
            (
                ['Robert Berlin', 'Anne-Kathrin Sturm'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Hörmann 3, Bönke 1. Robert Berlin/Anne-Kathrin Sturm')
        )

    def test_get_author_string_abbreviations_without_von_separating_slash(self):
        # Case 4.3
        self.assertEqual(
            (
                ['RND', 'seb'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Nachhaken des jungen Reporters. RND/seb')
        )
    def test_get_author_string_organization_abbreviation(self):
        self.assertEqual(
            (
                ['mazonline'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Some text. Von MAZonline')
        )

    def test_get_author_string_return_null(self):
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString('2021 bis 20. März 2022 im Museum für Druckkunst Leipzig*')
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString('in die Stadt. Von ChristianKunze') # falsely written together
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieveDataFromArticle.getAuthorString(' Präparat aus dem Westen haben wollten. Von MAZ-Online/gel') # abbreviation too long / contains hyphen
        )
