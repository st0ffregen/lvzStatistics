import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tqdm
import re
import math

# this scripts tries to connect the author to their abbreviation
# from an abbreviation it attempts to find an author name similar to the abbreviation in a predefined time window
# we know that the LVZ does assign abbreviations based on the first letter of the first name and the last name
# but still we first test for this case
# if it does not yield any results we test if the abbreviation characters are contained in the authors name
# in both cases we accept the match if it is unique
# the script then adds the author and abbreviation to the author table

organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline']
batch_size = 100  # TODO: check again, if this could be a problem when abbreviated articles are sparse. plot graph displaying the number of articles with abbreviations over time


def main():
    match_author_to_abbreviation()


# TODO 29.05: tests schreiben für die klasse und dann nochmal alles durchlaufen lassen
# dann full name authors in die db nachtragen und dann mit dem finalen mapping beginnen
def match_author_to_abbreviation():
    con, cur = get_db_connection()
    months = 6
    article_count = get_article_count(cur)
    current_abbreviation_to_author_mapping = []

    oldest_article = get_oldest_article(cur)
    window_articles = get_article_window(cur, oldest_article, months=months)
    focused_article = oldest_article

    for i in tqdm.tqdm(range(article_count)):
        window_articles_authors_with_frequency = get_authors_with_frequency(window_articles)

        matches = search_for_full_name(focused_article, window_articles_authors_with_frequency)

        if matches is None: # focused article has no abbreviations
            focused_article = get_succeeding_focused_article(window_articles, focused_article)
            continue

        add_article_id(focused_article, matches)
        current_abbreviation_to_author_mapping.extend(matches)

        focused_article = get_succeeding_focused_article(window_articles, focused_article)

        if focused_article is None:
            save_matches_to_db(con, cur, current_abbreviation_to_author_mapping)
            break

        if i > 0 and i % batch_size == 0:
            save_matches_to_db(con, cur, current_abbreviation_to_author_mapping)
            current_abbreviation_to_author_mapping = []

        window_articles = get_article_window(cur, focused_article, months=months)


def save_matches_to_db(con, cur, current_abbreviation_to_author_mapping):
    for abbreviation_to_author in current_abbreviation_to_author_mapping:
        updated_at = datetime.utcnow().isoformat()
        cur.execute('insert into authors values (?,?,?,?,?,?)',
                    (None, abbreviation_to_author['author'], abbreviation_to_author['abbreviation'],
                     round(abbreviation_to_author['certainty'], 3), updated_at, updated_at))
        cur.execute('insert into article_authors values (?,?,?,?,?)',
                    (None, abbreviation_to_author['article_id'], cur.lastrowid, updated_at, updated_at))
    con.commit()


def add_article_id(focused_article, matches):
    # add focused_article id to every element in matches dict
    for match in matches:
        match['article_id'] = focused_article['id']


def get_article_count(cur):
    article_count = cur.execute('select count(*) from articles where organization = "lvz"').fetchone()[0] + 1
    return article_count


def get_db_connection():
    con = sqlite3.connect('../data/articles_with_author_mapping.db')
    cur = con.cursor()
    return con, cur


def get_authors_with_frequency(window_articles):
    authors_with_frequency = {}
    for article in window_articles:
        if article['author_array'] is None:
            continue

        authors = []
        for idx, author in enumerate(eval(article['author_array'])):
            if eval(article['author_is_abbreviation'])[idx] is False:
                authors.append(author.lower().strip())

        for author in authors:
            if author not in authors_with_frequency.keys():
                authors_with_frequency[author] = 1
            else:
                authors_with_frequency[author] += 1

    return authors_with_frequency


def at_least_one_author_is_abbreviated(focused_article):
    return any(eval(focused_article['author_is_abbreviation']))


def all_abbreviations_have_a_match(author_abbreviations, matches):
    return all([author_abbreviation in [match['abbreviation'] for match in matches] for
         author_abbreviation in author_abbreviations])


def at_least_one_author_is_an_organization(focused_article):
    return any([author.lower() in organizations for author in eval(focused_article['author_array'])])


def search_for_full_name(focused_article, all_authors):
    focused_article = focused_article.copy()
    all_authors = all_authors.copy()
    direct_matches = []

    if focused_article['author_is_abbreviation'] is None:
        return None

    if at_least_one_author_is_abbreviated(focused_article) is False:
        return None

    if at_least_one_author_is_an_organization(focused_article):
        remaining_author_is_abbreviation, remaining_authors = add_organization_matches(direct_matches, focused_article)

        if len(remaining_authors) == 0:
            return direct_matches
        else:
            focused_article['author_array'] = str(remaining_authors)
            focused_article['author_is_abbreviation'] = str(remaining_author_is_abbreviation)

    author_abbreviations = get_abbreviations(focused_article)

    prepare_all_authors_dict(all_authors)

    find_direct_matches(all_authors, author_abbreviations, direct_matches)

    # remove abbreviations that have a direct match
    author_abbreviations = [author_abbreviation for author_abbreviation in author_abbreviations if author_abbreviation not in [match['abbreviation'] for match in direct_matches]]

    if len(author_abbreviations) == 0:
        return direct_matches

    fuzzy_matches = find_fuzzy_matches(all_authors, author_abbreviations)

    result = direct_matches + fuzzy_matches

    return result


def find_fuzzy_matches(all_authors, author_abbreviations):
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
        fuzzy_matches.append(
            {'abbreviation': author_abbreviation, 'author': matches[0]['author'], 'certainty': round(matches[0]['certainty'], 3)})

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


def find_direct_matches(all_authors, author_abbreviations, direct_matches):
    for author_abbreviation in author_abbreviations:
        matches = []
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
            direct_matches.append({'abbreviation': author_abbreviation, 'author': matches[0]['author'],
                                   'certainty': round(matches[0]['certainty'], 3)})


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
        author_abbreviation = ''.join([first_char[0] for first_char in re.split(r' |-', author)])
        all_authors_with_frequency[author] = {'frequency': frequency, 'naive_abbreviation': author_abbreviation}


def get_abbreviations(focused_article):
    author_abbreviations = []
    for idx, author in enumerate(eval(focused_article['author_array'])):
        if eval(focused_article['author_is_abbreviation'])[idx]:
            author_abbreviations.append(author.lower().replace('.', ''))

    return author_abbreviations


def add_organization_matches(direct_matches, focused_article):
    author_array = eval(focused_article['author_array'])
    remaining_authors = []
    remaining_author_is_abbreviation = []

    for author in author_array:
        if author.lower() in organizations:
            direct_matches.append({'abbreviation': author, 'author': author, 'certainty': 1})
        else:
            remaining_authors.append(author)
            remaining_author_is_abbreviation.append(
                eval(focused_article['author_is_abbreviation'])[author_array.index(author)])

    return remaining_author_is_abbreviation, remaining_authors


def get_succeeding_focused_article(articles_in_window, focused_article):
    # get succeeding article where at least one author is an abbreviation
    focused_article_index = articles_in_window.index(focused_article)
    next_index = focused_article_index + 1

    while True:
        if next_index == len(articles_in_window):
            return None

        next_article = articles_in_window[next_index]

        if next_article['author_is_abbreviation'] is not None and any(eval(next_article['author_is_abbreviation'])):
            return next_article

        next_index += 1


def get_article_window(cur, focused_article, months=6):
    article_date = focused_article['published_at']
    article_date = datetime.strptime(article_date, '%Y-%m-%dT%H:%M:%S%z')
    lower_date_limit = (article_date - relativedelta(months=months)).isoformat()
    upper_date_limit = (article_date + relativedelta(months=months)).isoformat()

    cur.execute(
        'select id, url, author_array, author_is_abbreviation, published_at from articles where organization == "lvz" and published_at >= "' + lower_date_limit + '" and published_at <= "' + upper_date_limit + '" order by published_at asc')
    fetched_articles = cur.fetchall()
    article_window = [{'id': article[0], 'url': article[1], 'author_array': article[2], 'author_is_abbreviation': article[3], 'published_at': article[4]} for article in fetched_articles]
    return article_window


def get_oldest_article(cur):
    cur.execute(
        'select id, url, author_array, author_is_abbreviation, published_at from articles where organization == "lvz" and author_is_abbreviation is not null and author_is_abbreviation like "%True%" order by published_at asc limit 1')
    next_fetched_article = cur.fetchone()
    next_article = {'id': next_fetched_article[0], 'url': next_fetched_article[1], 'author_array': next_fetched_article[2],
                    'author_is_abbreviation': next_fetched_article[3], 'published_at': next_fetched_article[4]}
    return next_article


if __name__ == '__main__':
    main()