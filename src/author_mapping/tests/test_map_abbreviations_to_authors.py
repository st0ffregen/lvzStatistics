from unittest import TestCase
import pandas as pd

from src.author_mapping.scripts import map_abbreviations_to_authors
from src.author_mapping.tests.utils import mock_database


class TestMapAbbreviationsToAuthors(TestCase):

    author_mapping = pd.DataFrame(columns=['full_name', 'abbreviation'], data=[
        ["Mark Daniel", "md"],
        ["Theresa Moosmann", "tm"],
        ["Hasan Alkas", "ha"],
    ])
    authors = pd.DataFrame(columns=['full_name', 'abbreviation'], data=[
        ["Mark Daniel", "md"],
        ["Theresa Moosmann", "tm"],
        ["Jan Armin-Döbeln", "jad"],
    ])

    def setUp(self):
        self.con, self.cur = mock_database.mock_database()

    def tearDown(self):
        self.cur.close()
        self.con.close()

    def test_insert_unmapped_abbreviations(self):
        map_abbreviations_to_authors.insert_unmapped_abbreviations(self.cur, self.author_mapping, self.authors)

        self.cur.execute('select id, abbreviation from abbreviations where abbreviation = "jad"')
        abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(abbreviations_rows))

        self.cur.execute('select id, author_id, abbreviation_id from author_abbreviations where abbreviation_id = ?', (abbreviations_rows[0][0],))
        author_abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_abbreviations_rows))

        self.cur.execute('select id from authors where id = ?', (author_abbreviations_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))


    def test_insert_unmapped_names(self):
        map_abbreviations_to_authors.insert_unmapped_names(self.cur, self.author_mapping, self.authors)

        self.cur.execute('select id, name from names where name = "Jan Armin-Döbeln"')
        names_rows = self.cur.fetchall()
        self.assertEqual(1, len(names_rows))

        self.cur.execute('select id, author_id, name_id from author_names where name_id = ?', (names_rows[0][0],))
        author_names_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_names_rows))

        self.cur.execute('select id from authors where id = ?', (author_names_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))

    def test_insert_mapped_authors(self):
        map_abbreviations_to_authors.insert_mapped_authors(self.cur, self.author_mapping)

        self.cur.execute('select id, name from names where name = "Mark Daniel"')
        names_rows = self.cur.fetchall()
        self.assertEqual(1, len(names_rows))

        self.cur.execute('select id, author_id, name_id from author_names where name_id = ?', (names_rows[0][0],))
        author_names_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_names_rows))

        self.cur.execute('select id from authors where id = ?', (author_names_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))

        self.cur.execute('select id, abbreviation from abbreviations where abbreviation = "tm"')
        abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(abbreviations_rows))

        self.cur.execute('select id, author_id, abbreviation_id from author_abbreviations where abbreviation_id = ?', (abbreviations_rows[0][0],))
        author_abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_abbreviations_rows))

        self.cur.execute('select id from authors where id = ?', (author_abbreviations_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))


    def test_insert_mapped_authors_with_both_name_and_abbreviation_already_in_db_raise_exception(self):
        self.cur.execute('insert into abbreviations values (null, "tm", "2020-01-01", "2020-01-01")')
        self.cur.execute('insert into names values (null, "Theresa Moosmann", "2020-01-01", "2020-01-01")')

        with self.assertRaises(Exception):
            map_abbreviations_to_authors.insert_mapped_authors(self.cur, self.author_mapping)


    def test_insert_mapped_authors_with_name_already_in_db_but_no_authors_names_raise_exception(self):
        self.cur.execute('insert into names values (null, "Mark Daniel", "2020-01-01", "2020-01-01")')

        with self.assertRaises(Exception):
            map_abbreviations_to_authors.insert_mapped_authors(self.cur, self.author_mapping)


    def test_insert_mapped_authors_with_name_already_in_db(self):
        self.cur.execute('insert into names values (null, "Mark Daniel", "2020-01-01", "2020-01-01")')
        name_id = self.cur.lastrowid
        author_id = 1337
        self.cur.execute('insert into authors values (?, "2020-01-01", "2020-01-01")', (author_id,))
        self.cur.execute('insert into author_names values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, name_id))

        map_abbreviations_to_authors.insert_mapped_authors(self.cur, self.author_mapping)

        self.cur.execute('select id, name from names where name = "Mark Daniel"')
        names_rows = self.cur.fetchall()
        self.assertEqual(1, len(names_rows))

        self.cur.execute('select id, author_id, name_id from author_names where name_id = ?', (names_rows[0][0],))
        author_names_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_names_rows))

        self.cur.execute('select id from authors where id = ?', (author_names_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))

        self.cur.execute('select id, abbreviation from abbreviations where abbreviation = "md"')
        abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(abbreviations_rows))

        self.cur.execute('select id, author_id, abbreviation_id from author_abbreviations where abbreviation_id = ?', (abbreviations_rows[0][0],))
        author_abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_abbreviations_rows))

        # test that is same id
        self.assertEqual(author_names_rows[0][1], author_abbreviations_rows[0][1])

    def test_insert_mapped_authors_with_abbreviation_already_in_db(self):
        self.cur.execute('insert into abbreviations values (null, "md", "2020-01-01", "2020-01-01")')
        abbreviation_id = self.cur.lastrowid
        author_id = 1337
        self.cur.execute('insert into authors values (?, "2020-01-01", "2020-01-01")', (author_id,))
        self.cur.execute('insert into author_abbreviations values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, abbreviation_id))

        map_abbreviations_to_authors.insert_mapped_authors(self.cur, self.author_mapping)

        self.cur.execute('select id, name from names where name = "Mark Daniel"')
        names_rows = self.cur.fetchall()
        self.assertEqual(1, len(names_rows))

        self.cur.execute('select id, author_id, name_id from author_names where name_id = ?', (names_rows[0][0],))
        author_names_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_names_rows))

        self.cur.execute('select id from authors where id = ?', (author_names_rows[0][1],))
        authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(authors_rows))

        self.cur.execute('select id, abbreviation from abbreviations where abbreviation = "md"')
        abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(abbreviations_rows))

        self.cur.execute('select id, author_id, abbreviation_id from author_abbreviations where abbreviation_id = ?', (abbreviations_rows[0][0],))
        author_abbreviations_rows = self.cur.fetchall()
        self.assertEqual(1, len(author_abbreviations_rows))

        # test that is same id
        self.assertEqual(author_names_rows[0][1], author_abbreviations_rows[0][1])