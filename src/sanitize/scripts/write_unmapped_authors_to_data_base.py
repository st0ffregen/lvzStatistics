import json
import sqlite3
from datetime import datetime
from src.models.MatchingType import MatchingType
from src.models.AuthorDTO import AuthorDTO

import tqdm

# this scripts writes the author of every article to the database

organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline', 'lvz-online'] + ['daz', 'oaz', 'ovz'] # second are regional newspaper belonging to the LVZ
chunk_size = 5000 #


def main():
    write_authors_to_database()


def write_authors_to_database():
    con, cur = get_db_connection()
    articles = get_articles(cur)
    all_authors: list[AuthorDTO] = []

    for idx, article in enumerate(tqdm.tqdm(articles)):
        if article["author_array"] is None or article['author_is_abbreviation'] is None:
            if idx > 0 and idx % chunk_size == 0:
                save_authors_to_db(con, cur, all_authors)
                all_authors = []
            continue

        article_authors: list[AuthorDTO] = []

        author_array = article['author_array']
        author_is_abbreviation = article['author_is_abbreviation']

        organizations_matches = [AuthorDTO(author.lower(), author.lower(), None, MatchingType.ORGANIZATION_MATCH) for author in author_array if author in organizations]
        article_authors.extend(organizations_matches)
        article_authors.extend([AuthorDTO(author, None, None, MatchingType.IS_FULL_NAME) for author in author_array if author_is_abbreviation[author_array.index(author)] is False and author.lower() not in [a.name for a in organizations_matches]])
        article_authors.extend([AuthorDTO(None, author.lower(), None, MatchingType.IS_ABBREVIATION) for author in author_array if author_is_abbreviation[author_array.index(author)] is True and author.lower() not in [a.name for a in organizations_matches]])

        add_article_id(article, article_authors)
        all_authors.extend(article_authors)

        if idx > 0 and idx % chunk_size == 0:
            save_authors_to_db(con, cur, all_authors)
            all_authors = []


def save_authors_to_db(con, cur, authors: list[AuthorDTO]):
    for author in authors:
        updated_at = datetime.utcnow().isoformat()
        cur.execute('insert into unmapped_authors values (?,?,?,?,?,?,?)',
                    (None, author.name, author.abbreviation,
                     None, author.matching_type.name, updated_at, updated_at))
        cur.execute('insert into article_authors values (?,?,?,?,?)',
                    (None, author.article_id, cur.lastrowid, updated_at, updated_at))
    con.commit()

def add_article_id(article, authors):
    # add article id to every element authors list
    for author in authors:
        author.article_id = article['id']


def get_articles(cur):
    print('fetching articles')
    cur.execute('select id, author_array, author_is_abbreviation, published_at from articles where organization = "lvz" order by published_at asc')
    rows = cur.fetchall()

    articles = []

    for row in rows:
        row_dict = {
            'id': row[0],
            'author_array': json.loads(row[1]),
            'author_is_abbreviation': json.loads(row[2]),
            'published_at': row[3]
        }
        articles.append(row_dict)

    return articles


def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


if __name__ == '__main__':
    main()