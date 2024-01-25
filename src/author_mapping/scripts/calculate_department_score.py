import sqlite3
import tqdm
import pandas as pd
import numpy as np
import json
from src.models.MatchingType import MatchingType
from scipy.stats import wasserstein_distance
from src.utils.author_mapping.determine_department_entity_shares import determine_departments_abbreviation_and_full_name_shares

DEPARTMENT_THRESHOLD = 10
PENALIZATION_SCORE_SCALAR = 1
SMALL_DEPARTMENT_NUMBER_PENALTY_Y_INTERSECT = 0.2
SMALL_DEPARTMENT_NUMBER_PENALTY_SLOPE = -0.05


# This calculates the department score for each mapping.

def calculate_department_score() -> pd.DataFrame:
    con, cur = get_db_connection()

    department_affiliation = get_data(cur)

    department_affiliation = prepare_data(department_affiliation)

    name_abbreviation_dict = get_full_name_abbreviations_dict(department_affiliation)

    department_affiliation = clean_data(department_affiliation)

    results = pd.DataFrame(
        columns=['full_name', 'abbreviation', 'wasserstein_distance', 'n_departments', 'n_not_overlapping_departments',
                 'penalization_score', 'department_score'])

    departments_scaler_score = determine_departments_abbreviation_and_full_name_shares(cur)

    for name, abbreviation in tqdm.tqdm(name_abbreviation_dict):

        departments_filtered_for_name = department_affiliation[(department_affiliation["name"] == name)]
        name_department_count = departments_filtered_for_name.groupby(['name', 'department']).size().reset_index(
            name='count').sort_values(['name', 'count'], ascending=[True, False])

        departments_filtered_for_abbr = department_affiliation[(department_affiliation["abbreviation"] == abbreviation)]
        abbr_department_count = departments_filtered_for_abbr.groupby(
            ['abbreviation', 'department']).size().reset_index(name='count').sort_values(['abbreviation', 'count'],
                                                                                         ascending=[True, False])

        # scale the article count up or down depending on the full_name/abbreviation share of the department
        abbr_department_count = scale_department_count(abbr_department_count, departments_scaler_score, "abbreviation_share")
        name_department_count = scale_department_count(name_department_count, departments_scaler_score, "full_name_share")

        # remove departments with less than 10 articles to get rid of noise
        # Note: this might result in a department not being in both lists anymore because it had less than DEPARTMENT_THRESHOLD articles for one of the two entities (e.g. increasing the penalty)
        name_department_count = name_department_count[name_department_count["count"] >= DEPARTMENT_THRESHOLD]
        abbr_department_count = abbr_department_count[abbr_department_count["count"] >= DEPARTMENT_THRESHOLD]

        # get number of departments that for the author entity
        n_departments_for_author = len(
            set(name_department_count["department"].tolist() + abbr_department_count["department"].tolist()))

        # get number of departments that are not in both lists (needed for penalization later)
        n_not_overlapping_departments = len(
            set(name_department_count["department"].tolist()) ^ set(abbr_department_count["department"].tolist()))

        # remove departments that are not in both lists
        name_department_count = name_department_count[
            name_department_count["department"].isin(abbr_department_count["department"].tolist())]
        abbr_department_count = abbr_department_count[
            abbr_department_count["department"].isin(name_department_count["department"].tolist())]

        # create lists of the departments for each entity
        name_department_list = name_department_count["department"].tolist()
        abbr_department_list = abbr_department_count["department"].tolist()

        # order the two dataframes by the same order of departments
        categorical = pd.Categorical(name_department_count["department"],
                                     categories=name_department_count["department"].tolist())
        abbr_department_count = abbr_department_count.set_index("department").reindex(categorical).reset_index()

        # get counts into a list each
        name_department_count_list = name_department_count["count"].tolist()
        abbr_department_count_list = abbr_department_count["count"].tolist()

        # if the two lists do not have any overlap, set the distance to one (worst case) as it is the same for the worst normalized score
        # test if any element in abbr_department_count_list is in full_name_department_count_list
        if not any(elem in name_department_list for elem in abbr_department_list):
            score = 1
            # add to results with loc
            results.loc[len(results)] = [name, abbreviation, np.nan, n_departments_for_author, n_not_overlapping_departments,
                                         np.nan, 1]
            continue

        # compare with wasserstein metric
        w_distance = wasserstein_distance(range(0, len(name_department_count_list)),
                                          range(0, len(abbr_department_count_list)), name_department_count_list,
                                          abbr_department_count_list)

        # calculate penalization score
        # construct linear function that penalizes the difference in department arrays
        # it computes the score be taking the percentage of not overlapping departments
        # it gets scaled by a factor alpha
        small_department_number_penalty = max(0, SMALL_DEPARTMENT_NUMBER_PENALTY_Y_INTERSECT + (SMALL_DEPARTMENT_NUMBER_PENALTY_SLOPE * n_departments_for_author))  # add a small penalty for small numbers of departments
        penalization_score = PENALIZATION_SCORE_SCALAR * (n_not_overlapping_departments / n_departments_for_author + small_department_number_penalty)

        # fill score later after normalization of both wasserstein distance and penalization score
        score = np.nan

        # add to results
        results.loc[len(results)] = [name, abbreviation, w_distance, n_departments_for_author, n_not_overlapping_departments,
                                     penalization_score, score]

    results = normalize_department_score_results(results)

    return results


def normalize_department_score_results(results: pd.DataFrame) -> pd.DataFrame:
    # normalize wasserstein distance
    results["wasserstein_distance_normalized"] = (results["wasserstein_distance"] - results[
        "wasserstein_distance"].min()) / (results["wasserstein_distance"].max() - results[
        "wasserstein_distance"].min())

    # normalize penalization score
    results["penalization_score_normalized"] = (results["penalization_score"] - results[
        "penalization_score"].min()) / (results["penalization_score"].max() - results["penalization_score"].min())

    # compute score for rows where it is not set to 1
    results.loc[results["department_score"].isna(), "department_score"] = 1 / 2 * (
            results["wasserstein_distance_normalized"] + results["penalization_score_normalized"])

    return results


def clean_data(department_affiliation: pd.DataFrame) -> pd.DataFrame:

    # remove rows where department equals "Region" or "Nachrichten" for being to unspecific
    department_affiliation = department_affiliation[department_affiliation.department != 'Region']
    department_affiliation = department_affiliation[department_affiliation.department != 'Nachrichten']

    # set name to None in rows that where matched to prevent from names being matched to articles where the abbreviation is connected to but not the name (e.g. prevent like we are before the proximity matching)
    department_affiliation.loc[~department_affiliation["abbreviation"].isna(), "name"] = None
    return department_affiliation


def prepare_data(department_affiliation: pd.DataFrame) -> pd.DataFrame:

    # get names where matching_type is only IS_FULL_NAME and never has another value
    not_matched_authors = department_affiliation.groupby('name').filter(
        lambda x: all(match_type == MatchingType.IS_FULL_NAME for match_type in x['matching_type'].values))

    # remove rows where name in names_with_only_full_name
    department_affiliation = department_affiliation[~department_affiliation["name"].isin(not_matched_authors["name"].tolist())]

    department_affiliation["department"] = department_affiliation["department"].apply(lambda x: json.loads(x))
    department_affiliation = department_affiliation.explode('department')

    return department_affiliation


def get_full_name_abbreviations_dict(department_affiliation):

    # Get unique name, abbreviation pairs where abbreviation or name is not nan
    name_abbreviation_dict = \
        department_affiliation[(~department_affiliation["name"].isna()) & (~department_affiliation["abbreviation"].isna())][
            ["name", "abbreviation"]].drop_duplicates().values.tolist()

    return name_abbreviation_dict


def scale_department_count(department_count: pd.DataFrame, departments_scaler_score: pd.DataFrame, key) -> pd.DataFrame:
    # apply the scaling to each row
    department_count["count"] = department_count.apply(lambda x: scale_function(x, departments_scaler_score, key), axis=1)

    return department_count


def scale_function(row, departments_scaler_score, share_key):
    # Note: does not scale if department name is not in departments_scaler_score

    return int(row["count"] * 0.5/departments_scaler_score[departments_scaler_score["department"] == row["department"]][share_key].values[0]) if row["department"] in departments_scaler_score["department"].tolist() else row["count"]


def get_data(cur):

    # get all articles with affiliated authors that are not organizations
    rows = cur.execute(
        "SELECT ar.id, ar.article_namespace_array, ar.published_at, a.name, a.abbreviation, a.matching_type FROM articles ar join article_authors aa on ar.id = aa.article_id join unmapped_authors a on aa.author_id = a.id where a.matching_type != ?",
        (MatchingType.ORGANIZATION_MATCH.name,)).fetchall()

    department_affiliation = pd.DataFrame(
        columns=['id', 'department', 'published_at', 'name', 'abbreviation', 'matching_type'], data=rows)

    return department_affiliation


def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur
