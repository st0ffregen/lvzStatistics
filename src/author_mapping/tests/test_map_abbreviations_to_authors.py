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
        unmapped_abbreviations = self.authors[~self.authors["abbreviation"].isin(self.author_mapping["abbreviation"])]
        map_abbreviations_to_authors.insert_unmapped_abbreviations(self.cur, unmapped_abbreviations)

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
        unmapped_names = self.authors[~self.authors["full_name"].isin(self.author_mapping["full_name"])]
        map_abbreviations_to_authors.insert_unmapped_names(self.cur, unmapped_names)

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

    def test_create_new_mapping_with_abbreviation_already_in_db(self):
        self.cur.execute('insert into abbreviations values (null, "md", "2020-01-01", "2020-01-01")')
        abbreviation_id = self.cur.lastrowid
        author_id = 1337
        self.cur.execute('insert into authors values (?, "2020-01-01", "2020-01-01")', (author_id,))
        self.cur.execute('insert into author_abbreviations values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, abbreviation_id))

        article_id = 1338
        all_articles = [{'id': article_id, 'author_array': ["md"], 'author_is_abbreviation': [True]}]

        map_abbreviations_to_authors.create_new_mapping(self.cur, all_articles)

        self.cur.execute('select article_id, author_id from mapped_article_authors')
        mapped_article_authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(mapped_article_authors_rows))
        self.assertEqual(article_id, mapped_article_authors_rows[0][0])
        self.assertEqual(author_id, mapped_article_authors_rows[0][1])

    def test_create_new_mapping_with_name_already_in_db(self):
        self.cur.execute('insert into names values (null, "Mark Daniel", "2020-01-01", "2020-01-01")')
        name_id = self.cur.lastrowid
        author_id = 1337
        self.cur.execute('insert into authors values (?, "2020-01-01", "2020-01-01")', (author_id,))
        self.cur.execute('insert into author_names values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, name_id))

        article_id = 1338
        all_articles = [{'id': article_id, 'author_array': ["Mark Daniel"], 'author_is_abbreviation': [False]}]

        map_abbreviations_to_authors.create_new_mapping(self.cur, all_articles)

        self.cur.execute('select article_id, author_id from mapped_article_authors')
        mapped_article_authors_rows = self.cur.fetchall()
        self.assertEqual(1, len(mapped_article_authors_rows))
        self.assertEqual(article_id, mapped_article_authors_rows[0][0])
        self.assertEqual(author_id, mapped_article_authors_rows[0][1])

    def test_create_new_mapping_with_both_name_and_abbreviation_already_in_db(self):
        self.cur.execute('insert into abbreviations values (null, "md", "2020-01-01", "2020-01-01")')
        abbreviation_id = self.cur.lastrowid
        author_id = 1337
        self.cur.execute('insert into authors values (?, "2020-01-01", "2020-01-01")', (author_id,))
        self.cur.execute('insert into author_abbreviations values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, abbreviation_id))

        self.cur.execute('insert into names values (null, "Mark Daniel", "2020-01-01", "2020-01-01")')
        name_id = self.cur.lastrowid
        self.cur.execute('insert into author_names values (null, ?, ?, "2020-01-01", "2020-01-01")', (author_id, name_id))

        first_article_id = 1338
        second_article_id = 1339
        all_articles = [
            {'id': first_article_id, 'author_array': ["Mark Daniel"], 'author_is_abbreviation': [False]},
            {'id': second_article_id, 'author_array': ["md"], 'author_is_abbreviation': [True]}
        ]

        map_abbreviations_to_authors.create_new_mapping(self.cur, all_articles)

        self.cur.execute('select article_id, author_id from mapped_article_authors order by article_id asc')
        mapped_article_authors_rows = self.cur.fetchall()
        self.assertEqual(2, len(mapped_article_authors_rows))
        self.assertEqual(first_article_id, mapped_article_authors_rows[0][0])
        self.assertEqual(author_id, mapped_article_authors_rows[0][1])
        self.assertEqual(second_article_id, mapped_article_authors_rows[1][0])
        self.assertEqual(author_id, mapped_article_authors_rows[1][1])


    def test_create_new_mapping_with_name_not_present_in_db(self):
        article_id = 1337
        name = "Mark Daniel"
        all_articles = [{'id': article_id, 'author_array': [name], 'author_is_abbreviation': [False]}]

        map_abbreviations_to_authors.create_new_mapping(self.cur, all_articles)

        # test for name presences in name table
        self.cur.execute('select id, name from names where name = ?', (name,))
        names_rows = self.cur.fetchall()
        name_id = names_rows[0][0]

        self.cur.execute('select id, author_id, name_id from author_names where name_id = ?', (name_id,))
        author_names_rows = self.cur.fetchall()
        author_id = author_names_rows[0][1]

        self.cur.execute('select article_id, author_id from mapped_article_authors where author_id = ? and article_id = ?', (author_id, article_id))
        mapped_article_authors_rows = self.cur.fetchall()

        self.assertEqual(1, len(author_names_rows))
        self.assertEqual(1, len(names_rows))
        self.assertEqual(1, len(mapped_article_authors_rows))


    def test_create_new_mapping_with_abbreviation_not_present_in_db(self):
        article_id = 1337
        abbreviation = "md"
        all_articles = [{'id': article_id, 'author_array': [abbreviation], 'author_is_abbreviation': [True]}]

        map_abbreviations_to_authors.create_new_mapping(self.cur, all_articles)

        # test for name presences in name table
        self.cur.execute('select id, abbreviation from abbreviations where abbreviation = ?', (abbreviation,))
        abbreviations_rows = self.cur.fetchall()
        abbreviation_id = abbreviations_rows[0][0]

        self.cur.execute('select id, author_id, abbreviation_id from author_abbreviations where abbreviation_id = ?', (abbreviation_id,))
        author_abbreviations_rows = self.cur.fetchall()
        author_id = author_abbreviations_rows[0][1]

        self.cur.execute('select article_id, author_id from mapped_article_authors where author_id = ? and article_id = ?', (author_id, article_id))
        mapped_article_authors_rows = self.cur.fetchall()

        self.assertEqual(1, len(author_abbreviations_rows))
        self.assertEqual(1, len(abbreviations_rows))
        self.assertEqual(1, len(mapped_article_authors_rows))

    def test_remove_possible_duplicates(self):
        article = {}
        article['author_array'] = ["Mark Daniel", "tm", "Mark Daniel"]
        article['author_is_abbreviation'] = [False, True, False]

        map_abbreviations_to_authors.remove_possible_duplicates(article)
        self.assertEqual(2, len(article['author_array']))
        self.assertEqual(2, len(article['author_is_abbreviation']))
        self.assertEqual("Mark Daniel", article['author_array'][0])
        self.assertEqual(False, article['author_is_abbreviation'][0])
        self.assertEqual("tm", article['author_array'][1])
        self.assertEqual(True, article['author_is_abbreviation'][1])
