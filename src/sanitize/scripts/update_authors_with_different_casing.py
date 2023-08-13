# Sets author names to the most prevalent one for every name that is matching when case insensitive
import json
import sqlite3
import pandas as pd

def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur

def close_db_connection(cur, con):
    cur.close()
    con.close()

def update_authors():
    con, cur = get_db_connection()

    rows = cur.execute('select author_array, id from articles where organization = "lvz" and author_array != "null"').fetchall()
    authors = pd.DataFrame(rows, columns=["author_array", "id"])
    authors["author_array"] = authors["author_array"].apply(lambda x: json.loads(x))
    # explode on author_array
    authors = authors.explode("author_array")
    # rename author_array to author
    authors = authors.rename(columns={"author_array": "author"})
    authors_without_duplicates = authors.drop_duplicates(subset=["author"], keep="first")
    authors_without_duplicates["author_lower"] = authors_without_duplicates["author"].apply(lambda x: x.lower())
    authors_with_different_writing = authors_without_duplicates[authors_without_duplicates.duplicated(subset=["author_lower"], keep=False)]
    # create count column with count of author name in authors dataframe
    authors_with_different_writing["count"] = authors_with_different_writing["author"].apply(lambda x: authors[authors["author"] == x]["author"].count())
    authors_without_duplicates = authors_with_different_writing.sort_values("count", ascending=False).drop_duplicates(subset=["author_lower"], keep="first")
    # get ids from authors where author column equals author_lower column of authors_without_duplicates but no author column of authors_without_duplicates
    ids = authors[authors["author"].str.lower().isin(authors_without_duplicates["author_lower"]) & ~authors["author"].isin(authors_without_duplicates["author"])]["id"].unique()
    print(f"need to update {len(ids)} articles!")
    authors_to_be_updated = authors[authors["id"].isin(ids)]
    # set author column to value of author column in authors_without_duplicates if it is present in authors_without_duplicates
    authors_to_be_updated["author"] = authors_to_be_updated["author"].apply(lambda x: authors_without_duplicates[authors_without_duplicates["author_lower"] == x.lower()]["author"].values[0] if authors_without_duplicates[authors_without_duplicates["author_lower"] == x.lower()].shape[0] == 1 else x)
    # implode to author_array
    authors_to_be_updated = authors_to_be_updated.groupby('id')['author'].apply(list).reset_index(name='author_array')
    authors_to_be_updated["author_array"] = authors_to_be_updated["author_array"].apply(lambda x: json.dumps(x))
    # generate update statements
    cur.executemany("update articles set author_array = ? where id = ?", [(author_array, id) for id, author_array in zip(authors_to_be_updated['id'], authors_to_be_updated['author_array'])])
    # commit changes
    con.commit()
    # get affected rows
    affected_rows = cur.rowcount

    print(f"Affected rows: {affected_rows}")
    close_db_connection(cur, con)


def main():
    update_authors()


if __name__ == '__main__':
    main()
