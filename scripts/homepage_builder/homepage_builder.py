import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(filename='site_update_log.log', level=logging.INFO, format='%(asctime)s - %(message)s') # noqa

# API keys
SCHEDULED_PAGE_API_KEY = os.getenv('SCHEDULED_PAGE_API_KEY')
BASE_URL = os.getenv('BASE_URL')


# Endpoints
generate_recs_in_db_url = f'{BASE_URL}/api/generate_recs_in_db' # noqa
generate_movie_rec_titles_url = f'{BASE_URL}/api/generate_movie_rec_titles' # noqa
gen_homepage_data_url = f'{BASE_URL}/api/gen_homepage_data'

# Headers
api_headers = {
    'x-api-key': SCHEDULED_PAGE_API_KEY,
    'Content-Type': 'application/json'
}

# Data for the requests
data_recs_in_db = {
    "blurb": "false",
    "lists_to_generate": 10,
    "movies_per_list": 20
}

data_generate_movie_rec_titles = {
    "total": 25
}


def log_message(message):
    date = datetime.now()
    print(date, message)


# Function to call APIs with error handling and retries
def call_generate_recs_in_db():
    try:
        response = requests.post(generate_recs_in_db_url, json=data_recs_in_db, headers=api_headers, timeout=300) # noqa
        if response.status_code == 400 and response.json().get('error') == "generation_title_limit cannot be more than total_titles, generate more titles": # noqa
            log_message('INFO: Encountered generation_title_limit error, generating more titles.') # noqa
            generate_more_titles()
            # Retry after generating more titles
            call_generate_recs_in_db()
        elif response.status_code == 200:
            log_message('INFO: Successfully generated recommendations in DB.')
        else:
            log_message(f'ERROR: Failed to generate recommendations in DB. Status code: {response.status_code}, Response: {response.text}') # noqa
    except Exception as e:
        log_message(f'ERROR: Error while generating recommendations in DB: {e}') # noqa


def generate_more_titles():
    try:
        response = requests.post(generate_movie_rec_titles_url, json=data_generate_movie_rec_titles, headers=api_headers, timeout=120) # noqa
        if response.status_code == 200:
            log_message('INFO: Successfully generated additional movie recommendation titles.') # noqa
        else:
            log_message(f'ERROR: Failed to generate additional movie recommendation titles. Status code: {response.status_code}, Response: {response.text}') # noqa
    except Exception as e:
        log_message(f'ERROR: Error while generating additional movie recommendation titles: {e}') # noqa


def gen_homepage_data():
    for i in range(4):
        try:
            response = requests.post(gen_homepage_data_url, headers=api_headers, data='', timeout=60) # noqa
            if response.status_code == 200:
                log_message('INFO: Successfully generated homepage data.')
            else:
                log_message(f'ERROR: Failed to generate homepage data. Status code: {response.status_code}, Response: {response.text}') # noqa
        except Exception as e:
            log_message(f'ERROR: Error while generating homepage data: {e}')


# Main process
if __name__ == "__main__":
    call_generate_recs_in_db()
    gen_homepage_data()
