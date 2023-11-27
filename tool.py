#!/usr/bin/env python3
import argparse
import logging
import pandas as pd
import numpy as np
import os
from langchain.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PyPDFium2Loader
from langchain.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import random
from helpers.df_helpers import documents2Dataframe
from helpers.df_helpers import df2Graph
from helpers.df_helpers import graph2Df


# Set up logging for verbose output
logging.basicConfig(level=logging.INFO)

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
    regenerate = True
    if regenerate:
        concepts_list = df2Graph(df, model='zephyr:latest')
        dfg1 = graph2Df(concepts_list)
        if not os.path.exists(outputdirectory):
            os.makedirs(outputdirectory)
        
        dfg1.to_csv(outputdirectory/"graph.csv", sep="|", index=False)
        df.to_csv(outputdirectory/"chunks.csv", sep="|", index=False)
    else:
        dfg1 = pd.read_csv(outputdirectory/"graph.csv", sep="|")

    dfg1.replace("", np.nan, inplace=True)
    dfg1.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
    dfg1['count'] = 4 
    ## Increasing the weight of the relation to 4. 
    ## We will assign the weight of 1 when later the contextual proximity will be calculated.  
    print(dfg1.shape)
    dfg1.head()


def main(args):
    # Example of verbose output
    logging.info('Starting the process with the following arguments:')
    logging.info(args)

    # Assume process_documents is a function that processes the documents
    logging.info('Processing documents...')
    processed_data = process_documents(args.documents)

    # Assume visualize_graph is a function that creates and visualizes the graph
    logging.info('Creating and visualizing the graph...')
    graph = visualize_graph(processed_data)

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