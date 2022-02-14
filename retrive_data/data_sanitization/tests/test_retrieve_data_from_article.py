import unittest
from ..scripts import retrieveDataFromArticle

class TestBot(unittest.TestCase):
    def test_get_author_string_with_und_seperator(self):
        self.assertEqual(
            (
                ['Theresa Moosmann', 'Mathias Wöbking'],
                [False, False]
            ),
            retrieveDataFromArticle.getAuthorString('Die Zeiten, in der das Gerät ihr Ein und Alles war, sind '
                                                    'hoffentlich vorbei. Von Theresa Moosmann und Mathias Wöbking',
                                                    True
                                                    )
        )

    def test_get_author_string_with_slash_seperator(self):
        self.assertEqual(
            (
                ['Regina Katzer', 'Mathias Wöbking', 'Mark Daniel'],
                [False, False, False]
            ),
            retrieveDataFromArticle.getAuthorString('„Wir werden den Hashtag und die Kampagne auch im nächsten Jahr'
                                                    ' gemeinsam nutzen.“ Von Regina Katzer / Mathias Wöbking / Mark Daniel',
                                                    True
                                                    )
        )

    def test_get_author_string_single_abbreviation(self):
        self.assertEqual(
            (
                ['an'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Ein möglicher Gegenkandidat ist bislang noch nicht bekannt. Von an',
                                                    True
                                                    )
        )


    def test_get_author_string_single_author_name(self):
        self.assertEqual(
            (
                ['Kristin Engel'],
                [False]
            ),
            retrieveDataFromArticle.getAuthorString('Reparaturarbeiten an der Kamera für das Storchen-TV vorzunehmen. Von Kristin Engel',
                                                    True
                                                    )
        )

    def test_get_author_string_abbreviation_with_slash_seperator(self):
        self.assertEqual(
            (
                ['LVZ', 'lg'],
                [True, True]
            ),
            retrieveDataFromArticle.getAuthorString('Zur Höhe des Sachschadens konnte zunächst keine Angabe gemacht werden. Von LVZ/lg',
                                                    True
                                                    )
        )

    def test_get_author_string_abbreviation_with_dots(self):
        self.assertEqual(
            (
                ['F. D.'],
                [True]
            ),
            retrieveDataFromArticle.getAuthorString('Auch zu weiteren Hintergründen der Tat machten die Behörden keinerlei Angaben. Von F. D.',
                                                    True
                                                    )
        )

    def test_fail_get_author_string_single_author_name_without_von(self):
        self.assertEqual(
            (
                None,
                None
            ),
            retrieveDataFromArticle.getAuthorString('Dresden und die Tänzer der Linedance Igel aus Taucha. Kathrin Kirscht',
                                                    True
                                                    )
        )

    def test_fail_get_author_string_author_abbreviation_name_without_von(self):
        self.assertEqual(
            (
                None,
                None
            ),
            retrieveDataFromArticle.getAuthorString('war und deshalb den Rettungswagen nicht bemerkte. ast',
                                                    True
                                                    )
        )


    def test_get_author_string_author_with_comma_and_und(self):
        self.assertEqual(
            (
                ['Kay Würker', 'Jens Rosenkranz', 'Thomas Haegeler', 'Ellen Paul', 'Dana Weber'],
                [False, False, False, False, False]
            ),
            retrieveDataFromArticle.getAuthorString('holte 2007 den Deutschen Märchenkongress nach Altenburg. Von Kay Würker, Jens Rosenkranz, Thomas Haegeler, Ellen Paul und Dana Weber',
                                                    True
                                                    )
        )
