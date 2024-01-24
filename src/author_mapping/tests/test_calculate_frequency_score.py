from unittest import TestCase
from unittest.mock import Mock

from src.author_mapping.scripts import calculate_frequency_score
from src.author_mapping.tests.utils import mock_database
from src.author_mapping.tests.utils import test_data_for_department_score
from src.models.MatchingType import MatchingType

class TestCalculateFrequencyScore(TestCase):

    articles = test_data_for_department_score.articles

    def setUp(self):
        self.con, self.cur = mock_database.fill_database(self.articles)

        # fill in some mappings
        self.cur.execute('update unmapped_authors set abbreviation = "md", matching_type = "DIRECT_MATCH" where name = "Mark Daniel" limit 1')
        self.cur.execute('update unmapped_authors set abbreviation = "tm", matching_type = "DIRECT_MATCH" where name = "Theresa Moosmann" limit 1')
        self.cur.execute('update unmapped_authors set abbreviation = "tm", matching_type = "DIRECT_MATCH" where name = "Hannah Suppa" limit 1')
        self.con.commit()

        calculate_frequency_score.get_db_connection = Mock(return_value=(self.con, self.cur))
        calculate_frequency_score.DEPARTMENT_THRESHOLD = 0
        calculate_frequency_score.SMALL_DEPARTMENT_NUMBER_PENALTY_Y_INTERSECT = 0
        calculate_frequency_score.SMALL_DEPARTMENT_NUMBER_PENALTY_SLOPE = 0


    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_get_abbreviations_with_full_names(self):
        authors = calculate_frequency_score.get_abbreviations_with_full_names(self.cur)

        self.assertTrue(['Mark Daniel', 'md'] in authors[['full_name', 'abbreviation']].values.tolist())


    def test_calculate_frequency_score(self):
        authors = calculate_frequency_score.calculate_frequency_score()

        self.assertTrue(['Theresa Moosmann', 'tm', 1/2, 1] in authors[['full_name', 'abbreviation', 'full_name_pointing_to_abbreviation_share', 'abbreviation_pointing_to_full_name_share']].values.tolist())
        self.assertTrue(['Hannah Suppa', 'tm', 1/2, 1] in authors[['full_name', 'abbreviation', 'full_name_pointing_to_abbreviation_share', 'abbreviation_pointing_to_full_name_share']].values.tolist())
