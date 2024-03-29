import requests
import json

def update_lib():
    # API endpoint
    url = 'https://orkl.eu/api/v1/library/entries'

    # Initialize pagination parameters
    limit = 100  # Number of entries to retrieve per request
    offset = 0   # Initial offset

    all_entries = []  # List to store all entries

    while True:
        # Prepare query parameters
        params = {
            'limit': limit,
            'offset': offset,
            'order_by': 'created_at',
            'order': 'asc'
        }

        # Send GET request
        response = requests.get(url, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            # Retrieve JSON data from response
            data = response.json()

            # Extract entries from the response data
            entries = data['data']

            # Add the retrieved entries to the main list
            all_entries.extend(entries)

            # Increment the offset for the next request
            offset += limit

            # Check if there are more entries to retrieve
            if len(entries) < limit:
                break  # Exit the loop if all entries have been retrieved
        else:
            print(f"Failed to retrieve entries. Status code: {response.status_code}")
            break

    # Create a dictionary containing all entries
    data_dict = {
        "data": all_entries
    }
    filename = 'library_entries.json'
    with open(filename, 'w') as file:
        json.dump(data_dict, file.read(), indent=4)
        print(f"All entries saved to {filename}.")

filename = 'library_entries.json'
with open(filename, 'r') as file:
    all_entries = json.load(file)
    print(all_entries.keys())
    
# Print progress
    num_entries = len(all_entries["data"])
    print(f"Total entries: {num_entries}")
    for i, entry in enumerate(all_entries["data"], 1):
        entry_id = entry['id']
        entry_title = entry['title']
        print(f"Processing entry {i}/{num_entries}: {entry_id} - {entry_title}")
        # Save the associated files
        files = entry['files']
        for file_type, file_url in files.items():
            file_response = requests.get(file_url)
            if file_response.status_code == 200:
                file_content = file_response.content
                file_extension = file_type.split('.')[-1]
                file_save_path = f"entry_{entry_id}.{file_extension}"
                with open(file_save_path, 'wb') as file:
                    file.write(file_content)
                    print(f"Saved {file_type}: {file_save_path}")
            else:
                print(f"Failed to download {file_type} for entry {entry_id}. Status code: {file_response.status_code}")

<<<<<<<< HEAD:2_download_all_txt.py
                # Check if the file already exists
                if os.path.exists(file_save_path):
                    print(f"File {file_save_path} already exists. Skipping download.")
                    continue
                try:

                    file_response = requests.get(file_url)
                    if file_response.status_code == 200:
                        file_content = file_response.content
                        with open(file_save_path, 'wb') as file:
                            file.write(file_content)
                            print(f"Saved {file_type}: {file_save_path}")
                    else:
                        print(f"Failed to download {file_type} for entry {entry_id}. Status code: {file_response.status_code}")

                    # Additional processing for each entry can be added here

                    print(f"Entry {entry_id} processed.")
                except requests.exceptions.ConnectionError:
                    print("Connection Error", file_url)

if __name__ == "__main__":
    main()

    
========
            # Additional processing for each entry can be added here

            print(f"Entry {entry_id} processed.")
>>>>>>>> parent of fec08a34 (improved graph generation):gen_library_entries.json.py
