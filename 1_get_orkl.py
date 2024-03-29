import requests
import json
import time
import logging
from requests.exceptions import HTTPError, ConnectionError

# Initialize logging
logging.basicConfig(level=logging.INFO)

def fetch_entries(session, api_url, limit, offset):
    params = {
        'limit': limit,
        'offset': offset,
        'order_by': 'created_at',
        'order': 'asc'
    }
    try:
        response = session.get(api_url, params=params)
        response.raise_for_status()
        return response.json()['data']
    except (HTTPError, ConnectionError) as err:
        logging.error(f"Request failed: {err}")
        return None

def save_to_file(entries, filename):
    try:
        with open(filename, 'w') as file:
            json.dump({"data": entries}, file, indent=4)  # Wrap entries in a dictionary
    except IOError as err:
        logging.error(f"Failed to save data: {err}")

def main():
    api_url = 'https://orkl.eu/api/v1/library/entries'
    limit = 100
    offset = 0
    all_entries = []
    
    with requests.Session() as session:
        while True:
            entries = fetch_entries(session, api_url, limit, offset)
            if entries is None:
                break

            all_entries.extend(entries)
            if len(entries) < limit:
                break

            offset += limit
            time.sleep(0.3)

        if all_entries:
            save_to_file(all_entries, 'library_entries.json')
            logging.info("All data saved successfully.")

if __name__ == "__main__":
    main()
