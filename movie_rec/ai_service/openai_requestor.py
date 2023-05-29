import datetime
import pandas as pd
import uuid
import openai
from lib2to3.pytree import Base
from flask import session
import logging
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from movie_rec.ai_service.models import Base
from movie_rec.services.models.model import MovieRecommendationRelation, MovieRecommendations
from movie_rec.services.movie_search import process_request, query_movie_by_uuid
from movie_rec.utils import UUIDEncoder

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_rec"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


import re

def create_movie_list(response):
    lines = response.split("\n")
    movie_data = []
    for line in lines:
        line = line.strip()  # Remove leading and trailing white space
        try:
            if ": " in line or ", Year: " in line:
                if ". " in line:
                    index, line = line.split(". ", 1)
                    index = index.strip()  # Remove leading/trailing whitespace
                else:
                    index = None  # No index is given

                if "Movie: " in line:
                    _, movie_with_year = line.split("Movie: ", 1)
                elif "Movie Name: " in line:
                    _, movie_with_year = line.split("Movie Name: ", 1)
                elif "Name: " in line:
                    _, movie_with_year = line.split("Name: ", 1)
                else:
                    movie_with_year = line

                movie_with_year = movie_with_year.strip()
                if ", Year: " in movie_with_year:
                    movie, year = movie_with_year.split(", Year: ")
                else:
                    movie, year = movie_with_year.split(": ")

                movie = movie.strip()  # Remove leading and trailing white space

                # Extract only the year as an integer
                year = re.search(r'\d{4}', year)  # Search for a four digit number representing the year
                if year:
                    year = int(year.group())  # Convert the year to integer
                else:
                    year = None  # No valid year found

                # Append the movie data as a dictionary
                movie_data.append({"Index": index, "Movie": movie, "Year": year})

        except ValueError as e:
            print(f"An error occurred while processing line: {line}. Error: {e}")
    if not movie_data:
        return None

    return movie_data



def fetch_movie_details(movies, omdb_api_key, rec_topic=None):
    movie_list = []
    for movie in movies:
        movie_details = process_request('movie_name', movie['Movie'], omdb_api_key, movie['Year'], rec_topic)
        if movie_details is not None:
            data = json.loads(movie_details.data)
            movie_uuid = data.get('uuid')
            movie_list.append(movie_uuid)
            # TODO - Add movie details to logging
            logging.info(f"Movie Details: {movie_uuid}")
    return movie_list


def store_movie_recommendation(movie_list, movie_type, count):
    # Check if any of the movies in movie_list are already in the database
    # movie_id_str = ','.join(str(uuid) for uuid in movie_list)

    rec_uuid = uuid.uuid4()
    new_recommendations = MovieRecommendations(
        uuid=rec_uuid,
        topic_name=str(movie_type),
        count=int(count),
        date_generated=datetime.datetime.now(),
        casting_id=None
    )
    session.add(new_recommendations)
    session.commit()
    for movie in movie_list:
        # add movie uuid and recomendation uuid to MovieRecommendation
        new_movie_recommendation = MovieRecommendationRelation(
            recommendation_uuid=rec_uuid,
            movie_uuid=movie
        )
        session.add(new_movie_recommendation)
    logging.info(f"Movie Recommendation UUID: {rec_uuid}")
    session.commit()


def get_existing_recommendations(movie_type: str, value: int) -> str:
    rec_uuid, rec_count  = check_movie_recommendation(movie_type, value)
    logging.info(f"Movie Recommendation UUID: {rec_count} and {value}")
    
    if rec_count == value:
        movie_list = get_related_movies(rec_uuid)
        output_list = []
        for movie_uuid in movie_list:
            movie_details = query_movie_by_uuid(movie_uuid)
            output_list.append(movie_details.to_dict())
        
        logging.info(f"Movie Recommendation UUID: {rec_uuid}")
        logging.info(f"Movie List: {output_list}")
        output_json = json.dumps(output_list, cls=UUIDEncoder)
        return output_json

    return None


import time
import openai

def get_new_recommendations(api_model: str, openai_api_key: str, movie_type: str, value: int, input_message: list) -> str:
    openai.api_key = openai_api_key
    logging.info(f"OpenAI Request Message: {input_message}")
    try:
        response = openai.ChatCompletion.create(
            model=api_model,
            messages=input_message
        )
    except openai.error.RateLimitError:
        time.sleep(5)  # Wait for 5 seconds before retrying
        return get_new_recommendations(api_model, openai_api_key, movie_type, value, input_message)

    combined_message = f"Top {str(value)} {movie_type}"
    logging.info(f"OpenAI Request Message: {response['choices'][0]['message']}")
    resp_message = response['choices'][0]['message']['content']

    movie_data = create_movie_list(resp_message)
    if movie_data is None:
        return f'{combined_message} is not supported.'
    if len(movie_data) < value:
        return ValueError(f"Not all movies were found. Only {len(movie_data)} movies were found.")
    return movie_data


def get_recommendation_titles(api_model: str, openai_api_key: str, value: int, input_message: list) -> str:
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=api_model,
        messages=input_message
    )
    print(response)
    return response['choices'][0]['message']['content']


def process_new_recommendations(movie_data: list, omdb_api_key: str, movie_type: str, value: int) -> str:
    df = pd.DataFrame(movie_data, columns=['Movie', 'Year'])
    resp_json = df.to_json(orient='records')
    movies = json.loads(resp_json)

    movie_list = fetch_movie_details(movies, omdb_api_key, movie_type)
    store_movie_recommendation(movie_list, movie_type, value)
    return resp_json


def get_chatgpt_movie_rec(movie_type: str, value: int, input_message: list, api_model: str, omdb_api_key: str, openai_api_key: str) -> str:
    existing_recommendations = get_existing_recommendations(movie_type, value)
    if existing_recommendations is not None:
        return existing_recommendations

    num_attempts = 0
    while num_attempts < 3:
        try:
            new_recommendations = get_new_recommendations(api_model, openai_api_key, movie_type, value, input_message)
            if new_recommendations is not None:
                return process_new_recommendations(new_recommendations, omdb_api_key, movie_type, value)
        except ValueError:
            num_attempts += 1

    return "Error: Failed to retrieve movie recommendations."


def check_movie_recommendation(search_term, value):
    # Use '%' as a wildcard to find similar topic names
    movie_recommendation = (
        session.query(MovieRecommendations)
        .filter(MovieRecommendations.topic_name.like(f"%{search_term}%"))
        .filter(MovieRecommendations.count == value)
        .first()
    )

    if movie_recommendation is None:
        return None, None
    else:
        return movie_recommendation.uuid, movie_recommendation.count


def get_related_movies(recommendation_uuid):
    # Query the relation table to get all associated movie UUIDs
    movie_relations = session.query(MovieRecommendationRelation).filter_by(recommendation_uuid=recommendation_uuid).all()

    # Create a list to hold all the movie_uuid values
    related_movies = [relation.movie_uuid for relation in movie_relations]

    return related_movies
