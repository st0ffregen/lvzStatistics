import json
import sqlite3
from datetime import datetime

import tqdm

THRESHOLD = 5

def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur

def close_db_connection(cur, con):
    cur.close()
    con.close()

def remove_authors():
    con, cur = get_db_connection()

    rows = cur.execute('select author_array from articles group by author_array having count(*) < ?', (THRESHOLD,)).fetchall()
    # extract all authors
    authors = [author for row in rows for author in json.loads(row[0])]
    # remove duplicates
    authors = list(set(authors))
    affected_rows = 0

    for author in tqdm.tqdm(authors):
        rows = cur.execute("select id from articles where author_array like ?", ("%" + json.dumps(author) + "%",)).fetchall()
        ids = [str(row[0]) for row in rows]
        if len(ids) < THRESHOLD:
            # update articles with single authors
            cur.execute(f'update articles set author_array = \'["lvz"]\', author_is_abbreviation = \'[true]\', updated_at = ? where author_array not like "%,%" and id in {"(" + ",".join(ids) + ")"}', (datetime.utcnow().isoformat(),))
            affected_rows += cur.rowcount
            # update articles with multiple authors
            row_to_update = cur.execute(f'select id, author_array, author_is_abbreviation from articles where author_array like "%,%" and id in {"(" + ",".join(ids) + ")"}').fetchall()
            for row in row_to_update:
                id = row[0]
                old_authors = json.loads(row[1])
                old_author_is_abbreviation = json.loads(row[2])
                new_authors = [a for a in old_authors if a != author]
                index = old_authors.index(author)
                new_author_is_abbreviation = [a for i, a in enumerate(old_author_is_abbreviation) if i != index]
                cur.execute('update articles set author_array = ?, author_is_abbreviation = ?, updated_at = ? where id = ?', (json.dumps(new_authors), json.dumps(new_author_is_abbreviation), datetime.utcnow().isoformat(), id))
                affected_rows += cur.rowcount
            con.commit()

    print(f"Affected rows: {affected_rows}")
    close_db_connection(cur, con)


def main():
    remove_authors()


if __name__ == '__main__':
    main()
