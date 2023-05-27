import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import tqdm
import re

# this scripts tries to connect the author to their abbreviation
# from an abbreviation it attempts to find an author name similar to the abbreviation in a predefined time window
# we know that the LVZ does assign abbreviations based on the first letter of the first name and the last name
# but still we first test for this case
# if it does not yield any results we test if the abbreviation characters are contained in the authors name
# in both cases we accept the match if it is unique
# the script then adds the author and abbreviation to the author table

organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn']

def main():
    con = sqlite3.connect('../data/articles_with_basic_information_improved_author_recognition.db')
    cur = con.cursor()
    months = 6
    batch_size = 100
    article_count = 201094 # select count(*) + 1 from articles where organization = 'lvz'
    all_abbreviation_to_author_mapping = []
    current_abbreviation_to_author_mapping = []

    oldest_article = get_oldest_article(cur)
    window_articles = get_article_window(cur, oldest_article, months=months)

    focused_article = oldest_article

    for i in tqdm.tqdm(range(article_count)):
        window_articles_authors_with_frequency = get_authors_with_frequency(window_articles)

        matches = search_for_full_name(focused_article, window_articles_authors_with_frequency)
        # check for each element in matches if the combination of author and abbreviation is not already in current_abbreviation_to_author_mapping
        matches = [match for match in matches if not any(abbreviation_to_author['author'] == match['author'] and abbreviation_to_author['abbreviation'] == match['abbreviation'] for abbreviation_to_author in all_abbreviation_to_author_mapping)]
        all_abbreviation_to_author_mapping.extend(matches)
        current_abbreviation_to_author_mapping.extend(matches)

        focused_article = get_succeeding_focused_article(window_articles, focused_article)
        if focused_article is None:
            break

        window_articles = get_article_window(cur, focused_article, months=months)

        if i > 0 and i % batch_size == 0:
            for abbreviation_to_author in current_abbreviation_to_author_mapping:
                updated_at = datetime.utcnow().isoformat()
                cur.execute('insert into authors values (?,?,?,?,?,?)',
                            (None, abbreviation_to_author['author'], abbreviation_to_author['abbreviation'], round(abbreviation_to_author['certainty'], 3), updated_at, updated_at))
            con.commit()
            current_abbreviation_to_author_mapping = []




def get_authors_with_frequency(window_articles):
    window_articles_authors_with_frequency = {}
    for article in window_articles:
        if article['author_array'] is None:
            continue

        authors = []
        for idx, author in enumerate(eval(article['author_array'])):
            if eval(article['author_is_abbreviation'])[idx] is False:
                authors.append(author.lower())

        for author in authors:
            if author not in window_articles_authors_with_frequency.keys():
                window_articles_authors_with_frequency[author] = 1
            else:
                window_articles_authors_with_frequency[author] += 1
    return window_articles_authors_with_frequency


def search_for_full_name(focused_article, all_authors_with_frequency: dict):
    direct_matches = []

    if focused_article['author_is_abbreviation'] is None:
        return None

    if not any(eval(focused_article['author_is_abbreviation'])):
        return None

    if any([author.lower() in organizations for author in eval(focused_article['author_array'])]):
        author_array = eval(focused_article['author_array'])
        remaining_authors = []
        for author in author_array:
            if author.lower() in organizations:
                direct_matches.append({'abbreviation': author, 'author': author, 'certainty': 1})
            else:
                remaining_authors.append(author)

        if len(remaining_authors) == 0:
            return direct_matches
        else:
            focused_article['author_array'] = str(remaining_authors)


    article_author_abbreviations = []
    for idx, author in enumerate(eval(focused_article['author_array'])):
        if eval(focused_article['author_is_abbreviation'])[idx]:
            article_author_abbreviations.append(author.lower().replace('.', ''))

    for author, frequency in all_authors_with_frequency.items():
        author_abbreviation = ''.join([first_char[0] for first_char in author.split(' ')])
        all_authors_with_frequency[author] = {'frequency': frequency, 'abbreviation': author_abbreviation}



    for author_abbreviation in article_author_abbreviations:
        matches = []
        for author, frequency_and_abbreviation in all_authors_with_frequency.items():
            if author_abbreviation == frequency_and_abbreviation['abbreviation']:
                matches.append({'author': author, 'frequency': frequency_and_abbreviation['frequency'], 'certainty': None})

        # assign direct matches the author with the highest frequency
        # assign base certainty of 0.7 for being a direct match
        # adds up possible 0.2 certainty
        # assigns 0.1 certainty if all authors have the same frequency
        if len(matches) > 0:
            # calculate certainty based on normalized frequency
            frequency_values = [match['frequency'] for match in matches]
            min_frequency = min(frequency_values)
            max_frequency = max(frequency_values)
            if max_frequency == min_frequency: # avoid division by zero
                if len(matches) == 1:
                    matches[0]['certainty'] = 0.9
                else:
                    for idx, match in enumerate(matches):
                        matches[idx]['certainty'] += 0.1
            else:
                # update certainty based on normalized frequency
                for idx, match in enumerate(matches):
                    matches[idx]['certainty'] = 0.7
                    matches[idx]['certainty'] += 0.2 * (match['frequency'] - min_frequency) / (max_frequency - min_frequency)
                    # multiplies a penalty term for small frequencies: min(0.2 *  frequency,1)
                    #matches[idx]['certainty'] = min(0.2 * matches[idx]['frequency'], 1) * matches[idx]['certainty']

            matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)
            direct_matches.append({'abbreviation': author_abbreviation, 'author': matches[0]['author'], 'certainty': matches[0]['certainty']})

    if len(direct_matches) > 0:
        return direct_matches

    # fuzzy matches follow the conditions:
    # 1. all abbreviations chars are contained in the author name
    # 2. the abbreviation chars are in the correct order (note there are exceptions e.g. "Nils Inker" with abbreviation "in" for "Inker" would not be found)
    # further there are conditions that higher the certainty of the match:
    # 3. the first char has to match the first char of the author first name
    # 4. one char (not the first one) has to match the first char of the author last name

    fuzzy_matches = []
    for author_abbreviation in article_author_abbreviations:
        matches = []
        for author, frequency_and_abbreviation in all_authors_with_frequency.items():
            full_name_split = re.split(r' |-', author)
            first_name = full_name_split[0]
            last_name = full_name_split[-1]
            certainty = 0

            # necessary condition
            if all([char in author for char in author_abbreviation]) is False:
                continue
            if all([author_abbreviation.index(char) <= author.index(char) for char in author_abbreviation]) is False: # condition 2
                continue

            indices = [author.index(char) for char in author_abbreviation] # condition 2
            if all([indices[idx] <= indices[idx + 1] for idx in range(len(indices) - 1)]) is False:
                continue

            # conditions that increase certainty
            # add 0.2 certainty if for each split in full_name_split there is a char in the abbreviation and it is matching the index
            if len(author_abbreviation) == len(full_name_split):
                for idx, split in enumerate(full_name_split):
                    if author_abbreviation[idx] == split[0]:
                        certainty += 0.2
            else:
                if author_abbreviation[0] == first_name[0]:
                    certainty += 0.2

                if author_abbreviation[-1] == last_name[0]:
                    certainty += 0.2

                elif any([char == last_name[0] for char in author_abbreviation]):
                    certainty += 0.1
                    if any([char == last_name[0] for char in author_abbreviation[1:]]):
                        # if it is not the first character
                        certainty += 0.1

            matches.append({'author': author, 'frequency': frequency_and_abbreviation['frequency'], 'certainty': certainty})

        if len(matches) == 0:
            continue

        frequency_values = [match['frequency'] for match in matches]
        min_frequency = min(frequency_values)
        max_frequency = max(frequency_values)

        if min_frequency == max_frequency: # avoid division by zero
            for idx, match in enumerate(matches):
                matches[idx]['certainty'] += 0.3
        else:
            # update certainty based on normalized frequency
            for idx, match in enumerate(matches):
                matches[idx]['certainty'] += 0.3 * (match['frequency'] - min_frequency) / (max_frequency - min_frequency)
                # multiplies a penalty term for small frequencies: min(0.05 *  frequency,1)
                #matches[idx]['certainty'] = min(0.2 * matches[idx]['frequency'], 1) * matches[idx]['certainty']

        matches = sorted(matches, key=lambda k: k['certainty'], reverse=True)
        fuzzy_matches.append({'abbreviation': author_abbreviation, 'author': matches[0]['author'], 'certainty': matches[0]['certainty']})

    return fuzzy_matches




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
        'select url, author_array, author_is_abbreviation, published_at from articles where organization == "lvz" and published_at >= "' + lower_date_limit + '" and published_at <= "' + upper_date_limit + '" order by published_at asc')
    fetched_articles = cur.fetchall()
    article_window = [{'url': article[0], 'author_array': article[1], 'author_is_abbreviation': article[2], 'published_at': article[3]} for article in fetched_articles]
    return article_window


def get_oldest_article(cur):
    cur.execute(
        'select url, author_array, author_is_abbreviation, published_at from articles where organization == "lvz" and author_is_abbreviation is not null and author_is_abbreviation like "%True%" order by published_at asc limit 1')
    next_fetched_article = cur.fetchone()
    next_article = {'url': next_fetched_article[0], 'author_array': next_fetched_article[1],
                    'author_is_abbreviation': next_fetched_article[2], 'published_at': next_fetched_article[3]}
    return next_article


if __name__ == '__main__':
    main()