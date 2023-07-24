import json
import sqlite3
from datetime import datetime

import tqdm

THRESHOLD = 5

def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur

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
            cur.execute(f'update articles set author_array = \'["lvz"]\', updated_at = ? where author_array not like "%,%" and id in {"(" + ",".join(ids) + ")"}', (datetime.utcnow().isoformat(),))
            affected_rows += cur.rowcount
            # update articles with multiple authors
            r = cur.execute(f'select id, author_array from articles where author_array like "%,%" and id in {"(" + ",".join(ids) + ")"}').fetchall()
            for id_and_author_array in r:
                id = id_and_author_array[0]
                old_authors = json.loads(id_and_author_array[1])
                new_authors = [a for a in old_authors if a != author]
                cur.execute('update articles set author_array = ?, updated_at = ? where id = ?', (json.dumps(new_authors), datetime.utcnow().isoformat(), id))
                affected_rows += cur.rowcount
            con.commit()

    print(f"Affected rows: {affected_rows}")


def main():
    remove_authors()


if __name__ == '__main__':
    main()
