import json
import sqlite3
from datetime import datetime

from src.models.MatchingType import MatchingType

def mock_database():
    # Create a temporary in-memory SQLite database for testing
    con = sqlite3.connect(':memory:')
    cur = con.cursor()

    # simplified tables for testing
    cur.execute(
        'CREATE TABLE "articles" ( "id" INTEGER, "url" TEXT NOT NULL, "organization" TEXT NOT NULL, "author_array" TEXT, "author_is_abbreviation" TEXT, "article_namespace_array" TEXT,  "published_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL)'
    )
    cur.execute(
        'CREATE TABLE "unmapped_authors" ( "id" INTEGER NOT NULL UNIQUE, "name" TEXT, "abbreviation" TEXT, "matching_certainty" NUMERIC, "matching_type" TEXT, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, PRIMARY KEY("id" AUTOINCREMENT))'
    )
    cur.execute(
        'CREATE TABLE "unmapped_article_authors" ( "id" INTEGER NOT NULL UNIQUE, "article_id" INTEGER NOT NULL, "author_id" INTEGER NOT NULL, "created_at" TEXT NOT NULL, "updated_at" TEXT NOT NULL, UNIQUE("article_id","author_id"), PRIMARY KEY("id" AUTOINCREMENT))'
    )
    cur.execute(
        'CREATE TABLE "abbreviations" (  "id" INTEGER NOT NULL UNIQUE,  "abbreviation" TEXT NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  PRIMARY KEY("id" AUTOINCREMENT));'
    )
    cur.execute(
        'CREATE TABLE "authors" (  "id" INTEGER NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  PRIMARY KEY("id" AUTOINCREMENT) );'
    )
    cur.execute(
        'CREATE TABLE "author_abbreviations" (  "id" INTEGER NOT NULL UNIQUE,  "author_id" INTEGER NOT NULL,  "abbreviation_id" INTEGER NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  FOREIGN KEY("author_id") REFERENCES "authors"("id") ON DELETE CASCADE,  FOREIGN KEY("abbreviation_id") REFERENCES "abbreviations"("id") ON DELETE CASCADE,  PRIMARY KEY("id" AUTOINCREMENT),  UNIQUE("author_id","abbreviation_id") );'
    )
    cur.execute(
        'CREATE TABLE "names" (  "id" INTEGER NOT NULL UNIQUE,  "name" TEXT NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  PRIMARY KEY("id" AUTOINCREMENT) );'
    )
    cur.execute(
        'CREATE TABLE "author_names" (  "id" INTEGER NOT NULL UNIQUE,  "author_id" INTEGER NOT NULL,  "name_id" INTEGER NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  FOREIGN KEY("author_id") REFERENCES "authors"("id") ON DELETE CASCADE,  FOREIGN KEY("name_id") REFERENCES "names"("id") ON DELETE CASCADE,  PRIMARY KEY("id" AUTOINCREMENT),  UNIQUE("author_id","name_id") );'
    )
    cur.execute(
        'CREATE TABLE "mapped_article_authors" (  "id" INTEGER NOT NULL UNIQUE,  "article_id" INTEGER NOT NULL,  "author_id" INTEGER NOT NULL,  "created_at" TEXT NOT NULL,  "updated_at" TEXT NOT NULL,  FOREIGN KEY("author_id") REFERENCES "authors"("id") ON DELETE CASCADE,  FOREIGN KEY("article_id") REFERENCES "articles"("id") ON DELETE CASCADE,  PRIMARY KEY("id" AUTOINCREMENT),  UNIQUE("article_id","author_id") );'
    )


    con.commit()

    return con, cur


def fill_database(articles):
    con, cur = mock_database()

    for article in articles:
        updated_at = datetime.utcnow().isoformat()
        cur.execute(
            'INSERT INTO articles (id, url, author_array, author_is_abbreviation, article_namespace_array, published_at, organization, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (article['id'], article['url'], json.dumps(article['author_array']),
             json.dumps(article['author_is_abbreviation']), json.dumps(article['author_namespace_array']),
             article['published_at'], article['organization'], updated_at))

        for author in article['author_array']:
            abbr = None

            if author == 'lvz':
                matching_type = MatchingType.ORGANIZATION_MATCH.name
                abbr = author
            elif article['author_is_abbreviation'][article['author_array'].index(author)]:
                matching_type = MatchingType.IS_ABBREVIATION.name
                abbr = author
                author = None
            else:
                matching_type = MatchingType.IS_FULL_NAME.name

            cur.execute('insert into unmapped_authors values (?,?,?,?,?,?,?)',
                             (None, author, abbr, None, matching_type, updated_at, updated_at))

            cur.execute('insert into unmapped_article_authors values (?,?,?,?,?)',
                             (None, article['id'], cur.lastrowid, updated_at, updated_at))

    con.commit()

    return con, cur
