mkdir -p data_input/Akira_reports && mkdir -p data_output/Akira_reports && grep -l 'Akira' data_input/orkl/* | xargs -I {} cp {} data_input/Akira_reports ; python '3_build_graph.py' Akira
