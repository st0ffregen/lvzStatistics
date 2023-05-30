import sqlite3
import json
import re
import sys
import traceback
from datetime import datetime
import spacy
import regex
import tqdm
from retrieve_data.data_sanitization.utils.logger import Logger

nlp = spacy.load('de_core_news_sm')

redaktionsAuthorList = ['Redaktion.', 'red.']
punctuation_blocklist = ['»', '-', '“', '*', '"', '“']
punctuation_blocklist_keep_whitespace = [' -', '  ', '“ ', ' „', '" ', '“ ']
inner_punctuation_blocklist = [u'\xa0', u'\xc2']
organizations = ['lvz', 'dpa', 'dnn', 'haz', 'maz', 'rnd', 'np', 'oz', 'ln', 'kn', 'gtet', 'paz', 'wazaz', 'sid', 'op', 'sn', 'mazonline']
re_name = r'((?:[\p{L}]+|\p{L}\.)(?:\s|-)(?:[\p{L}]+|\p{L}\.)(?:(?:\s|-)[\p{L}]*|\p{L}\.)?)'

success = 0
failed = 0
notLVZ = 0


class AuthorError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'AuthorError, {0} '.format(self.message)
        else:
            return 'AuthorError has been raised'


class Article:
    def __init__(self, url, context_tag, organization, author_array, author_is_abbreviation_array, genre,
                 article_namespace_array,
                 published_at, modified_at, is_free, headline, text):
        self.url = url
        self.context_tag = context_tag
        self.organization = organization
        self.author_array = author_array
        self.author_is_abbreviation_array = author_is_abbreviation_array
        self.genre = genre
        self.article_namespace_array = article_namespace_array
        self.published_at = published_at
        self.modified_at = modified_at
        self.is_free = is_free
        self.headline = headline
        self.text = text


def loadDownloadedData(databaseName, limit, offset):
    con = sqlite3.connect(databaseName)
    cur = con.cursor()
    cur.execute('select url, contextTag from articles order by id desc limit ' + str(limit) + ' offset ' + str(offset))
    entries = cur.fetchall()
    articles = []
    for row in entries:
        articles.append({'url': row[0], 'contextTag': row[1]})

    return articles


def getArticleNamespace(url):
    matches = re.findall('(.*\/){1,7}(?=.{4,})', url)

    if len(matches) != 1:
        raise Exception(f'two many/few matches for {url}: {matches}')

    articleNamespace = matches[0].split('/')
    return [i for i in articleNamespace if i]  # remove empty strings


def getData(json, key):
    try:
        return json[key]
    except KeyError:
        return None


def remove_outer_unwanted_punctuation(string):
    string = string.strip()

    if string == '':
        return string

    for punctuation in punctuation_blocklist:
        if string[0] == punctuation:
            string = string[1:]
        if string[-1] == punctuation:
            string = string[:-1]

    return string.strip()

def remove_inner_unwanted_punctuation(string):
    string = string.strip()

    if string == '':
        return string

    for punctuation in inner_punctuation_blocklist:
        string = string.replace(punctuation, '')

    for punctuation in punctuation_blocklist_keep_whitespace:
        string = string.replace(punctuation, ' ')

    return string.strip()

def get_author(article_text):
    authors, is_abbreviations = getAuthorString(article_text)

    if authors is None:
        return None, None

    authors, is_abbreviation = remove_empty_strings(authors, is_abbreviations)
    authors, is_abbreviation = remove_duplicates(authors, is_abbreviation)

    return authors, is_abbreviation

def remove_empty_strings(authors, is_abbreviation):
    for i in range(len(authors)):
        if authors[i] == '':
            authors.pop(i)
            is_abbreviation.pop(i)

    return authors, is_abbreviation

def remove_duplicates(authors, is_abbreviation):
    if len(authors) != len(set(authors)):
        authors, is_abbreviation = [list(el) for el in zip(*set(zip(authors, is_abbreviation)))]

    return authors, is_abbreviation

def handle_special_cases(article_text):
    # Case 5: Editorial abbreviation
    match = regex.search(r'\.\s+(Redaktion|red)\.?$', article_text, flags=re.UNICODE)
    if match:
        return ["LVZ"], [True]

    # Case 9: organization abbreviation
    match = regex.search(rf'von\s({"|".join(organizations)})$', article_text.lower(), flags=re.UNICODE)
    if match:
        return [match.group(1)], [True]

    return [], []

def remove_special_cases_from_text(article_text):
    authors = []
    is_abbreviations = []

    # Case 8: co-author
    match = regex.search(r'\((mit .*)\)$', article_text, flags=re.UNICODE)
    if match:
        co_author = match.group(1).replace('mit ', '')
        authors.append(co_author)
        is_abbreviation = check_if_is_abbreviation(co_author)
        if is_abbreviation is None:
            return None, None, None
        is_abbreviations.append(is_abbreviation)

        article_text = article_text.replace('(' + match.group(1) + ')', '')
        article_text = article_text.strip()

    article_text = replace_keywords(article_text, r'.*\s(Interview:)\s.*$')
    article_text = replace_keywords(article_text, r'.*\s(\d{1,2}\.\d{1,2}\.\d{2,4})\s.*$')
    article_text = replace_keywords(article_text, r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    article_text = replace_keywords(article_text, r'\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]{2,}(?:\.[a-zA-Z]{2,}){1,}(?:\/[a-zA-Z0-9-]+)*(?:\.html)?')

    return article_text, authors, is_abbreviations


def replace_keywords(article_text, reg):
    match = regex.search(reg, article_text, flags=re.UNICODE)
    if match:
        article_text = article_text.replace(match.group(1) if len(match.groups()) > 0 else match.captures()[0], 'Von') # TODO: groups und capture unterschied checken
    return article_text


def getAuthorString(article_text):
    article_text = article_text[-100:]
    article_text = remove_obvious_noise(article_text)
    article_text = remove_outer_unwanted_punctuation(article_text)
    article_text = remove_inner_unwanted_punctuation(article_text)

    authors = []
    is_abbreviations = []

    # regex vars
    # it can contain up to three words, separated by a space, including unicode characters, hyphens (e.g. "Elke Hans-Peter") and dots (e.g. "Hermann M. Schröder")
    #re_abbr = r'([\w\.?]+)(?:\s|\/|,)?'

    authors, is_abbreviations = handle_special_cases(article_text)

    if len(authors) > 0:
        return authors, is_abbreviations

    article_text, authors, is_abbreviations = remove_special_cases_from_text(article_text)

    if article_text is None:
        return None, None


    # Case 3.1: Single abbreviation with "Von" prefix, separated by a period
    match = regex.search(r'Von\s+(\w\.\s?\w\.)$', article_text, flags=re.UNICODE)
    if match:
        authors.append(match.group(1).replace(' ', '').replace('.', ''))
        is_abbreviations.append(True)
        return authors, is_abbreviations

    # Case 4.1/7: Mix of full names and or multiple abbreviations with "Von" prefix, separated by a slash
    match = regex.search(r'Von (.*\/.*)+$', article_text, flags=re.UNICODE)
    if match:
        splits = re.split(r'\s*/\s*', match.group(1))

        # check with spacy if names are persons but only if white spaces are included
        for split in splits:
            authors.append(remove_outer_unwanted_punctuation(split))
            if ' ' in split:
                is_person = nlp(split)[0].ent_type_ == 'PER'
                is_abbreviations.append(is_person is False)
            elif len(split) < 2 or len(split) > 6:
                return None, None
            elif '.' in split: # similar to case 3.1
                authors[-1] = authors[-1].replace('.', '')
                is_abbreviations.append(True)
            elif split.isupper(): # very likely that it is an abbreviation
                is_abbreviations.append(True)
            else:
                is_abbreviations.append(True)

        return authors, is_abbreviations

    # Case 4.1/7???: Mix of full names and or multiple abbreviations without "Von" prefix, separated by a slash
    match = regex.search(rf'(?:\.|:)\s(?!Von\s)((?:-?\w{{2,6}}|{re_name})\/(?:-?\w{{2,6}}|{re_name}))+$', article_text, flags=re.UNICODE)
    if match:
        splits = re.split(r'\s*/\s*', match.group(1))

        # check with spacy if names are persons but only if white spaces are included
        for split in splits:
            authors.append(remove_outer_unwanted_punctuation(split))
            if ' ' in split:
                entities = nlp(split).ents
                is_person = all(ent.label_ == 'PER' for ent in entities) and len(entities) > 0

                if is_person is False:
                    return None, None
                is_abbreviations.append(is_person is False)
            elif len(split) < 2 or len(split) > 6:
                return None, None
            elif '.' in split: # similar to case 3.1
                authors[-1] = authors[-1].replace('.', '')
                is_abbreviations.append(True)
            elif split.isupper(): # very likely that it is an abbreviation
                is_abbreviations.append(True)
            else:
                is_abbreviations.append(True)

        return authors, is_abbreviations


    # Case 6.: No author given, texts ends with a period or colon
    match = regex.search(r'(?:\.|:)$', article_text)
    if match:
        authors.append("LVZ")
        is_abbreviations.append(True)
        return authors, is_abbreviations

    # Case 3.2: Single abbreviation without "Von" prefix
    if 'Von ' not in article_text:
        match = regex.search(r'(?:\.|:)\s+(-?\w{2,6})$', article_text, flags=re.UNICODE)
        if match:
            authors.append(match.group(1))
            is_abbreviations.append(True)
            return authors, is_abbreviations

    # Case 3.3: Single abbreviation written together with "Von" prefix
    match = regex.search(r'Von\s+(-?\w{2,6})$', article_text, flags=re.UNICODE)
    if match:
        authors.append(match.group(1))
        is_abbreviations.append(True)
        return authors, is_abbreviations


    # Case 2.1: Multiple full names with "Von" prefix
    match = regex.search(rf'Von\s+{re_name}\s+und\s+{re_name}$', article_text, flags=re.UNICODE)
    if match:
        authors.extend([match.group(1), match.group(2)])
        is_abbreviations.extend([False, False])
        return authors, is_abbreviations

    # Case 2.5: Multiple full names with "Von" prefix, separated by commas and "und"
    if 'Von' in article_text and ',' in article_text.split('Von ')[1] and 'und' in article_text.split('Von ')[1]: # check if there is a comma and an "und" after "Von"
        match = regex.search(rf'Von\s+({re_name},?\s?)+\s+und\s+{re_name}$', article_text, flags=re.UNICODE)
        if match:
            names = re.split(', | und ', match.captures()[0].replace('Von ', ''))
            authors.extend(names)
            is_abbreviations.extend([False] * len(names))
            return authors, is_abbreviations

    # Case 2.6: Multiple full names with "Von" prefix, separated by commas
    if 'Von' in article_text and ',' in article_text.split('Von ')[1]: # check if there is at least one comma after "Von ..."
        match = regex.search(rf'Von\s+(?:{re_name},?\s?)+$', article_text, flags=re.UNICODE)
        if match:
            names = re.split(r'\s*,\s*', match.captures()[0].replace('Von ', ''))
            authors.extend(names)
            is_abbreviations.extend([False] * len(names))
            return authors, is_abbreviations

    # Case 4.2: Mix of full names and or multiple abbreviations with "Von" prefix, separated by a comma
    match = regex.search(r'Von (.*,.*)+$', article_text, flags=re.UNICODE)
    if match:
        splits = re.split(r'\s*,\s*', match.group(1))

        # check with spacy if names are persons but only if white spaces are included
        for split in splits:
            split = split.strip()
            authors.append(split)
            is_abbreviation = check_if_is_abbreviation(split)
            if is_abbreviation is None:
                return None, None
            is_abbreviations.append(is_abbreviation)

        return authors, is_abbreviations

    # Case 2.4: Multiple full names with "Von" prefix, separated each by a slash
    if 'Von' in article_text and '/' in article_text.split('Von ')[1]: # check if there is a slash after "Von"
        match = regex.search(rf'Von\s+(?:{re_name}/?\s?)+$', article_text, flags=re.UNICODE)
        if match:
            names = re.split(r'\s*/\s*', match.captures()[0].replace('Von ', ''))
            # check with spacy that names are persons
            for name in names:
                if nlp(name)[0].ent_type_ != 'PER':
                    return None, None

            authors.extend(names)
            is_abbreviations.extend([False] * len(names))
            return authors, is_abbreviations

    # Case 2.2: Multiple full names without "Von" prefix, separated from text by a period or colon
    match = regex.search(rf'(?:\.|:)\s+{re_name}\s+und\s+{re_name}$', article_text, flags=re.UNICODE)
    if match:
        authors.extend([match.group(1), match.group(2)])
        is_abbreviations.extend([False, False])
        return authors, is_abbreviations

    # Case 4.3: Multiple abbreviations names without "Von" prefix, separated from text by a period or colon
    if '/' in article_text and 'Von ' not in article_text:
        match = regex.search(r'(?:\.|:)\s+(-?\w{2,6}\/?)+$', article_text, flags=re.UNICODE)
        if match:
            capture = match.captures()[0]
            capture = capture[1:].strip()
            abbreviations = re.split(r'\s*/\s*', capture)
            authors.extend(abbreviations)
            is_abbreviations.extend([True] * len(abbreviations))
            return authors, is_abbreviations

    # Case 2.3: Multiple full names without "Von" prefix, missing period or colon
    match = regex.search(rf'{re_name}\s+und\s+{re_name}$', article_text, flags=re.UNICODE)
    if match:
        names = []
        for group in match.groups():

            entities = nlp(group).ents
            is_person = all(ent.label_ == 'PER' for ent in entities) and len(entities) > 0
            if is_person:
                names.append(entities[0].lemma_)

        if names:
            authors.extend(names)
            is_abbreviations.extend([False] * len(names))
            return authors, is_abbreviations

    # Case 1.4: Single full name with "Von" prefix, name followed by " (Text)"
    if 'Von ' in article_text and ' (Text)' in article_text:
        match = regex.search(rf'Von\s+{re_name}\s+\(Text\)', article_text, flags=re.UNICODE)
        if match:
            authors.append(match.group(1))
            is_abbreviations.append(False)
            return authors, is_abbreviations

    # Case 1.1: Single full name with "Von" prefix
    match = regex.search(rf'Von\s+{re_name}$', article_text, flags=re.UNICODE)
    if match:
        authors.append(match.group(1))
        is_abbreviations.append(False)
        return authors, is_abbreviations


    # Case 1.2: Single full name without "Von" prefix, separated from the text by a period or colon
    match = regex.search(rf'(?:\.|:)\s(?!Von\s){re_name}$', article_text, flags=re.UNICODE)
    if match:
        authors.append(match.group(1))
        is_abbreviations.append(False)
        return authors, is_abbreviations

    # General case name without "Von" prefix, missing period or colon
    # in this case check if the last words are a name
    # include up to two name parts given that no middle names exists
    last_elements = [' '.join(re.split(r' |/', article_text)[-4:-2]), ' '.join(re.split(r' |/', article_text)[-2:])]
    for element in last_elements:
        entities = nlp(element).ents
        is_person = all(ent.label_ == 'PER' for ent in entities) and len(entities) > 0
        # check if it matches regex re_name
        if element != '' and is_person and regex.match(rf'^{re_name}$', element):
            authors.append(element)
            is_abbreviations.append(False)
    if authors:
        return authors, is_abbreviations

    return None, None

def remove_obvious_noise(string):
    #string = remove_email_addresses(string)
    #string = remove_hyper_links(string)
    return string

def remove_email_addresses(string):
    # recognize hyperlinks
    hyper_links = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', string)
    for link in hyper_links:
        string = string.replace(link, '')
    return string.strip()

def remove_hyper_links(string):
    # recognize hyperlinks
    hyper_links = re.findall(r'\b(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]{2,}(?:\.[a-zA-Z]{2,}){1,}(?:\/[a-zA-Z0-9-]+)*(?:\.html)?', string)
    for link in hyper_links:
        string = string.replace(link, '')
    return string.strip()

def check_if_is_abbreviation(string):
    if ' ' in string:
        is_person = nlp(string)[0].ent_type_ == 'PER'
        return is_person is False
    elif len(string) < 2 or len(string) > 6:
        return None
    elif '.' in string:  # similar to case 3.1
        return True
    elif string.isupper():  # very likely that it is an abbreviation
        return True
    else:
        return True


def save_to_database(articles, logger):
    con = sqlite3.connect('../data/articles_with_author_mapping.db')
    cur = con.cursor()
    global failed


    for article in articles:
        if article is not None:
            try:
                updated_at = datetime.utcnow().isoformat()

                article.author_array = json.dumps(article.author_array)
                article.author_is_abbreviation_array = json.dumps(article.author_is_abbreviation_array)
                article.article_namespace_array = json.dumps(article.article_namespace_array)

                cur.execute('insert into articles values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (None, article.url, article.context_tag, article.organization, article.author_array,
                             article.author_is_abbreviation_array,
                             article.genre, article.article_namespace_array, article.published_at, article.modified_at,
                             article.is_free, article.headline, article.text, updated_at, updated_at))

            except sqlite3.IntegrityError as e:
                logger.warning(f'error for article {article.url} : {e}')
                failed += 1
    con.commit()



def aggregateData(article, logger):
    global success
    global failed
    global notLVZ

    try:
        jsonContent = json.loads(article['contextTag'])

        organization = jsonContent['author']['name'].lower()

        if organization != 'lvz':
            notLVZ += 1

        articleNamespace = getArticleNamespace(article['url'])
        genre = getData(jsonContent, 'genre')
        datePublished = getData(jsonContent, 'datePublished')
        dateModified = getData(jsonContent, 'dateModified')
        headline = getData(jsonContent, 'headline')
        text = getData(jsonContent, 'articleBody')
        isFree = getData(jsonContent, 'isAccessibleForFree')
        if text is not None and organization == 'lvz':
            authorArray, author_is_abbreviation_array = get_author(text)
        else:
            authorArray, author_is_abbreviation_array = None, None

        article_object = Article(article['url'], article['contextTag'], organization, authorArray, author_is_abbreviation_array,
                                 genre, articleNamespace, datePublished, dateModified, isFree, headline, text)

        logger.info(f'Successfully aggregated data for {article["url"]}')
        success += 1
        return article_object

    except Exception as e:
        logger.warning(f'Something went wrong for {article["url"]}: {e}')
        logger.warning(traceback.format_exception(*sys.exc_info()))
        failed += 1
        return


def main():
    logger = Logger('../logs/', 'retrieval', 'INFO').get_logger()

    for l in tqdm.tqdm(range(0, 53)):
        offset = l * 7000
        limit = 7000
        logger.info('start run from ' + str(offset) + ' to ' + str(offset + limit))
        articles = loadDownloadedData('../data/all_downloaded_articles.db', limit, offset)
        articles_for_db = []
        for article in articles:
            articles_for_db.append(aggregateData(article, logger))

        save_to_database(articles_for_db, logger)


    print('success: ' + str(success))
    print('failed: ' + str(failed))
    print('notLVZ: ' + str(notLVZ))


if __name__ == '__main__':
    main()
