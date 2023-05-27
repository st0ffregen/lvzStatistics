from unittest import TestCase, mock
from ..scripts import connect_author_to_abbreviation

class TestConnectAuthorToAbbreviation(TestCase):

    def test_oldest_article(self):
        cur = mock.Mock()
        mock_result = mock.Mock()
        cur.execute.return_value = "asd"