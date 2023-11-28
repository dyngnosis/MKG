#!/usr/bin/env python3
import argparse
import logging
#import cudf as pd
import pandas as pd
import cupy as np
import os
from langchain.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PyPDFium2Loader
from langchain.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import random
from helpers.df_helpers import documents2Dataframe
from helpers.df_helpers import df2Graph
from helpers.df_helpers import graph2Df
import networkx as nx
import seaborn as sns
from pyvis.network import Network



# Set up logging for verbose output
logging.basicConfig(level=logging.INFO)

def contextual_proximity(df: pd.DataFrame) -> pd.DataFrame:
    ## Melt the dataframe into a list of nodes
    dfg_long = pd.melt(
        df, id_vars=["chunk_id"], value_vars=["node_1", "node_2"], value_name="node"
    )
    dfg_long.drop(columns=["variable"], inplace=True)
    # Self join with chunk id as the key will create a link between terms occuring in the same text chunk.
    dfg_wide = pd.merge(dfg_long, dfg_long, on="chunk_id", suffixes=("_1", "_2"))
    # drop self loops
    self_loops_drop = dfg_wide[dfg_wide["node_1"] == dfg_wide["node_2"]].index
    dfg2 = dfg_wide.drop(index=self_loops_drop).reset_index(drop=True)
    ## Group and count edges.
    dfg2 = (
        dfg2.groupby(["node_1", "node_2"])
        .agg({"chunk_id": [",".join, "count"]})
        .reset_index()
    )
    dfg2.columns = ["node_1", "node_2", "chunk_id", "count"]
    dfg2.replace("", np.nan, inplace=True)
    dfg2.dropna(subset=["node_1", "node_2"], inplace=True)
    # Drop edges with 1 count
    dfg2 = dfg2[dfg2["count"] != 1]
    dfg2["edge"] = "contextual proximity"
    return dfg2



def process_documents(data_dir):
    inputdirectory = Path(f"./data_input/{data_dir}")

    ## This is where the output csv files will be written
    outputdirectory = Path(f"./data_output/{data_dir}")

    loader = DirectoryLoader(inputdirectory, glob='**/*.text', show_progress=True, loader_kwargs={'content_type': 'text/plain','encoding':'utf-8'})

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )

    pages = splitter.split_documents(documents)
    print("Number of chunks = ", len(pages))
    df = documents2Dataframe(pages)
    print(df.shape)
    # df.head()
    # Regenerate the graph if the flag is set to True, leaving this here to bypass when debugging
    regenerate = False
    if regenerate:
        concepts_list = df2Graph(df, model='mistral-openorca:latest')
        dfg1 = graph2Df(concepts_list)
        if not os.path.exists(outputdirectory):
            os.makedirs(outputdirectory)
        
        dfg1.to_csv(outputdirectory/"graph.csv", sep="|", index=False)
        df.to_csv(outputdirectory/"chunks.csv", sep="|", index=False)
    else:
        dfg1 = pd.read_csv(outputdirectory/"graph.csv", sep="|")
        df = pd.read_csv(outputdirectory/"chunks.csv", sep="|")


    dfg1.replace("", np.nan, inplace=True)
    dfg1.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
    dfg1['count'] = 4 
    ## Increasing the weight of the relation to 4. 
    ## We will assign the weight of 1 when later the contextual proximity will be calculated.  
    print(dfg1.shape)
    dfg1.head()
    return dfg1

def contextual_proximity(df: pd.DataFrame) -> pd.DataFrame:
    ## Melt the dataframe into a list of nodes
    dfg_long = pd.melt(
        df, id_vars=["chunk_id"], value_vars=["node_1", "node_2"], value_name="node"
    )
    dfg_long.drop(columns=["variable"], inplace=True)
    # Self join with chunk id as the key will create a link between terms occuring in the same text chunk.
    dfg_wide = pd.merge(dfg_long, dfg_long, on="chunk_id", suffixes=("_1", "_2"))
    # drop self loops
    self_loops_drop = dfg_wide[dfg_wide["node_1"] == dfg_wide["node_2"]].index
    dfg2 = dfg_wide.drop(index=self_loops_drop).reset_index(drop=True)
    ## Group and count edges.
    dfg2 = (
        dfg2.groupby(["node_1", "node_2"])
        .agg({"chunk_id": [",".join, "count"]})
        .reset_index()
    )
    dfg2.columns = ["node_1", "node_2", "chunk_id", "count"]
    dfg2.replace("", np.nan, inplace=True)
    dfg2.dropna(subset=["node_1", "node_2"], inplace=True)
    # Drop edges with 1 count
    dfg2 = dfg2[dfg2["count"] != 1]
    dfg2["edge"] = "contextual proximity"
    return dfg2


def merge_graphs(dfg1, dfg2):
    dfg = pd.concat([dfg1, dfg2], axis=0)
    dfg = (
        dfg.groupby(["node_1", "node_2"])
        .agg({"chunk_id": ",".join, "edge": ','.join, 'count': 'sum'})
        .reset_index()
    )   
    return dfg 

def calc_networkx_graph(dfg):
    nodes = pd.concat([dfg['node_1'], dfg['node_2']], axis=0).unique()
    nodes.shape
    return nodes

def make_network_x_graph(dfg, nodes):
    G = nx.Graph()

    ## Add nodes to the graph
    for node in nodes:
        G.add_node(
            str(node),
            title=f"Node ID: {node}",
            # input_string=input_string,
            # chunk_id=chunk_id            
        )

    ## Add edges to the graph
    for index, row in dfg.iterrows():
        G.add_edge(
            str(row["node_1"]),
            str(row["node_2"]),
            title=row["edge"],
            weight=row['count']/4
        )

    #calculate community for colouring
    communities_generator = nx.community.girvan_newman(G)
    top_level_communities = next(communities_generator)
    next_level_communities = next(communities_generator)
    communities = sorted(map(sorted, next_level_communities))
    print("Number of Communities = ", len(communities))
    print(communities)
    colors = colors2Community(communities)
    for index, row in colors.iterrows():
        G.nodes[row['node']]['group'] = row['group']
        G.nodes[row['node']]['color'] = row['color']
        G.nodes[row['node']]['size'] = G.degree[row['node']]

    graph_output_directory = "./docs/index.html"

    net = Network(
        notebook=False,
        bgcolor="#1a1a1a",
        cdn_resources="remote",
        height="1600px",  # Set the height to 80%
        width="100%",
        select_menu=True,
        font_color="#cccccc",
        filter_menu=True,
    )

    net.from_nx(G)
    for node in G.nodes(data=True):
        net.get_node(node[0])["title"] = f"Node ID: {node[0]}"

    # net.repulsion(node_distance=150, spring_length=400)
    net.force_atlas_2based(central_gravity=0.015, gravity=-31)
    # net.barnes_hut(gravity=-18100, central_gravity=5.05, spring_length=380)
    net.show_buttons(filter_=["physics"])

    net.show(graph_output_directory, notebook=False)
        

## Now add these colors to communities and make another dataframe
def colors2Community(communities) -> pd.DataFrame:
    ## Define a color palette
    palette = "hls"
    p = sns.color_palette(palette, len(communities)).as_hex()
    random.shuffle(p)
    rows = []
    group = 0
    for community in communities:
        color = p.pop()
        group += 1
        for node in community:
            rows += [{"node": node, "color": color, "group": group}]
    df_colors = pd.DataFrame(rows)
    return df_colors



def main(args):
    # Example of verbose output
    logging.info('Starting the process with the following arguments:')
    logging.info(args)

    # Assume process_documents is a function that processes the documents
    logging.info('Processing documents...')
    dfg1 = process_documents(args.documents)

    # Assume visualize_graph is a function that creates and visualizes the graph
    logging.info('Creating and visualizing the graph...')
    dfg2 = contextual_proximity(dfg1)
    #dfg2.tail()
    graph = merge_graphs(dfg1, dfg2)
    nodes = calc_networkx_graph(graph)
    make_network_x_graph(graph, nodes)
    # graph = visualize_graph(dfg1)


    logging.info('Process completed successfully.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI tool for processing documents and generating a knowledge graph.')

    # Define the arguments this CLI will accept
    parser.add_argument('documents', type=str, help='Path to the documents to process')
    # Add more arguments as needed

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    main(args)