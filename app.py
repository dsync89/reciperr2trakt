import requests
import json
import time
import os
import logging

# Replace these with your Trakt API client ID, client secret, and access token file path
CLIENT_ID = 'xxx' # get from trakt
CLIENT_SECRET = 'yyy' # get from trakt
TOKEN_FILE_PATH = 'access_token.json'

# Trakt username and list name
USERNAME = 'd-sync' # replace with your trakt username
LIST_NAME = 'Reciperr - Aliens Theme Movies (1990-2030, No Animation, No Superheroes)' # replace with the list name you want to create
LIST_DESCRIPTION = 'A list of movies from Reciperr, imported using https://github.com/dsync89/reciperr2trakt'

# URL from which to fetch movies JSON data
MOVIES_URL = 'https://reciperr.com/api/recipe/list/params?recipeMetadataId=66b08869655ec328d05828f7' # StevenLu formatted JSON list, get it from https://reciperr.com

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_access_token():
    """Load the access token from the JSON file if it exists."""
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, 'r') as token_file:
            return json.load(token_file).get('access_token')
    return None

def save_access_token(access_token):
    """Save the access token to a JSON file."""
    with open(TOKEN_FILE_PATH, 'w') as token_file:
        json.dump({'access_token': access_token}, token_file)
    logging.info('Access token saved to file.')

def is_token_valid(access_token):
    """Check if the access token is valid by making a simple authenticated request."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }
    response = requests.get('https://api.trakt.tv/users/me', headers=headers)
    return response.status_code == 200

def get_new_access_token():
    """Obtain a new access token using the device code flow."""
    device_code_url = 'https://api.trakt.tv/oauth/device/code'
    device_code_payload = {
        'client_id': CLIENT_ID
    }
    device_code_response = requests.post(device_code_url, data=device_code_payload)
    device_code_data = device_code_response.json()

    logging.info(f"Please go to {device_code_data['verification_url']} and enter the code: {device_code_data['user_code']}")

    poll_url = 'https://api.trakt.tv/oauth/device/token'
    poll_payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': device_code_data['device_code']
    }

    access_token = None
    while True:
        poll_response = requests.post(poll_url, data=poll_payload)
        
        try:
            poll_data = poll_response.json()
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from response.")
            logging.debug(f"Response content: {poll_response.text}")
            time.sleep(device_code_data['interval'])
            continue

        if poll_response.status_code == 200:
            access_token = poll_data['access_token']
            save_access_token(access_token)
            break
        elif poll_response.status_code == 400:
            logging.info("Waiting for user to authorize the app...")
            time.sleep(device_code_data['interval'])
        else:
            logging.error(f"Error: {poll_data.get('error_description', 'Unknown error')}")
            break

    if not access_token:
        logging.critical("Failed to obtain access token.")
        exit()

    return access_token

def fetch_movies_data(url):
    """Fetch movies JSON data from the URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch movies data. Status code: {response.status_code}, Response: {response.text}")
        exit()

def get_list_id_or_slug(username, list_name, headers):
    """Check if the list exists and return its ID or slug."""
    list_url = f'https://api.trakt.tv/users/{username}/lists'
    response = requests.get(list_url, headers=headers)

    if response.status_code == 200:
        lists = response.json()
        for trakt_list in lists:
            if trakt_list['name'].lower() == list_name.lower():
                return trakt_list['ids']['trakt'], None
        return None, None
    else:
        logging.error(f"Failed to fetch lists. Status code: {response.status_code}, Response: {response.json()}")
        exit()

def create_list(username, list_name, list_description, headers):
    """Create a new list and return its ID and slug."""
    create_list_url = f'https://api.trakt.tv/users/{username}/lists'
    list_data = {
        'name': list_name,
        'description': list_description,
        'privacy': 'private',  # You can change this to 'public' if you want the list to be public
        'display_numbers': False,
        'allow_comments': True,
        'sort_by': 'rank',
        'sort_how': 'asc'
    }
    create_response = requests.post(create_list_url, headers=headers, data=json.dumps(list_data))
    
    if create_response.status_code == 201:
        created_list = create_response.json()
        logging.info(f"List created successfully. ID: {created_list['ids']['trakt']}, Slug: {created_list['ids']['slug']}")
        return created_list['ids']['trakt'], created_list['ids']['slug']
    else:
        logging.error(f"Failed to create list. Status code: {create_response.status_code}, Response: {create_response.json()}")
        exit()

def add_items_to_list(username, list_identifier, items, headers):
    """Add items to the Trakt list."""
    add_items_url = f'https://api.trakt.tv/users/{username}/lists/{list_identifier}/items'
    add_response = requests.post(add_items_url, headers=headers, data=json.dumps(items))

    if add_response.status_code == 201:
        logging.info("Movies added successfully.")
    else:
        logging.error(f"Failed to add movies. Status code: {add_response.status_code}, Response: {add_response.json()}")

def main():
    # Load the access token from the file
    access_token = load_access_token()

    # If no token is loaded or the token is invalid, request a new one
    if not access_token or not is_token_valid(access_token):
        logging.info("Access token is invalid or expired. Requesting a new one...")
        access_token = get_new_access_token()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }

    # Fetch movies JSON data from the URL
    movies = fetch_movies_data(MOVIES_URL)

    # Check if the movies data is in the expected format
    if not isinstance(movies, list):
        logging.error("Movies data is not in the expected format.")
        exit()

    # Check if the list exists
    list_id, list_slug = get_list_id_or_slug(USERNAME, LIST_NAME, headers)

    if not list_id:
        # List does not exist, create it
        list_id, list_slug = create_list(USERNAME, LIST_NAME, LIST_DESCRIPTION, headers)

    # Prepare the data to be sent to Trakt
    items = {
        "movies": [
            {
                "ids": {
                    "imdb": movie.get("imdb_id")
                },
                "notes": "Added from Recipiarr"
            }
            for movie in movies
        ]
    }

    # Add items to the list
    add_items_to_list(USERNAME, list_id, items, headers)

if __name__ == "__main__":
    main()
