from unittest import TestCase
from unittest.mock import Mock

from src.utils.author_mapping import determine_department_entity_shares
from src.author_mapping.tests.utils import mock_database
from src.author_mapping.tests.utils import test_data_for_map_abbreviations_to_names


class TestDetermineDepartmentEntityShares(TestCase):

    articles = test_data_for_map_abbreviations_to_names.articles

    def setUp(self):
        self.con, self.cur = mock_database.fill_database(self.articles)

        determine_department_entity_shares.get_db_connection = Mock(return_value=(self.con, self.cur))

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_get_data(self):
        departments = determine_department_entity_shares.get_data(self.cur)

        self.assertTrue(['Mark Daniel', '["Borna"]'] in departments[['name', 'department']].values.tolist())
        self.assertTrue(['jad', '["Sport"]'] in departments[['abbreviation', 'department']].values.tolist())
        self.assertFalse(['lvz', '["Sport"]'] in departments[['abbreviation', 'department']].values.tolist())

    def test_determine_departments_abbreviation_and_full_name_shares(self):
        departments_scaler_score = determine_department_entity_shares.determine_departments_abbreviation_and_full_name_shares(self.cur)

        self.assertTrue(['Borna', 0.5, 0.5] in departments_scaler_score[['department', 'abbreviation_share', 'full_name_share']].values.tolist())
        self.assertTrue(['Sport', 0.75, 0.25] in departments_scaler_score[['department', 'abbreviation_share', 'full_name_share']].values.tolist())