import unittest
from src.sanitize.scripts import retrieve_data_from_article

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
            retrieve_data_from_article.get_author('some text. Von Mark Daniel')
        )

    def test_get_author_string_single_full_name_with_von_and_text_including_a_link(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieve_data_from_article.get_author('/a/link Von Mark Daniel')
        )

    def test_get_author_string_single_full_name_with_von_and_author_has_hyphen(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Manuela Engelmann-Bunk'],
                [False]
            ),
            retrieve_data_from_article.get_author('some text. Von Manuela Engelmann-Bunk')
        )

    def test_get_author_string_single_full_name_with_von_and_author_has_dot(self):
        # Case 1.1
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Manuela E. Bunk'],
                [False]
            ),
            retrieve_data_from_article.get_author('some text. Von Manuela E. Bunk')
        )

    def test_get_author_string_single_full_name_without_von_with_period(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period or colon
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieve_data_from_article.get_author('some text. Mark Daniel')
        )

        # self.assertEqual(
        #     (
        #         ['Kathrin Kirscht'],
        #         [False]
        #     ),
        #     retrieve_data_from_article.get_author('konnte das hei\u00dfe Getr\u00e4nk ausgeschenkt werden. Kathrin Kirscht')
        # )

    def test_get_author_string_single_full_name_without_von_with_colon(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period or colon
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieve_data_from_article.get_author('some text: Mark Daniel')
        )
        self.assertEqual(
            (
                ['Janina Fleischer'],
                [False]
            ),
            retrieve_data_from_article.get_author('Roman.S. Fischer Verlag;272 Seiten,19,95 Euro: Janina Fleischer')
        )

    def test_get_author_string_single_full_name_without_von_with_quotation(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Thomas Müller'],
                [False]
            ),
            retrieve_data_from_article.get_author('müssen wir dann mit unseren Kreisräten abstimmen.“ Thomas Müller')
        )

    def test_get_author_string_single_full_name_without_von_with_period_and_weird_unicode(self):
        # Case 1.2
        # Single full name without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieve_data_from_article.get_author(u'some text. \xa0 Mark Daniel')
        )

    def test_get_author_string_single_full_name_without_von_missing_period(self):
        # Case 1.3
        # Single full name without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Mark Daniel'],
                [False]
            ),
            retrieve_data_from_article.get_author('Some text Mark Daniel')
        )
    def test_get_author_string_single_full_name_without_von_missing_period_leading_hyper_link(self):
        # Case 1.3
        # Single full name without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Michael Dick'],
                [False]
            ),
            retrieve_data_from_article.get_author('an eine große Zeit des Leipziger Fußballs. www.initiative1903.de.tl Michael Dick')
        )

    def test_get_author_string_single_full_name_with_von_and_text_keyword(self):
        # Case 1.4
        # Single full name with "Von" prefix
        self.assertEqual(
            (
                ['Denise Peikert'],
                [False]
            ),
            retrieve_data_from_article.get_author('some text. Von Denise Peikert (Text) und André Kempner (Fotos)')
        )

    def test_get_author_string_multiple_full_names_with_von(self):
        # Case 2.1
        # Multiple full names with "Von" prefix
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieve_data_from_article.get_author('Some text. Von Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_without_von_with_period(self):
        # Case 2.2
        # Multiple full names without "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieve_data_from_article.get_author('Some Text. Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_without_von_missing_period(self):
        # Case 2.3
        # Multiple full names without "Von" prefix, missing period
        self.assertEqual(
            (
                ['Mark Daniel', 'Theresa Moosmann'],
                [False, False]
            ),
            retrieve_data_from_article.get_author('Some text Mark Daniel und Theresa Moosmann')
        )

    def test_get_author_string_multiple_full_names_with_von_slash(self):
        # Case 2.4
        # Multiple full names with "Von" prefix, separated by a slash
        self.assertEqual(
            (
                ['Regina Katzer', 'Mathias Wöbking', 'Mark Daniel'],
                [False, False, False]
            ),
            retrieve_data_from_article.get_author('Some text. Von Regina Katzer / Mathias Wöbking / Mark Daniel')
        )

    def test_get_author_string_multiple_full_names_with_von_commas_und(self):
        # Case 2.5
        # Multiple full names with "Von" prefix, separated by commas and "und"
        self.assertEqual(
            (
                ['Kay Würker', 'Jens Rosenkranz', 'Thomas Haegeler', 'Ellen Paul', 'Dana Weber'],
                [False, False, False, False, False]
            ),
            retrieve_data_from_article.get_author(
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
            retrieve_data_from_article.get_author(
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
            retrieve_data_from_article.get_author('Some text. Von F.D.')
        )

    def test_get_author_string_single_abbreviation_with_von_with_white_space(self):
        # Case 3.1
        # Single abbreviation with "Von" prefix, separated by a period
        self.assertEqual(
            (
                ['FD'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. Von F. D.')
        )

    def test_get_author_string_single_abbreviation_without_von(self):
        # Case 3.2
        # Single abbreviation without "Von" prefix
        self.assertEqual(
            (
                ['ast'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. ast')
        )
        self.assertEqual(
            (
                ['abö'],
                [True]
            ),
            retrieve_data_from_article.get_author('hannig kündigte zugleich an, zu prüfen, ob der gestellte insolvenzantrag wirksam ist. abö')
        )

    def test_get_author_string_single_abbreviation_with_von(self):
        # Case 3.3
        # Single abbreviation written together with "Von" prefix
        self.assertEqual(
            (
                ['ast'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. Von ast')
        )

    def test_fail_get_author_string_single_abbreviation_with_von_because_abbreviation_too_long(self):
        # Case 3.3/3.2
        # Single abbreviation without "Von" prefix
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Some text. Von toooooLong')
        )

    def test_get_author_string_mix_of_abbreviations_and_full_names_with_von_and_slash(self):
        # Case 4.1/7
        # Mix of abbreviations and full names, separated by a slash and "Von " prefix
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von LVZ/lg')
        )
        self.assertEqual(
            (
                ['DAZ', 'TS'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von DAZ/T.S.')
        )
        self.assertEqual(
            (
                ['DAZ', 'TS', 'abc', 'ABCD'],
                [True, True, True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von DAZ/T.S./abc/ABCD')
        )
        self.assertEqual(
            (
                ['Mark Daniel', 'ABCD'],
                [False, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von Mark Daniel/ABCD')
        )
        self.assertEqual(
            (
                ['ABCD', 'Mark Daniel'],
                [True, False]
            ),
            retrieve_data_from_article.get_author('Some text. Von ABCD/Mark Daniel')
        )
        self.assertEqual(
            (
                ['ABCD', 'Mark Tim Daniel'],
                [True, False]
            ),
            retrieve_data_from_article.get_author('Some text. Von ABCD/Mark Tim Daniel')
        )
        self.assertEqual(
            (
                ['ht', 'art'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von ht/-art')
        )

    def test_get_author_string_mix_of_abbreviations_and_full_names_without_von_and_slash(self):
        # Case 4.3/7
        # Mix of abbreviations and full names, separated by a slash without "Von " prefix
        self.assertEqual(
            (
                ['lyn', 'Thomas Klein'],
                [True, False]
            ),
            retrieve_data_from_article.get_author('werden, LVZ-Online schaltet einen Live-Ticker. lyn/Thomas Klein')
        )
        self.assertEqual(
            (
                ['Thomas Klein', 'lyn'],
                [False, True]
            ),
            retrieve_data_from_article.get_author('werden, LVZ-Online schaltet einen Live-Ticker. Thomas Klein/lyn')
        )
        self.assertEqual(
            (
                ['joka', 'nöß'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Angaben. „Vieles ist derzeit noch unklar“, erklärte Braunsdorf. Der Polizist blieb unverletzt. joka/nöß')
        )
        self.assertEqual(
            (
                ['lyn', 'kno'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Jeder dritte Studienanfänger stammte 2013 aus dem Westen. lyn / kno')
        )

    def test_get_author_string_mix_of_abbreviations_and_full_names_with_von_comma(self):
        # Case 4.2
        # Mix of abbreviations and full names, separated by a comma and "Von " prefix
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von LVZ, lg')
        )

    def test_fail_on_get_author_string_multiple_abbreviations_with_von_slash_because_abbreviation_to_long(self):
        # Case 4.1
        # Multiple abbreviations with "Von" prefix, separated by a slash
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Some text. Von DAZ/tooooooLong')
        )

    def test_fail_on_get_author_string_single_full_name_with_period_randomly_placed(self):
        # Case 1.1
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Some text. Von Mark. Daniel')
        )

    def test_get_author_string_editorial_abbreviation(self):
        # Case 5
        # Editorial abbreviation
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. Redaktion.')
        )
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. red.')
        )
        self.assertEqual(
            (
                ['LVZ'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. red')
        )

    def test_get_author_string_no_author(self):
        # Case 6
        # No author
        self.assertEqual(
            (
                ["LVZ"],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text.')
        )

    def test_get_author_string_no_author_text_ends_with_quotation_mark(self):
        # Case 6
        # No author
        self.assertEqual(
            (
                ["LVZ"],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text."')
        )

    def test_get_author_with_co_author_abbreviation(self):
        # Case 8
        # with co-author
        self.assertEqual(
            (
                ['dpa', 'mro'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Some text. Von mro (mit dpa)')
        )

    def test_get_author_string_with_co_author_full_name(self):
        # Case 8
        # with co-author
        self.assertEqual(
            (
                ['Theresa Moosmann', 'Mark Daniel'],
                [False, False]
            ),
            retrieve_data_from_article.get_author('Some text. Von Mark Daniel (mit Theresa Moosmann)')
        )

    def test_get_author_string_full_names_without_von_separating_slash(self):
        # general case
        self.assertEqual(
            (
                ['Robert Berlin', 'Anne-Kathrin Sturm'],
                [False, False]
            ),
            retrieve_data_from_article.get_author('Hörmann 3, Bönke 1. Robert Berlin/Anne-Kathrin Sturm')
        )

    def test_get_author_string_abbreviations_without_von_separating_slash(self):
        # Case 4.3
        self.assertEqual(
            (
                ['RND', 'seb'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('Nachhaken des jungen Reporters. RND/seb')
        )
    def test_get_author_string_organization_abbreviation(self):
        self.assertEqual(
            (
                ['mazonline'],
                [True]
            ),
            retrieve_data_from_article.get_author('Some text. Von MAZonline')
        )

    def test_get_author_replace_interview_with_von_keyword(self):
        self.assertEqual(
            (
                ['Matthias Roth'],
                [False]
            ),
            retrieve_data_from_article.get_author('Bundesligaspiele. Wir sind doch Vollprofis. Interview: Matthias Roth')
        )

    def test_get_author_replace_date_with_von_keyword(self):
        self.assertEqual(
            (
                ['kr', 'TJ'],
                [True, True]
            ),
            retrieve_data_from_article.get_author('macht nicht nur sie sich weiterhin Sorgen. Aus der Leipziger Volkszeitung vom 23.09.2014 kr/T.J')
        )

    def test_get_author_double_author_naming(self):
        self.assertEqual(
            (
                ['Steffen Brost'],
                [False]
            ),
            retrieve_data_from_article.get_author(' und uns mit Michel auf die Schulzeit freuen\". Steffen Brost Steffen Brost')
        )

    def test_get_author_string_return_null(self):
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('2021 bis 20. März 2022 im Museum für Druckkunst Leipzig*')
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('in die Stadt. Von ChristianKunze') # falsely written together
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author(' Präparat aus dem Westen haben wollten. Von MAZ-Online/gel') # abbreviation too long / contains hyphen
        )

        # M.Orbeck recognition fails due to missing white space
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Heimatforschung erhalten. O. Büchel/M.Orbeck')
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Anteilnahme. Je mehr Geld zusammenkomme, desto besser. Zur Spendenaktion LVZ')
        )


    def test_get_author_string_handle_digits(self):
        self.assertEqual(
            (
                ['okz'],
                [True]
            ),
            retrieve_data_from_article.get_author('Polizeirevier Grimma, Tel. 03437/708925100, zu melden. Von okz')
        )
        self.assertEqual(
            (
                None, None
            ),
            retrieve_data_from_article.get_author('Kreissportbund Nordsachsen, Leipziger Straße 44, 04860 Torgau, Telefon: 03421/969 70 31, Mail: ruhs@ksb-nordsachsen.de')
        )

    def test_half_positive_edge_cases(self):
        # cases that get an author assigned but are not 100% correct
        self.assertEqual(
            (
                ['Reinhard Rädler'],
                [False]
            ),
            retrieve_data_from_article.get_author('dieser neuen Bilder statt. Reinhard Rädler / Olaf Barth Aus der Leipziger Volkszeitung vom 22.05.2013 Reinhard Rädler')
        )
        self.assertEqual(
            (
                ['abö'],
                [True]
            ),
            retrieve_data_from_article.get_author('hannig kündigte zugleich an, zu prüfen, ob der gestellte insolvenzantrag wirksam ist. abö')
        )
        self.assertEqual(
            (
                ['LVZ'], [True]
            ),
            retrieve_data_from_article.get_author('Verteilung der Flüchtlinge beinhaltet.“ Andreas Hummel/ Julia Vollmer (mit dpa) Die Kommentarfunktion steht morgen wieder zur Verfügung.')
        )
