from unittest import TestCase
from unittest.mock import Mock
import pandas as pd
import numpy as np

from src.author_mapping.scripts import calculate_department_score
from src.author_mapping.tests.utils import mock_database
from src.author_mapping.tests.utils import test_data_for_department_score
from src.models.MatchingType import MatchingType

class TestCalculateDepartmentScore(TestCase):

    articles = test_data_for_department_score.articles

    def setUp(self):
        self.con, self.cur = mock_database.fill_database(self.articles)

        # fill in some mappings
        self.cur.execute('update unmapped_authors set abbreviation = "md", matching_type = "DIRECT_MATCH" where name = "Mark Daniel" limit 1')
        self.cur.execute('update unmapped_authors set abbreviation = "tm", matching_type = "DIRECT_MATCH" where name = "Theresa Moosmann" limit 1')
        self.con.commit()

        calculate_department_score.get_db_connection = Mock(return_value=(self.con, self.cur))
        calculate_department_score.DEPARTMENT_THRESHOLD = 0
        calculate_department_score.SMALL_DEPARTMENT_NUMBER_PENALTY_Y_INTERSECT = 0
        calculate_department_score.SMALL_DEPARTMENT_NUMBER_PENALTY_SLOPE = 0


    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_get_data_for_department_score(self):
        department_affiliation = calculate_department_score.get_data(self.cur)

        self.assertTrue(['Mark Daniel', '["Borna"]'] in department_affiliation[['name', 'department']].values.tolist())
        self.assertTrue(['jad', '["Sport"]'] in department_affiliation[['abbreviation', 'department']].values.tolist())
        self.assertFalse(['lvz', '["Sport"]'] in department_affiliation[['abbreviation', 'department']].values.tolist())


    def test_prepare_data_for_department_score(self):
        department_affiliation = pd.DataFrame(columns=['name', 'department', 'matching_type'],
                                              data=[["Mark Daniel", '["Borna", "Sport"]', MatchingType.DIRECT_MATCH.name], ["Theresa Moosmann", '["Sport"]', MatchingType.IS_FULL_NAME.name]])

        department_affiliation = calculate_department_score.prepare_data(department_affiliation)

        self.assertTrue(['Mark Daniel', 'Borna'] in department_affiliation[['name', 'department']].values.tolist())
        self.assertTrue(['Mark Daniel', 'Sport'] in department_affiliation[['name', 'department']].values.tolist())
        self.assertFalse(["Theresa Moosmann", 'Sport'] in department_affiliation[['name', 'department']].values.tolist())


    def test_scale_department_count(self):
        department_count = pd.DataFrame(columns=['department', 'count'], data=[["Sport", 1], ["Borna", 2]])
        department_scaler_score = pd.DataFrame(columns=['department', 'abbreviation_share', 'full_name_share'], data=[["Sport", 0.5, 0.5], ["Borna", 0.2, 0.8]])

        department_count_scaled = calculate_department_score.scale_department_count(department_count, department_scaler_score, "abbreviation_share")

        self.assertTrue(['Sport', 1] in department_count_scaled[['department', 'count']].values.tolist())
        self.assertTrue(['Borna', 5] in department_count_scaled[['department', 'count']].values.tolist())

    def test_calculate_department_score(self):
        results = calculate_department_score.calculate_department_score()

        self.assertTrue(['Theresa Moosmann', 'tm', 3, 1, 1/3] in results[['full_name', 'abbreviation', 'n_departments', 'n_not_overlapping_departments', 'penalization_score']].values.tolist())
        self.assertFalse(np.isnan(results[results["full_name"] == "Theresa Moosmann"]["department_score"].values[0]))
