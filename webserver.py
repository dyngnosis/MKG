# from flask import Flask, jsonify, send_from_directory
# import sqlite3
# import os

# app = Flask(__name__)

# # Function to get chunk data from SQLite database
# def get_chunk_data(chunk_id):
#     # Updated database connection path
#     conn = sqlite3.connect('./data_output/mimic_test.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
#     data = cursor.fetchone()
#     conn.close()
#     return data

# # Route to get chunk data
# @app.route('/get_chunk_data/<chunk_id>')
# def chunk_data(chunk_id):
#     data = get_chunk_data(chunk_id)
#     print(data)
#     if data:
#         return jsonify(data)
#     else:
#         return jsonify({"error": "Data not found"}), 404

# # Route to serve static files
# @app.route('/static/<path:path>')
# def send_static(path):
#     return send_from_directory('static', path)

# # Optionally, define a route for the root or any other HTML page
# @app.route('/')
# def index():
#     return send_from_directory('static', 'index.html')

# if __name__ == '__main__':
#     # Ensure the 'static' directory exists
#     if not os.path.exists('static'):
#         os.makedirs('static')
#     app.run(debug=True)

from flask import Flask, jsonify, send_from_directory, request
import sqlite3
import os

app = Flask(__name__)

# Function to get chunk data from SQLite database for multiple chunk IDs
def get_chunk_data(chunk_ids, db_name):
    # Construct the database file path
    db_file = os.path.join('./data_output', db_name + '.db')
    
    # Check if the database file exists
    if not os.path.exists(db_file):
        return None

    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    print(f"looking in database {db_file} at chunk_ids {chunk_ids}")
    # Prepare the query for multiple chunk IDs
    query = f"SELECT * FROM chunks WHERE chunk_id IN ({','.join('?' * len(chunk_ids))})"
    cursor.execute(query, chunk_ids)
    data = cursor.fetchall()
    print("data is", data)  
    conn.close()
    return data

# Route to get chunk data for one or more chunk IDs
@app.route('/get_chunk_data/<chunk_ids>')
def chunk_data(chunk_ids):
    # Split the chunk_ids by comma
    chunk_id_list = chunk_ids.split(',')
    print(chunk_id_list)

    # Extract the database name from the referer URL
    referer = request.headers.get('Referer', '')
    if referer:
        db_name = os.path.splitext(os.path.basename(referer))[0]
        db_name = db_name.split('_')[0]
        print(db_name)
    else:
        return jsonify({"error": "Referer not found"}), 400

    data = get_chunk_data(chunk_id_list, db_name)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Data not found"}), 404

# Route to serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Optionally, define a route for the root or any other HTML page
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    # Ensure the 'static' directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
