# #!/usr/bin/env python3
# import argparse
# import logging
# #import cudf as pd
# import pandas as pd
# #import cupy as np
# import numpy as np
# import os
# from langchain.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PyPDFium2Loader
# from langchain.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from pathlib import Path
# import random
# from helpers.df_helpers import documents2Dataframe
# from helpers.df_helpers import df2Graph
# from helpers.df_helpers import graph2Df
# import networkx as nx
# import seaborn as sns
# from pyvis.network import Network
# import gravis as gv
# import sqlite3

#!/usr/bin/env python3

# Standard Library Imports
import argparse
import logging
import os
from pathlib import Path
import random
import sqlite3

# Third-party Library Imports
import numpy as np
import pandas as pd
import seaborn as sns
import networkx as nx
from pyvis.network import Network
import gravis as gv

#for printing to console in color
from colorama import Fore, Style

# Local Module Imports
from langchain.document_loaders import (
    PyPDFLoader,
    UnstructuredPDFLoader,
    PyPDFium2Loader,
    PyPDFDirectoryLoader,
    DirectoryLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from helpers.df_helpers import documents2Dataframe, df2Graph, graph2Df





#TODO : Replace pandas with cudf
#TODO : Replace networkx with cuGraph (also: Can we use GPU for the graph calculations for initial HTML layout?)


# Set up logging for verbose output
logging.basicConfig(level=logging.INFO)

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

database = "./data_output/mydatabase.db"

sql_create_chunks_table = """ CREATE TABLE IF NOT EXISTS chunks (
                                    id integer PRIMARY KEY,
                                    chunk_id text NOT NULL,
                                    text_content text
                                ); """

sql_create_graphs_table = """ CREATE TABLE IF NOT EXISTS graphs (
                                    id integer PRIMARY KEY,
                                    node_1 text NOT NULL,
                                    node_2 text NOT NULL,
                                    edge text,
                                    count integer
                                ); """

# Create a database connection
conn = create_connection(database)

# Create tables
if conn is not None:
    create_table(conn, sql_create_chunks_table)
    create_table(conn, sql_create_graphs_table)
else:
    print("Error! cannot create the database connection.")

def insert_chunk(conn, chunk):
    """
    Insert a new chunk into the chunks table
    """
    sql = ''' INSERT INTO chunks(chunk_id, text_content)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, chunk)
    conn.commit()
    return cur.lastrowid

# Use this function to insert chunks
# chunk = ('chunk_id_123', 'Some text content')
# insert_chunk(conn, chunk)


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
    inputdirectory = Path(f"./data_input/{data_dir}_reports")
    outputdirectory = Path(f"./data_output/{data_dir}")

    database = f"./data_output/{data_dir}.db"
    conn = create_connection(database)

    # Create tables
    if conn is not None:
        create_table(conn, sql_create_chunks_table)
        create_table(conn, sql_create_graphs_table)

    loader = DirectoryLoader(inputdirectory, glob='**/*.text', show_progress=True, loader_kwargs={'content_type': 'text/plain','encoding':'utf-8'})
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )

    # Split documents into chunks and assign a unique ID to each chunk
    pages = splitter.split_documents(documents)
    # import pprint
    # pprint.pprint(pages[0].to_json())
    # pprint.pprint(pages[1].to_json())
    # pprint.pprint(pages[2].to_json())
    print("Number of chunks = ", len(pages))

    # Convert the split documents to a dataframe and include chunk IDs
    df = documents2Dataframe(pages)
    print(df.shape)

    
    # df.head()
    # Regenerate the graph if the flag is set to True, leaving this here to bypass when debugging
    regenerate = True
    if regenerate:
        # concepts_list = df2Graph(df, model='yichat:34')
        concepts_list = df2Graph(df, model='yichat:34', include_chunk_id=True)
        dfg1 = graph2Df(concepts_list)

        if not os.path.exists(outputdirectory):
            os.makedirs(outputdirectory)
        
        #dfg1.to_csv(outputdirectory/"graph.csv", sep="|", index=False)
        #df.to_csv(outputdirectory/"chunks.csv", sep="|", index=False)
        #write to sqldb instead
        dfg1.to_sql('graphs', conn, if_exists='replace', index=False)
        df.to_sql('chunks', conn, if_exists='replace', index=False)

    else:
        # dfg1 = pd.read_csv(outputdirectory/"graph.csv", sep="|")
        # df = pd.read_csv(outputdirectory/"chunks.csv", sep="|")
        #load from sqlite
        dfg1 = pd.read_sql_query("SELECT * FROM graphs", conn)
        df = pd.read_sql_query("SELECT * FROM chunks", conn)


    dfg1.replace("", np.nan, inplace=True)
    dfg1.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
    dfg1['count'] = 4 
    ## Increasing the weight of the relation to 4. 
    ## We will assign the weight of 1 when later the contextual proximity will be calculated.  
    print(dfg1.shape)
    dfg1.head()
    if conn:
        conn.close()
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
    # Create a dictionary to store each node with its associated chunk ids
    node_chunk_ids = {}

    # Iterate over each row in the DataFrame and update the dictionary
    for index, row in dfg.iterrows():
        for node in [row['node_1'], row['node_2']]:
            if node not in node_chunk_ids:
                node_chunk_ids[node] = set()
            node_chunk_ids[node].update(row['chunk_id'].split(','))

    # Convert the set of chunk ids to a comma-separated string for each node
    for node in node_chunk_ids:
        node_chunk_ids[node] = ','.join(node_chunk_ids[node])

    print(node_chunk_ids)
    return node_chunk_ids

# def update_html_file(html_file_path):
#     # First string to search for in the file
#     search_string_1 = "shownNode.label = state.manager.calcSingleNodeLabelText(parsedNode)"
#     # String to insert after the first search string
#     insert_string_1 = "              shownNode.chunk_id = parsedNode.chunk_id"

#     # Second string to search for in the file
#     search_string_2 = "              function nodeClicked(event, node){"
#     # String to insert after the second search string
#     insert_string_2 = "                let nodeString = JSON.stringify(node, null, 2);" \
#                       "\n                let htmlText = \"<div>Node: \" + String(node.id) + \"<pre>\" + nodeString + \"</pre></div>\";"
#     insert_string_2 +="""
#                       // Fetch chunk data from the server
#                   if (node.chunk_id) {
#                     fetch('/get_chunk_data/' + node.chunk_id)
#                       .then(response => response.json())
#                       .then(data => {
#                         // Process and display the chunk data
#                         let chunkDataHtml = '<div><strong>Chunk Data:</strong><br>';
#                         for (let key in data) {
#                           chunkDataHtml += `<strong>${key}:</strong> ${data[key]}<br>`;
#                         }
#                         chunkDataHtml += '</div>';

#                         htmlText = chunkDataHtml + htmlText;
#                         ui.elements.detailsBody.innerHTML = htmlText;
#                       })
#                       .catch(error => console.error('Error fetching chunk data:', error));
#                   } else {
#                     ui.elements.detailsBody.innerHTML = htmlText;
#                   }
#     """
#     delete_string = "let htmlText = \"<div>Node: \" + String(node.id) + \"</div>\";"


#     try:
#         # Read the content of the HTML file
#         with open(html_file_path, 'r') as file:
#             lines = file.readlines()

#         # Process the lines
#         modified_lines = []
#         for line in lines:
#             if delete_string in line:
#                 # Skip appending this line as it matches the delete string
#                 print(f"Deleted the string: {line.strip()}")
#                 continue            
#             modified_lines.append(line)
#             if search_string_1 in line:
#                 # Add the first new line after the found line
#                 modified_lines.append(insert_string_1 + '\n')
#                 print(f"Found the string: {search_string_1}")
#                 print(f"Inserted the string: {insert_string_1}")
#             if search_string_2 in line:
#                 # Add the second new line after the found line
#                 modified_lines.append(insert_string_2 + '\n')
#                 print(f"Found the string: {search_string_2}")
#                 print(f"Inserted the string: {insert_string_2}")

#         # Write the changes back to the file
#         with open(html_file_path, 'w') as file:
#             file.writelines(modified_lines)
#             print("File updated successfully.")

#     except IOError as e:
#         print(f"An error occurred: {e}")


def update_html_file(html_file_path):
    # First string to search for in the file
    search_string_1 = "shownNode.label = state.manager.calcSingleNodeLabelText(parsedNode)"
    # String to insert after the first search string
    insert_string_1 = "              shownNode.chunk_id = parsedNode.chunk_id"

    # Second string to search for in the file
    search_string_2 = "              function nodeClicked(event, node){"
    # Updated string to insert after the second search string
    insert_string_2 = """
                let nodeString = JSON.stringify(node, null, 2);
                let htmlText = "<div>Node: " + String(node.id) + "<pre>" + nodeString + "</pre></div>";
                if (typeof(node.click) !== "undefined" && node.click !== "") {
                  htmlText += '<div id="inD9wPVOuc8ypcDkM-details-user-provided">' + node.click + '</div>';
                }
                // Fetch chunk data from the server
if (node.chunk_id) {
    fetch('/get_chunk_data/' + node.chunk_id)
        .then(response => response.json())
        .then(data => {
            // Start the table
            let tableHtml = '<div><strong>Chunk Data:</strong><br><table border="1"><tr><th>Text</th><th>Image (Click for PDF)</th><th>Chunk ID</th></tr>';

            data.forEach((item) => {
                // Check if item is an array with three elements
                if (Array.isArray(item) && item.length === 3) {
                    let text = item[0];

                    // Replace the beginning of the sourceFile string and .text with .img
                    let imgSource = item[1].replace('data_input/', '/static/').replace('.text', '.img');
                    // Create a link to the PDF file
                    let pdfLink = imgSource.replace('.img', '.pdf');

                    let chunkId = item[2];

                    // Embedding the source file as an image source wrapped in a link to the PDF
                    let imgHtml = `<a href="${pdfLink}" target="_blank"><img src="${imgSource}" alt="Image" style="max-width:100px; max-height:100px;"></a>`;

                    tableHtml += `<tr><td>${text}</td><td>${imgHtml}</td><td>${chunkId}</td></tr>`;
                } else {
                    // Handle the case where item is not the expected array
                    console.error('Item is not an array of three elements:', item);
                }
            });

            // Close the table
            tableHtml += '</table></div>';

            htmlText = tableHtml + htmlText;
            ui.elements.detailsBody.innerHTML = htmlText;
        })
        .catch(error => console.error('Error fetching chunk data:', error));
}

    """

    delete_string = "let htmlText = \"<div>Node: \" + String(node.id) + \"</div>\";"

    try:
        # Read the content of the HTML file
        with open(html_file_path, 'r') as file:
            lines = file.readlines()

        # Process the lines
        modified_lines = []
        for line in lines:
            if delete_string in line:
                # Skip appending this line as it matches the delete string
                print(f"Deleted the string: {line.strip()}")
                continue
            modified_lines.append(line)
            if search_string_1 in line:
                # Add the first new line after the found line
                modified_lines.append(insert_string_1 + '\n')
                print(f"Found the string: {search_string_1}")
                print(f"Inserted the string: {insert_string_1}")
            if search_string_2 in line:
                # Add the second new line after the found line
                modified_lines.append(insert_string_2 + '\n')
                print(f"Found the string: {search_string_2}")
                print(f"Inserted the string: {insert_string_2}")

        # Write the changes back to the file
        with open(html_file_path, 'w') as file:
            file.writelines(modified_lines)
            print("File updated successfully.")

    except IOError as e:
        print(Fore.RED, f"An error occurred: {e}")

def make_network_x_graph(dfg, node_chunk_ids, args):
    G = nx.Graph()

    # Add nodes to the graph with chunk id as metadata
    for node, chunk_ids in node_chunk_ids.items():
        G.add_node(
            str(node),
            title=f"Node ID: {node}",
            chunk_id=chunk_ids
        )

    ## Add edges to the graph
    for index, row in dfg.iterrows():
        #print(row["node_1"], row["node_2"], row["edge"], row['count'])
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

    graph_output_directory = f"./static/{args}_index.html"

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

    gv_fig = gv.d3(G, show_node_label=True, use_node_size_normalization=True, node_size_normalization_max=30,  graph_height=1000,
                use_edge_size_normalization=True, 
                edge_size_data_source='weight', 
                details_height=300, 
                many_body_force_strength = -374.89,
                # use_collision_force= True,
                edge_curvature=0.3)
    #gv_fig.show()
    #delete ./static/mimic_test_gravis.html if it exists
    os.remove(f"./static/{args}_gravis.html") if os.path.exists(f"./static/{args}_gravis.html") else None
    gravis_path = f"./static/{args}_gravis.html"
    
    gv_fig.export_html(gravis_path)
    update_html_file(gravis_path)

        

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
    make_network_x_graph(graph, nodes, args.documents)
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