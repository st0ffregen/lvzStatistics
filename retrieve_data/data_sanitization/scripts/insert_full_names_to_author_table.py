import sqlite3
from datetime import datetime
from collections import defaultdict
import tqdm
import json

# this scripts retrieves all articles with at least one full name and adds it to the authors table
# as well as the article_authors mapping table.
# TODO: add script for adding articles where author_array is null as lvz authors in the authors table as well as the article_authors mapping table. Do that in retrieval script

def get_db_connection():
    con = sqlite3.connect('../data/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur

def retrieve_articles(cur):
    cur.execute('select id, author_array, author_is_abbreviation from articles ar where ar.organization = \'lvz\' and ar.author_is_abbreviation like \'%false%\'')
    rows = cur.fetchall()
    articles = []

    for row in rows:
        row_dict = {
            'id': row[0],
            'author_array': json.loads(row[1]),
            'author_is_abbreviation': json.loads(row[2])
        }
        articles.append(row_dict)

    return articles


def get_full_names(articles):
    authors = defaultdict(list)

    for article in articles:
        for idx, author in enumerate(article['author_array']):
            if article['author_is_abbreviation'][idx] is False:
                authors[author].append(article['id'])

    return authors

def save_authors_to_db(authors, con, cur):
    print('saving authors to db')
    for idx, (author, article_ids) in enumerate(tqdm.tqdm(authors.items())):
        updated_at = datetime.utcnow().isoformat()
        existing_author = cur.execute('select id from authors where name = ?', (author,)).fetchone()

        if existing_author is None:
            cur.execute('insert into authors values (?,?,?,?,?,?)',
                        (None, author, json.dumps(None),
                         json.dumps(None), updated_at, updated_at))
            author_id = cur.lastrowid
        else:
            author_id = existing_author[0]

        cur.executemany('insert into article_authors values (?,?,?,?,?)',
                    [(None, id, author_id, updated_at, updated_at) for id in article_ids])

        if idx > 0 and idx % 5000 == 0:
            con.commit()
    con.commit()


def main():
    con, cur = get_db_connection()
    articles = retrieve_articles(cur)
    authors = get_full_names(articles)
    save_authors_to_db(authors, con, cur)


if __name__ == '__main__':
    main()