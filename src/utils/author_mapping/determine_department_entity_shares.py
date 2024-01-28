import json
import pandas as pd
from src.models.MatchingType import MatchingType


def determine_departments_abbreviation_and_full_name_shares(cur):
    departments = get_data(cur)
    departments = prepare_data(departments)

    # get count for matching type
    grouped_departments = departments.groupby(["department", "matching_type"]).size().reset_index(
        name='count').sort_values(['department', 'matching_type', 'count'], ascending=[True, True, False])

    # Convert 'matching_type' column to categorical to ensure proper sorting
    grouped_departments['matching_type'] = pd.Categorical(grouped_departments['matching_type'],
                                                          categories=['IS_ABBREVIATION', 'IS_FULL_NAME'], ordered=True)

    # Pivot the DataFrame to have separate columns for each matching type
    pivoted_departments = grouped_departments.pivot(index='department', columns='matching_type',
                                                    values='count').reset_index()

    # Calculate shares
    pivoted_departments['abbreviation_share'] = pivoted_departments['IS_ABBREVIATION'] / (
                pivoted_departments['IS_ABBREVIATION'] + pivoted_departments['IS_FULL_NAME'])
    pivoted_departments['full_name_share'] = pivoted_departments['IS_FULL_NAME'] / (
                pivoted_departments['IS_ABBREVIATION'] + pivoted_departments['IS_FULL_NAME'])

    # create new df with ['department', 'abbreviation_share', 'full_name_share'] and a normal index
    departments_scaler_score = pivoted_departments[['department', 'abbreviation_share', 'full_name_share']].copy()
    # set default index name
    departments_scaler_score.index = range(len(departments_scaler_score))

    return departments_scaler_score


def prepare_data(departments):

    departments["department"] = departments["department"].apply(lambda x: json.loads(x))
    departments = departments.explode('department')
    departments.loc[
        departments["matching_type"] == MatchingType.FUZZY_MATCH, "matching_type"] = MatchingType.IS_ABBREVIATION
    departments.loc[
        departments["matching_type"] == MatchingType.DIRECT_MATCH, "matching_type"] = MatchingType.IS_ABBREVIATION

    # filter out departments that do not have both the matching_types
    departments = departments.groupby('department').filter(
        lambda x: all(match_type in x['matching_type'].values for match_type in ['IS_ABBREVIATION', 'IS_FULL_NAME']))

    return departments


def get_data(cur):
    # get all articles with affiliated authors that are not organizations
    rows = cur.execute(
        "SELECT ar.id, ar.article_namespace_array, ar.published_at, a.name, a.abbreviation, a.matching_type FROM articles ar join unmapped_article_authors aa on ar.id = aa.article_id join unmapped_authors a on aa.author_id = a.id where a.matching_type != ?",
        (MatchingType.ORGANIZATION_MATCH.name,)).fetchall()

    departments = pd.DataFrame(columns=['id', 'department', 'published_at', 'name', 'abbreviation', 'matching_type'],
                               data=rows)

    return departments
