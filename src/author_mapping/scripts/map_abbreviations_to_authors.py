import networkx as nx
import pandas as pd
from datetime import datetime
from tqdm import tqdm

from src.author_mapping.scripts import calculate_frequency_score
from src.author_mapping.scripts import calculate_department_score
from src.utils.get_db import get_db_connection
from src.sanitize.scripts.write_unmapped_authors_to_data_base import get_articles


DUMMY_NODE_WEIGHT = 0.8


def map_abbreviations_to_authors(db_file_path):
    print("Start mapping abbreviations to authors")
    print("Compute frequency score")
    authors_frequency_score = calculate_frequency_score.calculate_frequency_score(db_file_path)
    print("Compute department score")
    authors_department_score = calculate_department_score.calculate_department_score(db_file_path)

    # test if authors_frequency_score and authors_department_score have the same name, abbreviation pairs
    frequency_pairs = [(el[0], el[1]) for el in authors_frequency_score[['full_name', 'abbreviation']].values.tolist()]
    department_pairs = [(el[0], el[1]) for el in authors_department_score[['full_name', 'abbreviation']].values.tolist()]
    assert len(set(frequency_pairs) - set(department_pairs)) == 0

    # merge dataframes
    authors = authors_frequency_score.merge(authors_department_score, on=["full_name", "abbreviation"], how="inner")
    n_authors = len(authors)
    print(f"Found {n_authors} authors with both frequency and department score")

    # save self referencing nodes to add them later
    self_referencing_authors = authors[authors["full_name"].str.lower() == authors["abbreviation"].str.lower()]

    # Remove them from authors
    authors = authors[authors["full_name"].str.lower() != authors["abbreviation"].str.lower()]
    print(f"Removed {len(self_referencing_authors)} self referencing nodes")

    authors["score"] = -1 * (authors["department_score_normalized"] + authors["certainty"] + authors["frequency_score_normalized"]) # -1 factor because minimum_weight_full_matching minimizes

    # normalize score
    authors["normalized_score"] = (authors["score"] - authors["score"].min()) / (authors["score"].max() - authors["score"].min())

    graph, full_names_list, abbreviations_list = create_graph(authors)

    assigned_graph = construct_assigned_graph(abbreviations_list, full_names_list, graph)

    # transform graph to dataframe author_mapping with columns name and abbreviation
    author_mapping = pd.DataFrame(columns=["full_name", "abbreviation"], data=assigned_graph.edges)
    author_mapping = author_mapping.astype(str)

    print(f"author_mapping has {author_mapping.shape[0]} rows")

    # remove all abbreviations that contain "dummy" in their name
    author_mapping = author_mapping[~author_mapping["abbreviation"].str.contains("dummy")]

    print(f"after dummy removal: author_mapping has {author_mapping.shape[0]} rows")

    # add self referencing authors again
    author_mapping = pd.concat([author_mapping, self_referencing_authors[["full_name", "abbreviation"]]])
    print(f"after adding self referencing authors: author_mapping has {author_mapping.shape[0]} rows")

    print(f"There are {len(assigned_graph.nodes) - (len(assigned_graph.edges) * 2)} abbreviations that were not matched")
    # print not matched abbreviations
    print(f" The following abbreviations were not matched: {[node for node in assigned_graph.nodes if assigned_graph.degree(node) == 0]}")

    # test if these abbreviations have only one edge in the old graph. If so, we can append them to that author.
    # assumes that the names got assigned a more fitting abbreviation but these here do also belong to that name
    # Implement a treshold for a minimal score?
    unmatched_abbrs_with_only_one_edge = [node for node in assigned_graph.nodes if
                                          assigned_graph.degree(node) == 0 and len(list(graph.neighbors(node))) == 1]
    print(f"{len(unmatched_abbrs_with_only_one_edge)} abbreviations have only one edge in the old graph")
    # add them
    for abbr in unmatched_abbrs_with_only_one_edge:
        author_mapping.loc[len(author_mapping)] = [list(graph.neighbors(abbr))[0], abbr]
    print(f"after adding abbreviations with only one edge: author_mapping has {author_mapping.shape[0]} rows")

    # list remaining abbreviations
    remaining_abbrs = [node for node in assigned_graph.nodes if assigned_graph.degree(node) == 0 and len(list(graph.neighbors(node))) > 1]
    print(f"{len(remaining_abbrs)} remain unmatched: {remaining_abbrs}")

    print(f"write authors dataframe to csv file")
    authors.to_csv("../../../reports/data_sheets/authors.csv", index=False)

    print(f"write author_mapping to {db_file_path}")
    write_to_database(authors=authors, author_mapping=author_mapping)

    print("Finished mapping abbreviations to authors")

    # return values for visualization and evaluation
    return authors, authors_frequency_score, authors_department_score, author_mapping, self_referencing_authors, remaining_abbrs



def construct_assigned_graph(abbreviations_list, full_names_list, graph):

    new_edges = nx.bipartite.minimum_weight_full_matching(graph, top_nodes=full_names_list, weight="weight")
    assigned_graph = nx.Graph()
    assigned_graph.clear()
    assigned_graph.add_nodes_from(full_names_list, bipartite=0)
    assigned_graph.add_nodes_from(abbreviations_list, bipartite=1)
    assigned_graph.add_edges_from(new_edges.items())

    print(f"calculated new assigned graph with {len(assigned_graph.nodes)} nodes and {len(assigned_graph.edges)} edges")

    return assigned_graph


def create_graph(authors):

    graph = nx.Graph()
    graph.clear()
    full_names_list = authors["full_name"].unique().tolist()
    abbreviations_list = authors["abbreviation"].unique().tolist()
    graph.add_nodes_from(full_names_list, bipartite=0)
    graph.add_nodes_from(abbreviations_list, bipartite=1)
    dummy_nodes = [f"{name}_dummy" for name in full_names_list]
    graph.add_nodes_from(dummy_nodes, bipartite=1)
    for index, row in authors.iterrows():
        graph.add_edges_from([(row["full_name"], row["abbreviation"])], weight=round(row["normalized_score"], 2))
    for full_name in full_names_list:
        graph.add_edges_from([(full_name, f"{full_name}_dummy")], weight=DUMMY_NODE_WEIGHT)

    print(f"constructed graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

    return graph, full_names_list, abbreviations_list


def write_to_database(authors, author_mapping, db_file_path="../../../data/interim/articles_with_author_mapping.db"):
    con, cur = get_db_connection(db_file_path)
    # insert mapped authors, use tqdm

    insert_mapped_authors(cur, author_mapping=author_mapping)

    insert_unmapped_names(cur, author_mapping=author_mapping, authors=authors)

    insert_unmapped_abbreviations(cur, author_mapping=author_mapping, authors=authors)

    print("persist changes to database")
    con.commit()

    all_articles = get_articles(cur)
    for article in tqdm(all_articles):
        article_id = article['id']
        article_authors = article['author_array']
        article_authors_are_abbreviations = article['author_is_abbreviation']
        for author in article_authors:
            if article_authors_are_abbreviations[article_authors.index(author)] is False:
                cur.execute('select an.id from author_names an where an.name_id = (select id from names where name = ?)', (author,))
            else:
                cur.execute('select aa.id from author_abbreviations aa where aa.abbreviation_id = (select id from abbreviations where abbreviation = ?)', (author,))

            author_id = cur.fetchone()
            if author_id is None:
                raise Exception(f"author {author} is not in database")

            author_id = author_id[0]
            time = datetime.utcnow().isoformat()
            cur.execute('insert into mapped_article_authors values (?,?,?,?,?)', (None, article_id, author_id, time, time))

    print("persist changes to database")
    con.commit()

def insert_mapped_authors(cur, author_mapping):
    print(f"insert {author_mapping.shape[0]} mapped authors into database")
    for index, row in tqdm(author_mapping.iterrows(), total=len(author_mapping)):
        name, abbreviation = row["full_name"], row["abbreviation"]

        # test if name or abbreviation is already in database
        cur.execute('select * from names where name=?', (name,))
        name_id = cur.fetchone()
        cur.execute('select * from abbreviations where abbreviation=?', (abbreviation,))
        abbreviation_id = cur.fetchone()

        # if both is already in database, throw error
        if name_id is not None and abbreviation_id is not None:
            raise Exception(f"Both name {name} and abbreviation {abbreviation} are already in database")

        # if only name is already in database, add abbreviation to author_abbreviations
        if name_id is not None:
            name_id = name_id[0]
            cur.execute('select * from author_names where name_id=?', (name_id,))
            author_id = cur.fetchone()
            if author_id is None:
                # somehow the name got added but no author_names entry was created, raise exception
                raise Exception(f"Name {name} is in database but no author_names entry was created")

            author_id = author_id[1]

            # insert into abbreviations
            time = datetime.utcnow().isoformat()
            cur.execute('insert into abbreviations values (?,?,?,?)', (None, abbreviation, time, time))
            abbreviation_id = cur.lastrowid

            cur.execute('insert into author_abbreviations values (?,?,?,?,?)',
                        (None, author_id, abbreviation_id, time, time))
            continue

        # if only abbreviation is already in database, add name to author_names
        if abbreviation_id is not None:
            abbreviation_id = abbreviation_id[0]
            cur.execute('select * from author_abbreviations where abbreviation_id=?', (abbreviation_id,))
            author_id = cur.fetchone()

            if author_id is None:
                # somehow the abbreviation got added but no author_abbreviations entry was created, raise exception
                raise Exception(f"Abbreviation {abbreviation} is in database but no author_abbreviations entry was created")

            author_id = author_id[1]

            # insert into names
            time = datetime.utcnow().isoformat()
            cur.execute('insert into names values (?,?,?,?)', (None, name, time, time))
            name_id = cur.lastrowid

            cur.execute('insert into author_names values (?,?,?,?,?)', (None, author_id, name_id, time, time))
            continue

        time = datetime.utcnow().isoformat()
        # create new author entity
        cur.execute('insert into authors values (?,?,?)', (None, time, time))
        author_id = cur.lastrowid

        # insert into names
        cur.execute('insert into names values (?,?,?,?)', (None, name, time, time))
        name_id = cur.lastrowid

        # insert into author_names
        cur.execute('insert into author_names values (?,?,?,?,?)', (None, author_id, name_id, time, time))

        # insert into abbreviations
        cur.execute('insert into abbreviations values (?,?,?,?)', (None, abbreviation, time, time))
        abbreviation_id = cur.lastrowid

        # insert into author_abbreviations
        cur.execute('insert into author_abbreviations values (?,?,?,?,?)',
                    (None, author_id, abbreviation_id, time, time))


def insert_unmapped_names(cur, author_mapping, authors):
    # insert unmapped authors
    unmapped_names = authors[~authors["full_name"].isin(author_mapping["full_name"])]
    print(f"insert {unmapped_names.shape[0]} unmapped names into database")
    for index, row in tqdm(unmapped_names.iterrows(), total=len(unmapped_names)):
        name = row["full_name"]
        time = datetime.utcnow().isoformat()
        # create new author entity
        cur.execute('insert into authors values (?,?,?)', (None, time, time))
        author_id = cur.lastrowid

        # insert into names
        cur.execute('insert into names values (?,?,?,?)', (None, name, time, time))
        name_id = cur.lastrowid

        # insert into author_names
        cur.execute('insert into author_names values (?,?,?,?,?)', (None, author_id, name_id, time, time))


def insert_unmapped_abbreviations(cur, author_mapping, authors):
    # insert unmapped abbreviations
    unmapped_abbreviations = authors[~authors["abbreviation"].isin(author_mapping["abbreviation"])]
    print(f"insert {unmapped_abbreviations.shape[0]} unmapped abbreviations into database")
    for index, row in tqdm(unmapped_abbreviations.iterrows(), total=len(unmapped_abbreviations)):
        abbreviation = row["abbreviation"]
        time = datetime.utcnow().isoformat()

        # create new author entity
        cur.execute('insert into authors values (?,?,?)', (None, time, time))
        author_id = cur.lastrowid

        # insert into abbreviations
        cur.execute('insert into abbreviations values (?,?,?,?)', (None, abbreviation, time, time))
        abbreviation_id = cur.lastrowid

        # insert into author_abbreviations
        cur.execute('insert into author_abbreviations values (?,?,?,?,?)',
                    (None, author_id, abbreviation_id, time, time))


if __name__ == '__main__':
    map_abbreviations_to_authors("../../../data/interim/articles_with_author_mapping.db")
