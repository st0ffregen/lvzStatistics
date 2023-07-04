# Make all articles with an organization author point to the first entry of the organization in the article_author table
# removes all other entries of the organization in the article_author table

import sqlite3

def get_db_connection():
    con = sqlite3.connect('../data/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


if __name__ == '__main__':
    organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline', 'LVZ-Online', 'daz', 'oaz', 'ovz']
    con, cur = get_db_connection()
    for organization in organizations:
        organization = organization.upper()
        print(f"Processing {organization}")
        first_id = cur.execute('select id from authors a where upper(a.name) = ? and upper(a.abbreviation) = ?', (organization, organization)).fetchone()
        if first_id is None:
            print(f"No entries for {organization} found")
            continue
        first_id = first_id[0]
        print("Updating article_authors table")
        cur.execute('update article_authors set author_id = ? where author_id in (select id from authors a where upper(a.name) = ? and upper(a.abbreviation) = ?)', (first_id, organization, organization))
        print(f"Affected rows: {cur.rowcount}")
        print("Deleting entries in authors table")
        cur.execute('delete from authors where upper(name) = ? and upper(abbreviation) = ? and id != ?', (organization, organization, first_id))
        print(f"Affected rows: {cur.rowcount}")
        con.commit()

