import sqlite3
from datetime import datetime
from typing import Tuple
from dateutil.relativedelta import relativedelta
import tqdm
import re
import math
from collections import Counter
import json
from enum import Enum

# this scripts writes the author of every article to the database
# hereby, it tries to connect the abbreviations to the authors' full name
# from an abbreviation it attempts to find an author name similar to the abbreviation in a predefined time window
# it attempts first to find a direct match where the abbreviation matches the first character of the first name and the first character of the last name
# if it does not yield any results we apply a fuzzy matching
# we determine a certainty score to later decide the best match based on certainty and other heuristics

organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline', 'LVZ-Online'] + ['daz', 'oaz', 'ovz'] # second are regional newspaper belonging to the LVZ
batch_size = 100  # TODO: check again, if this could be a problem when abbreviated articles are sparse. plot graph displaying the number of articles with abbreviations over time
database_batch_size = 5000 # when to update the database


class MatchingType(Enum):
    DIRECT_MATCH = 1
    FUZZY_MATCH = 2
    NO_MATCH = 3
    ORGANIZATION_MATCH = 4
    IS_FULL_NAME = 5


class AuthorRow:
    def __init__(self, name: str | None, abbreviation: str | None, matching_certainty: float | None, matching_type: MatchingType, article_id: int | None = None):
        self.name = name
        self.abbreviation = abbreviation
        self.matching_certainty = matching_certainty
        self.matching_type = matching_type
        self.article_id = article_id

    def __eq__(self, other):
        if not isinstance(other, AuthorRow):
            raise NotImplemented("other is not an AuthorRow")

        return self.name == other.name and self.abbreviation == other.abbreviation and self.matching_certainty == other.matching_certainty and self.matching_type == other.matching_type and self.article_id == other.article_id



def main():
    write_author_to_database()

def write_author_to_database():
    con, cur = get_db_connection()
    months = 6
    articles = get_articles(cur)
    current_abbreviation_to_author_mapping = []

    window_articles = get_article_window(cur, articles[0], months=months)

    for idx, article in enumerate(tqdm.tqdm(articles)):
        window_articles_authors_with_frequency = get_authors_with_frequency(window_articles)

        matches = search_for_full_name(article, window_articles_authors_with_frequency)

        add_article_id(article, matches)
        current_abbreviation_to_author_mapping.extend(matches)

        if article is None:
            save_matches_to_db(con, cur, current_abbreviation_to_author_mapping)
            break

        if idx > 0 and idx % batch_size == 0:
            window_articles = get_article_window(cur, article, months=months)

        if idx > 0 and idx % database_batch_size == 0:
            save_matches_to_db(con, cur, current_abbreviation_to_author_mapping)
            current_abbreviation_to_author_mapping = []


def save_matches_to_db(con, cur, current_abbreviation_to_author_mapping: list[AuthorRow]):
    for abbreviation_to_author in current_abbreviation_to_author_mapping:
        updated_at = datetime.utcnow().isoformat()
        certainty = round(abbreviation_to_author.matching_certainty, 3) if abbreviation_to_author.matching_certainty is not None else None
        cur.execute('insert into authors values (?,?,?,?,?,?,?)',
                    (None, abbreviation_to_author.name, abbreviation_to_author.abbreviation,
                     certainty, abbreviation_to_author.matching_type.name, updated_at, updated_at))
        cur.execute('insert into article_authors values (?,?,?,?,?)',
                    (None, abbreviation_to_author.article_id, cur.lastrowid, updated_at, updated_at))
    con.commit()

def add_article_id(article, matches):
    # add focused_article id to every element in matches dict
    for match in matches:
        match.article_id = article['id']


def get_articles(cur):
    cur.execute('select id, author_array, author_is_abbreviation, published_at from articles where organization = "lvz" order by published_at asc')
    rows = cur.fetchall()

    articles = []

    for row in rows:
        row_dict = {
            'id': row[0],
            'author_array': json.loads(row[1]),
            'author_is_abbreviation': json.loads(row[2]),
            'published_at': row[3]
        }
        articles.append(row_dict)

    return articles


def get_db_connection():
    con = sqlite3.connect('../data/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


def get_authors_with_frequency(articles):
    authors_with_frequency = Counter()
    abbreviations = set()

    for article in articles:
        if article['author_array'] is None:
            continue

        abbreviations.update(
            author.lower().strip()
            for author, is_abbreviation in zip(article['author_array'], article['author_is_abbreviation'])
            if is_abbreviation
        )
        authors = [
            author.lower().strip()
            for author, is_abbreviation in zip(article['author_array'], article['author_is_abbreviation'])
            if not is_abbreviation
        ]
        authors_with_frequency.update(authors)

    del authors_with_frequency['']  # Remove empty author if present

    return authors_with_frequency


def at_least_one_author_is_full_name(focused_article):
    return False in focused_article['author_is_abbreviation']

def all_abbreviations_have_a_match(author_abbreviations, matches):
    return all([author_abbreviation in [match['abbreviation'] for match in matches] for
         author_abbreviation in author_abbreviations])


def at_least_one_author_is_an_organization(focused_article):
    return any([author.lower() in organizations for author in focused_article['author_array']])


def search_for_full_name(focused_article, all_authors) -> list[AuthorRow] | None:
    focused_article = focused_article.copy()
    all_authors = all_authors.copy()
    result: list[AuthorRow] = []

    if focused_article['author_is_abbreviation'] is None:
        return None

    if at_least_one_author_is_full_name(focused_article):
        full_names, remaining_author_is_abbreviation, remaining_authors = add_full_names(focused_article)
        result.extend(full_names)

        if len(remaining_authors) == 0:
            return result

    if at_least_one_author_is_an_organization(focused_article):
        matches, remaining_author_is_abbreviation, remaining_authors = add_organization_matches(focused_article)
        result.extend(matches)

        if len(remaining_authors) == 0:
            return result
        else:
            focused_article['author_array'] = remaining_authors
            focused_article['author_is_abbreviation'] = remaining_author_is_abbreviation

    author_abbreviations = get_abbreviations(focused_article)

    prepare_all_authors_dict(all_authors)

    direct_matches = find_direct_matches(all_authors, author_abbreviations)
    result.extend(direct_matches)

    # remove abbreviations that have a direct match
    author_abbreviations = {author_abbreviation for author_abbreviation in author_abbreviations if author_abbreviation not in [match.abbreviation for match in direct_matches]}

    if len(author_abbreviations) == 0:
        return result

    fuzzy_matches = find_fuzzy_matches(all_authors, author_abbreviations)
    result.extend(fuzzy_matches)

    # remove abbreviations that have a fuzzy match
    author_abbreviations = {author_abbreviation for author_abbreviation in author_abbreviations if
                            author_abbreviation not in [match.abbreviation for match in fuzzy_matches]}

    # add remaining abbreviations with author equals None
    result.extend([AuthorRow(None, abbreviation, None, MatchingType.NO_MATCH) for abbreviation in author_abbreviations])

    return result


def find_fuzzy_matches(all_authors, author_abbreviations) -> list[AuthorRow]:
    # fuzzy matches follow the conditions:
    # 1. all abbreviations chars are contained in the author name
    # 2. the abbreviation chars are in the correct order (note there are exceptions e.g. "Nils Inker" with abbreviation "in" for "Inker" would not be found)
    # further there are conditions that higher the certainty of the match:
    # 3. the abbreviation chars match the first characters of the author's name parts (e.g. first name, middle name...)
    # 4. there is one abbreviation char that matches the first char of the last name
    # 4.1 that char is not the first char of the abbreviation

    fuzzy_matches = []

    for author_abbreviation in author_abbreviations:
        matches = []

        for author, frequency_and_abbreviation in all_authors.items():
            full_name_split = re.split(r' |-', author)
            first_name = full_name_split[0]
            last_name = full_name_split[-1]
            certainty = 0

            if len(full_name_split) < 2:
                # author's name is likely not a real name
                continue

            if are_necessary_conditions_fullfilled(author, author_abbreviation) is False:
                continue

            certainty = calculate_fuzzy_certainty(author_abbreviation, certainty, first_name, full_name_split, last_name)

            matches.append(
                {'author': author, 'frequency': frequency_and_abbreviation['frequency'], 'certainty': certainty})

        if len(matches) == 0:
            continue

        add_frequency_based_certainty_for_fuzzy_matches(matches)

        matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)
        fuzzy_matches.append(AuthorRow(matches[0]['author'], author_abbreviation, round(matches[0]['certainty'], 3), MatchingType.FUZZY_MATCH))

    return fuzzy_matches


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


def calculate_fuzzy_certainty(author_abbreviation, certainty, first_name, full_name_split, last_name):
    # conditions that increase certainty
    # add 0.2 certainty if for each split in full_name_split there is a char in the abbreviation and it is matching the index
    if len(author_abbreviation) == len(full_name_split):
        for idx, split in enumerate(full_name_split):
            if author_abbreviation[idx] == split[0]:
                certainty += 0.3
    else:
        if author_abbreviation[0] == first_name[0]:
            certainty += 0.3

        if author_abbreviation[-1] == last_name[0]:
            certainty += 0.3

        elif any([char == last_name[0] for char in author_abbreviation]):
            certainty += 0.1
            if any([char == last_name[0] for char in author_abbreviation[1:]]):
                # if it is not the first character
                certainty += 0.1

    return certainty


def are_necessary_conditions_fullfilled(author, author_abbreviation):
    if all([char in author for char in author_abbreviation]) is False:
        return False

    if ordered_abbreviation_chars_match_name(author, author_abbreviation) is False:
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


def find_direct_matches(all_authors, author_abbreviations) -> list[AuthorRow]:
    direct_matches: list[AuthorRow] = []

    for author_abbreviation in author_abbreviations:
        matches: list[dict] = []
        for author, frequency_and_abbreviation in all_authors.items():
            if author_abbreviation == frequency_and_abbreviation['naive_abbreviation']:
                matches.append(
                    {'author': author, 'frequency': frequency_and_abbreviation['frequency'], 'certainty': None})

        # assign direct matches the author with the highest frequency
        # assign base certainty of 0.7 for being a direct match
        # adds up possible 0.2 certainty
        # assigns 0.1 certainty if all authors have the same frequency
        if len(matches) > 0:
            add_frequency_based_certainty_for_direct_matches(matches)

            matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)
            direct_matches.append(AuthorRow(matches[0]['author'], author_abbreviation, round(matches[0]['certainty'], 3), MatchingType.DIRECT_MATCH))

    return direct_matches

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


def prepare_all_authors_dict(all_authors_with_frequency):
    for author, frequency in all_authors_with_frequency.items():
        author_abbreviation = ''.join([first_char[0] for first_char in re.split(r' |-', author) if first_char != ''])
        all_authors_with_frequency[author] = {'frequency': frequency, 'naive_abbreviation': author_abbreviation}


def get_abbreviations(focused_article):
    author_abbreviations = set()
    for idx, author in enumerate(focused_article['author_array']):
        if focused_article['author_is_abbreviation'][idx]:
            author_abbreviations.add(author.lower().replace('.', ''))

    return author_abbreviations


def add_full_names(focused_article) -> Tuple[list[AuthorRow], list[bool], list[dict]]:
    full_names = [AuthorRow(author, None, None, MatchingType.IS_FULL_NAME) for author, is_abbreviated in zip(focused_article['author_array'], focused_article['author_is_abbreviation']) if is_abbreviated is False]
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
            matches.append(AuthorRow(author, author, 1, MatchingType.ORGANIZATION_MATCH))
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


def get_article_window(cur, focused_article, months=6):
    article_date = focused_article['published_at']
    article_date = datetime.strptime(article_date, '%Y-%m-%dT%H:%M:%S%z')
    lower_date_limit = (article_date - relativedelta(months=months)).isoformat()
    upper_date_limit = (article_date + relativedelta(months=months)).isoformat()

    cur.execute(
        'select id, author_array, author_is_abbreviation, published_at from articles where organization == "lvz" and published_at >= ? and published_at <= ? order by published_at asc', (lower_date_limit, upper_date_limit))
    fetched_articles = cur.fetchall()
    article_window = [{'id': article[0], 'author_array': json.loads(article[1]), 'author_is_abbreviation': json.loads(article[2]), 'published_at': article[3]} for article in fetched_articles]

    return article_window



if __name__ == '__main__':
    main()