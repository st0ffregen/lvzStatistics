import sqlite3
from datetime import datetime
from typing import Tuple
from dateutil.relativedelta import relativedelta
import tqdm
import re
import math
from collections import Counter
from src.models.AuthorDTO import AuthorDTO
from src.models.MatchingType import MatchingType

# this scripts reads in the authors of the articles
# it tries to connect the abbreviations to a full name
# from an abbreviation it attempts to find an author name similar to the abbreviation in a predefined time window
# it attempts first to find a direct match where the abbreviation matches the first character of the first name and the first character of the last name
# if it does not yield any results we apply a fuzzy matching
# we determine a certainty score to later decide the best match based on certainty and other heuristics

organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline', 'lvz-online'] + ['daz', 'oaz', 'ovz'] # second are regional newspaper belonging to the LVZ
batch_size = 100  # TODO: check again, if this could be a problem when abbreviated articles are sparse. plot graph displaying the number of articles with abbreviations over time
database_batch_size = 5000 # when to update the database


def main():
    search_for_proximity_full_name()

def search_for_proximity_full_name():
    con, cur = get_db_connection()
    months = 6
    abbreviations = get_abbreviations_with_articles(cur)
    abbreviation_to_name_mapping = {}
    matches_found = 0

    window_names = get_names_window(cur, abbreviations[0], months=months)

    for idx, abbreviation in enumerate(tqdm.tqdm(abbreviations)):
        window_names_with_frequency = get_frequency_for_names(window_names)

        match = search_for_full_name(abbreviation, window_names_with_frequency)

        if match is None:
            #print(f"{idx}/{len(abbreviations)}: Could not find match for abbreviation {abbreviation}. Continuing.")
            continue

        matches_found += 1

        abbreviation_to_name_mapping[abbreviation['id']] = match

        if abbreviation is None:
            save_matches_to_db(con, cur, abbreviation_to_name_mapping)
            break

        if idx > 0 and idx % batch_size == 0:
            window_names = get_names_window(cur, abbreviation, months=months)

        if idx > 0 and idx % database_batch_size == 0:
            save_matches_to_db(con, cur, abbreviation_to_name_mapping)
            abbreviation_to_name_mapping = {}

    print(f"Found {matches_found} matches. {len(abbreviation_to_name_mapping)} abbreviations were not matched.")


def save_matches_to_db(con, cur, abbreviation_to_name_mapping: dict[AuthorDTO]):
    for abbr_id, abbreviation_to_author in abbreviation_to_name_mapping.items():
        updated_at = datetime.utcnow().isoformat()
        certainty = round(abbreviation_to_author.matching_certainty, 3) if abbreviation_to_author.matching_certainty is not None else None
        cur.execute('update unmapped_authors set name = ?, matching_certainty = ?, matching_type = ?, updated_at = ? where id = ?',
                    (abbreviation_to_author.name,
                     certainty, abbreviation_to_author.matching_type.name, updated_at, abbr_id))
    con.commit()

def get_abbreviations_with_articles(cur):
    cur.execute('SELECT au.id, au.abbreviation, ar.published_at FROM articles ar join unmapped_article_authors aa on ar.id=aa.article_id join unmapped_authors au on aa.author_id=au.id where ar.organization = "lvz" and au.matching_type = ? order by ar.published_at asc', (MatchingType.IS_ABBREVIATION.name,))
    rows = cur.fetchall()

    abbreviations = []

    for row in rows:
        row_dict = {
            'id': row[0],
            'abbreviation': row[1],
            'published_at': row[2]
        }
        abbreviations.append(row_dict)

    return abbreviations


def get_db_connection():
    con = sqlite3.connect('../../../data/interim/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


def get_frequency_for_names(names: list[{str, str, str}]) -> dict[str, int]:
    names_with_frequency = Counter([name["name"] for name in names])
    del names_with_frequency['']  # Remove empty author if present
    return names_with_frequency


def search_for_full_name(focused_abbreviation: dict, all_names: dict[str, int]) -> AuthorDTO | None:
    focused_abbreviation["abbreviation"] = focused_abbreviation["abbreviation"].lower().replace('.', '')
    all_names = all_names.copy()

    add_naive_abbreviation(all_names)

    direct_match = find_direct_match(all_names, focused_abbreviation["abbreviation"])

    if direct_match is not None:
        return direct_match

    fuzzy_match = find_fuzzy_match(all_names, focused_abbreviation["abbreviation"])

    if fuzzy_match is not None:
        return fuzzy_match

    return None


def find_fuzzy_match(all_names: dict, abbreviation: str) -> AuthorDTO | None:
    # fuzzy matches follow the conditions:
    # 1. all abbreviations chars are contained in the author name
    # 2. the abbreviation chars are in the correct order (note there are exceptions e.g. "Nils Inker" with abbreviation "in" for "Inker" would not be found)
    # further there are conditions that higher the certainty of the match:
    # 3. the abbreviation chars match the first characters of the author's name parts (e.g. first name, middle name...)
    # 4. there is one abbreviation char that matches the first char of the last name
    # 4.1 that char is not the first char of the abbreviation

    matches = []

    for name, frequency_and_abbreviation in all_names.items():
        full_name_split = re.split(r' |-', name.lower())
        first_name = full_name_split[0]
        last_name = full_name_split[-1]
        certainty = 0

        if len(full_name_split) < 2:
            # author's name is likely not a real name
            continue

        if are_necessary_conditions_fullfilled(name.lower(), abbreviation) is False:
            continue

        certainty = calculate_fuzzy_certainty(abbreviation, certainty, first_name, full_name_split, last_name)

        matches.append(
            {'name': name, 'frequency': frequency_and_abbreviation['frequency'], 'certainty': certainty})

    if len(matches) == 0:
        return None

    add_frequency_based_certainty_for_fuzzy_matches(matches)

    matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)

    return AuthorDTO(matches[0]['name'], abbreviation, round(matches[0]['certainty'], 3), MatchingType.FUZZY_MATCH)


def add_frequency_based_certainty_for_fuzzy_matches(matches):
    frequency_values = [match['frequency'] for match in matches]
    min_frequency = min(frequency_values)
    max_frequency = max(frequency_values)
    if min_frequency == max_frequency:  # avoid division by zero
        for idx, match in enumerate(matches):
            matches[idx]['certainty'] += 0.3
    else:
        # update certainty based on normalized frequency
        for idx, match in enumerate(matches):
            matches[idx]['certainty'] += 0.3 * (match['frequency'] - min_frequency) / (
                    max_frequency - min_frequency)
            # multiplies a penalty term for small frequencies: min(0.05 *  frequency,1)
            # matches[idx]['certainty'] = min(0.2 * matches[idx]['frequency'], 1) * matches[idx]['certainty']


def calculate_fuzzy_certainty(abbreviation, certainty, first_name, full_name_split, last_name):
    # conditions that increase certainty
    # add 0.2 certainty if for each split in full_name_split there is a char in the abbreviation and it is matching the index
    if len(abbreviation) == len(full_name_split):
        for idx, split in enumerate(full_name_split):
            if abbreviation[idx] == split[0]:
                certainty += 0.3
    else:
        if abbreviation[0] == first_name[0]:
            certainty += 0.3

        if abbreviation[-1] == last_name[0]:
            certainty += 0.3

        elif any([char == last_name[0] for char in abbreviation]):
            certainty += 0.1
            if any([char == last_name[0] for char in abbreviation[1:]]):
                # if it is not the first character
                certainty += 0.1

    return certainty


def are_necessary_conditions_fullfilled(name, abbreviation):
    if all([char in name for char in abbreviation]) is False:
        return False

    if ordered_abbreviation_chars_match_name(name, abbreviation) is False:
        return False

    return True


def ordered_abbreviation_chars_match_name(author, author_abbreviation):
    # checks if the abbreviation chars are contained in the name in an order so that each abbr char is after the previous one both in abbreviation and name
    # e.g. abbreviation "has" would fit into "Theresa Moosmann" as index: 1 (h) < 6 (a) < 11 (s)
    # in this example just checking with index(abbr_char) would return first index of each char resulting in 1 (h) < 6 (a) > 5 (s) and lead to a false negative

    indices = [author.index(author_abbreviation[0])]
    for abbr_idx, abbr_char in enumerate(author_abbreviation[1:]):
        possible_author_indices = [idx for idx, char in enumerate(author) if char == abbr_char]
        indices.append(min(possible_author_indices, key=lambda x: x - indices[-1] if x > indices[-1] else math.inf))

    return all([indices[idx] <= indices[idx + 1] for idx in range(len(indices) - 1)])


def find_direct_match(all_names: dict[str, dict], focused_abbreviation: str) -> AuthorDTO:
    direct_matches: list[AuthorDTO] = []

    matches: list[dict] = []
    for name, frequency_and_naive_abbreviation in all_names.items():
        if focused_abbreviation == frequency_and_naive_abbreviation['naive_abbreviation']:
            matches.append(
                {'name': name, 'frequency': frequency_and_naive_abbreviation['frequency'], 'certainty': None})

    # assign direct matches the name with the highest frequency
    # assign base certainty of 0.7 for being a direct match
    # adds up possible 0.2 certainty
    # assigns 0.1 certainty if all names have the same frequency
    if len(matches) > 0:
        add_frequency_based_certainty_for_direct_matches(matches)

        matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)
        return AuthorDTO(matches[0]['name'], focused_abbreviation, round(matches[0]['certainty'], 3), MatchingType.DIRECT_MATCH)

    return None

def add_frequency_based_certainty_for_direct_matches(matches):
    # calculate certainty based on normalized frequency
    frequency_values = [match['frequency'] for match in matches]
    min_frequency = min(frequency_values)
    max_frequency = max(frequency_values)
    if max_frequency == min_frequency:  # avoid division by zero
        if len(matches) == 1:
            matches[0]['certainty'] = 0.8
        else:
            for idx, match in enumerate(matches):
                matches[idx]['certainty'] = 0.1
    else:
        # update certainty based on normalized frequency
        for idx, match in enumerate(matches):
            matches[idx]['certainty'] = 0.7
            matches[idx]['certainty'] += 0.2 * (match['frequency'] - min_frequency) / (
                    max_frequency - min_frequency)
            # multiplies a penalty term for small frequencies: min(0.2 *  frequency,1)
            # matches[idx]['certainty'] = min(0.2 * matches[idx]['frequency'], 1) * matches[idx]['certainty']


def add_naive_abbreviation(names):
    for name, frequency in names.items():
        naive_abbreviation = ''.join([first_char[0] for first_char in re.split(r' |-', name) if first_char != '']).lower()
        names[name] = {'frequency': frequency, 'naive_abbreviation': naive_abbreviation}


def get_abbreviations(focused_article):
    author_abbreviations = set()
    for idx, author in enumerate(focused_article['author_array']):
        if focused_article['author_is_abbreviation'][idx]:
            author_abbreviations.add(author.lower().replace('.', ''))

    return author_abbreviations


def add_full_names(focused_article) -> Tuple[list[AuthorDTO], list[bool], list[dict]]:
    full_names = [AuthorDTO(author, None, None, MatchingType.IS_FULL_NAME) for author, is_abbreviated in zip(focused_article['author_array'], focused_article['author_is_abbreviation']) if is_abbreviated is False]
    remaining_authors = [{'abbreviation': None, 'author': author, 'certainty': None} for author, is_abbreviated in zip(focused_article['author_array'], focused_article['author_is_abbreviation']) if is_abbreviated]
    remaining_author_is_abbreviation = [True] * len(remaining_authors)
    return full_names, remaining_author_is_abbreviation, remaining_authors

def add_organization_matches(focused_article):
    author_array = focused_article['author_array']
    remaining_authors = []
    remaining_author_is_abbreviation = []
    matches = []

    for author in author_array:
        if author.lower() in organizations:
            matches.append(AuthorDTO(author.lower(), author.lower(), 1, MatchingType.ORGANIZATION_MATCH))
        else:
            remaining_authors.append(author)
            remaining_author_is_abbreviation.append(
                focused_article['author_is_abbreviation'][author_array.index(author)])

    return matches, remaining_author_is_abbreviation, remaining_authors


def get_succeeding_focused_article(articles_in_window, focused_article):
    # get succeeding article where at least one author is an abbreviation
    focused_article_index = articles_in_window.index(focused_article)
    next_index = focused_article_index + 1

    while True:
        if next_index == len(articles_in_window):
            return None

        next_article = articles_in_window[next_index]

        if next_article['author_is_abbreviation'] is not None and any(next_article['author_is_abbreviation']):
            return next_article

        next_index += 1


def get_names_window(cur, focused_abbreviation, months=6) -> list[{str, str, str}]:
    abbreviation_date = focused_abbreviation['published_at']
    abbreviation_date = datetime.strptime(abbreviation_date, '%Y-%m-%dT%H:%M:%S%z')
    lower_date_limit = (abbreviation_date - relativedelta(months=months)).isoformat()
    upper_date_limit = (abbreviation_date + relativedelta(months=months)).isoformat()

    cur.execute(
        'SELECT au.name, ar.published_at FROM articles ar join unmapped_article_authors aa on ar.id=aa.article_id join unmapped_authors au on aa.author_id=au.id where ar.organization = "lvz" and au.matching_type = ? and published_at >= ? and published_at <= ? order by ar.published_at asc', (MatchingType.IS_FULL_NAME, lower_date_limit, upper_date_limit))
    fetched_names = cur.fetchall()
    window_names = [{'name': name[0], 'published_at': name[1]} for name in fetched_names]

    return window_names



if __name__ == '__main__':
    main()