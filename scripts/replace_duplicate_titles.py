import sys
sys.path.append('C:/Users/denis/Dev/MovieRexBuilder') # noqa
import os
from dotenv import load_dotenv
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from movie_rec.models import MovieRecommendations

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Setup logging
logging.basicConfig(filename='renamed_titles.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Modify this with your actual SQLAlchemy connection string
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL, pool_recycle=280)
session = Session(engine)


def update_movie_recommendation(old_value, new_value):
    print(f"Updating '{old_value}' to '{new_value}'...")
    movie_entry = session.query(MovieRecommendations).filter_by(
        topic_name=old_value).first()

    if movie_entry:
        movie_entry.topic_name = new_value
        session.commit()
        log_message = f"Updated entry from '{old_value}' to '{new_value}'."
        logging.info(log_message)
        print(log_message)
    else:
        log_message = f"No entry found for '{old_value}'."
        logging.warning(log_message)
        print(log_message)


# Read the file and update the database
with open('duplicate_titles.txt', 'r') as file:
    for line in file:
        old_title, new_title = line.strip().split(' - ')
        update_movie_recommendation(old_title, new_title)
