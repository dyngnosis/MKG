import uuid
import pandas as pd
import cupy as np
from .prompts import extractConcepts
from .prompts import graphPrompt


def documents2Dataframe(documents) -> pd.DataFrame:
    """
    Convert a list of document objects into a pandas DataFrame.

    Each document object typically contains page content and metadata. This function creates a DataFrame where each row represents a document, including its content and metadata.

    Args:
    documents (list): A list of document objects with attributes 'page_content' and 'metadata'.

    Returns:
    pd.DataFrame: A pandas DataFrame where each row represents a document.
    """    
    rows = []
    for chunk in documents:
        row = {
            "text": chunk.page_content,
            **chunk.metadata,
            "chunk_id": uuid.uuid4().hex,
        }
        rows = rows + [row]

    df = pd.DataFrame(rows)
    return df


def df2ConceptsList(dataframe: pd.DataFrame) -> list:
    """
    Extract concepts from a DataFrame and return them as a list.

    This function applies the extractConcepts function to each row of the DataFrame to extract key concepts.

    Args:
    dataframe (pd.DataFrame): A pandas DataFrame with a column 'text' containing document content.

    Returns:
    list: A list of extracted concepts.
    """
    # dataframe.reset_index(inplace=True)
    results = dataframe.apply(
        lambda row: extractConcepts(
            row.text, {"chunk_id": row.chunk_id, "type": "concept"}
        ),
        axis=1,
    )
    # invalid json results in NaN
    results = results.dropna()
    results = results.reset_index(drop=True)

    ## Flatten the list of lists to one single list of entities.
    concept_list = np.concatenate(results).ravel().tolist()
    return concept_list


def concepts2Df(concepts_list) -> pd.DataFrame:
    """
    Convert a list of concepts into a pandas DataFrame.

    This function creates a DataFrame from a list of concept dictionaries. It also standardizes the 'entity' field by converting it to lowercase.

    Args:
    concepts_list (list): A list of dictionaries, each representing a concept.

    Returns:
    pd.DataFrame: A pandas DataFrame representing the concepts.
    """
    ## Remove all NaN entities
    concepts_dataframe = pd.DataFrame(concepts_list).replace(" ", np.nan)
    concepts_dataframe = concepts_dataframe.dropna(subset=["entity"])
    concepts_dataframe["entity"] = concepts_dataframe["entity"].apply(
        lambda x: x.lower()
    )

    return concepts_dataframe


def df2Graph(dataframe: pd.DataFrame, model=None) -> list:
    """
    Apply the graphPrompt function to each row of a DataFrame and return the results as a list.

    This function is used to generate a graph structure from a DataFrame containing document text.

    Args:
    dataframe (pd.DataFrame): A DataFrame with a column 'text' containing document content.
    model (str, optional): The name of the model to be used in the graphPrompt function.

    Returns:
    list: A list of graph nodes and edges.
    """
    # dataframe.reset_index(inplace=True)
    results = dataframe.apply(
        lambda row: graphPrompt(row.text, {"chunk_id": row.chunk_id}, model), axis=1
    )
    # invalid json results in NaN
    results = results.dropna()
    results = results.reset_index(drop=True)

    ## Flatten the list of lists to one single list of entities.
    concept_list = np.concatenate(results).ravel().tolist()
    return concept_list


def graph2Df(nodes_list) -> pd.DataFrame:
    """
    Convert a list of graph nodes into a pandas DataFrame.

    This function creates a DataFrame from a list of node dictionaries. It also standardizes node names by converting them to lowercase.

    Args:
    nodes_list (list): A list of dictionaries, each representing a graph node.

    Returns:
    pd.DataFrame: A pandas DataFrame representing the graph nodes.
    """
    ## Remove all NaN entities
    graph_dataframe = pd.DataFrame(nodes_list).replace(" ", np.nan)
    graph_dataframe = graph_dataframe.dropna(subset=["node_1", "node_2"])
    graph_dataframe["node_1"] = graph_dataframe["node_1"].apply(lambda x: x.lower())
    graph_dataframe["node_2"] = graph_dataframe["node_2"].apply(lambda x: x.lower())

    return graph_dataframe
