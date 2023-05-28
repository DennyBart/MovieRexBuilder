import datetime
import os
import pandas as pd
import uuid
import openai
from lib2to3.pytree import Base
from flask import session
import requests
import logging
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from movie_rec.ai_service.models import Base, OpenAIHistory
from movie_rec.services.models.model import MovieRecommendationRelation, MovieRecommendations
from movie_rec.services.movie_search import process_request, query_movie_by_uuid
from movie_rec.utils import UUIDEncoder

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_rec"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def create_movie_list(response):
    lines = response.split("\n")
    movie_data = []
    for line in lines:
        if "Movie: " in line and ", Year: " in line:
            # Remove any leading or trailing white space
            line = line.strip()

            # Remove the numerical index if it exists
            if ". " in line:
                _, line = line.split(". ", 1)

            movie, year = line.split(", Year: ")

            # Remove the 'Movie: ' from the movie string
            movie = movie.replace("Movie: ", "")
            
            movie_data.append({"Movie": movie, "Year": year})

        elif "I'm sorry" in line:
            return None

        elif 'Movie:' in line and 'Year:' in line:
            movie, year = line.split(', ')
            movie = movie.split(': ')[1]
            year = year.split(': ')[1]
            movie_data.append([movie, year])

    return movie_data


def fetch_movie_details(movies, omdb_api_key):
    movie_list = []
    for movie in movies:
        movie_details = process_request('movie_name', movie['Movie'], omdb_api_key, movie['Year'])
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


def get_chatgpt_response(movie_type, value: int, input_message, api_model, omdb_api_key, openai_api_key):
    rec_uuid, rec_count  = check_movie_recommendation(movie_type, value)
    logging.info(f"Movie Recommendation UUID: {rec_count} and {value}")
    if rec_count == value:
        movie_list = get_related_movies(rec_uuid)
        output_list = []
        for movie_uuid in movie_list:
            movie_details = query_movie_by_uuid(movie_uuid)
            output_list.append(movie_details.to_dict())
        # Convert output_list to JSON
        logging.info(f"Movie Recommendation UUID: {rec_uuid}")
        logging.info(f"Movie List: {output_list}")
        output_json = json.dumps(output_list, cls=UUIDEncoder)
        return output_json

    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=api_model,
        messages=input_message
    )
    combined_message = f"Top {str(value)} {movie_type} movies"
    logging.info(f"OpenAI Request Message: {response['choices'][0]['message']}")
    resp_message = response['choices'][0]['message']['content']

    movie_data = create_movie_list(resp_message)
    if movie_data is None:
        return f'{combined_message} is not supported.'

    df = pd.DataFrame(movie_data, columns=['Movie', 'Year'])
    resp_json = df.to_json(orient='records')
    movies = json.loads(resp_json)

    movie_list = fetch_movie_details(movies, omdb_api_key)
    store_movie_recommendation(movie_list, movie_type, value)
    return resp_json


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
