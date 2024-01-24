import sqlite3
import pandas as pd

from src.models.MatchingType import MatchingType


def calculate_frequency_score():
    con, cur = get_db_connection()
    authors = get_abbreviations_with_full_names(cur)

    authors["full_name_pointing_to_abbreviation_count"] = authors.groupby(["full_name", "abbreviation"])["full_name"].transform(
        "count")
    authors["abbreviation_pointing_to_full_name_count"] = authors.groupby(["full_name", "abbreviation"])[
        "abbreviation"].transform("count")

    # drop duplicates based on full_name, abbreviation, certainty. I can drop them because ..._count saved the count
    authors.drop_duplicates(subset=["full_name", "abbreviation"], inplace=True)

    # set the share that the full_name has of all full_names that point to that abbreviation
    authors_with_full_name_pointing_to_abbreviation_sum = authors.groupby(["abbreviation"]).agg(
        full_names_pointing_to_abbreviation_sum=("full_name_pointing_to_abbreviation_count", "sum")).reset_index()
    authors = pd.merge(authors, authors_with_full_name_pointing_to_abbreviation_sum, on="abbreviation")
    authors["full_name_pointing_to_abbreviation_share"] = authors["full_name_pointing_to_abbreviation_count"] / authors[
        "full_names_pointing_to_abbreviation_sum"]

    # set the share that the abbreviation has of all abbreviations that point to that full_name
    authors_with_abbreviation_pointing_to_full_name_sum = authors.groupby(["full_name"]).agg(
        abbreviations_pointing_to_full_name_sum=("abbreviation_pointing_to_full_name_count", "sum")).reset_index()
    authors = pd.merge(authors, authors_with_abbreviation_pointing_to_full_name_sum, on="full_name")
    authors["abbreviation_pointing_to_full_name_share"] = authors["abbreviation_pointing_to_full_name_count"] / authors[
        "abbreviations_pointing_to_full_name_sum"]

    # TODO: Rethink, if multiplication is best choice here
    authors["frequency_score"] = authors["full_name_pointing_to_abbreviation_share"] * authors["abbreviation_pointing_to_full_name_share"]

    return authors


def get_abbreviations_with_full_names(cur):
    cur.execute("select id, name, abbreviation, matching_certainty from unmapped_authors where matching_type = ? or matching_type = ?", (MatchingType.FUZZY_MATCH.name, MatchingType.DIRECT_MATCH.name))
    rows = cur.fetchall()
    authors = pd.DataFrame(columns=["id", "full_name", "abbreviation", "certainty"], data=rows)
    authors.set_index("id", inplace=True)
    return authors


def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur
