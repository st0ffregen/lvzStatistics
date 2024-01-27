import networkx as nx
import pandas as pd

from src.author_mapping.scripts import calculate_frequency_score
from src.author_mapping.scripts import calculate_department_score

DUMMY_NODE_WEIGHT = 0.8


def map_abbreviations_to_authors(db_file_path):
    authors_frequency_score = calculate_frequency_score.calculate_frequency_score(db_file_path)
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
        print(f"add abbreviation {abbr} to author {list(graph.neighbors(abbr))[0]}")
        author_mapping.loc[len(author_mapping)] = [list(graph.neighbors(abbr))[0], abbr]

    # list remaining abbreviations
    remaining_abbrs = [node for node in assigned_graph.nodes if assigned_graph.degree(node) == 0 and len(list(graph.neighbors(node))) > 1]
    print(f"{len(remaining_abbrs)} remain unmatched: {remaining_abbrs}")

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


if __name__ == '__main__':
    map_abbreviations_to_authors("../../../data/interim/articles_with_author_mapping.db")
