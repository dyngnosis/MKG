import requests
import json
import time

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
    
    # Delay to respect the rate limit
    time.sleep(0.3)  # Delay for 0.3 seconds (30/100 = 0.3)

# Save the data to a file
filename = 'library_entries.json'
with open(filename, 'w') as file:
    json.dump(all_entries, file, indent=4)

print(f"All data saved to {filename}.")
