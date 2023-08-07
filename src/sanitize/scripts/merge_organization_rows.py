# Make all articles with an organization author point to the first entry of the organization in the article_author table
# removes all other entries of the organization in the article_author table

import sqlite3
from datetime import datetime
from src.models.MatchingType import MatchingType

def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


if __name__ == '__main__':
    organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline', 'LVZ-Online', 'daz', 'oaz', 'ovz']
    con, cur = get_db_connection()
    for organization in organizations:
        organization = organization.upper()
        print(f"Processing {organization}")

        ids = cur.execute('select id from unmapped_authors a where upper(a.name) = ? or upper(a.abbreviation) = ?', (organization, organization)).fetchall()

        if len(ids) == 0:
            print(f"No entries for {organization} found")
            continue
        first_id = ids[0][0]

        print(f"Set matching type {MatchingType.ORGANIZATION_MATCH} for article with first id: {first_id}") # maybe that is not the case before
        cur.execute('update unmapped_authors set matching_type = ?, updated_at = ? where id = ?', (MatchingType.ORGANIZATION_MATCH, datetime.utcnow().isoformat(), first_id))

        print("Updating article_authors table")
        cur.execute('update article_authors set author_id = ?, updated_at = ? where author_id in ' + '(' + ','.join([str(id[0]) for id in ids]) + ')', (first_id, datetime.utcnow().isoformat()))
        print(f"Affected rows: {cur.rowcount}")

        print("Deleting entries in authors table")
        cur.execute('delete from unmapped_authors where (upper(name) = ? or upper(abbreviation) = ?) and id != ?', (organization, organization, first_id))
        print(f"Affected rows: {cur.rowcount}")

        con.commit()

