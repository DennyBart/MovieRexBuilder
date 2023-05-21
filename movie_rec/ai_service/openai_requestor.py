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
from movie_rec.services.models.model import MovieRecommendations
from movie_rec.services.movie_search import process_request

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_database"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def create_movie_list(response):
    lines = response.strip().split('\n')
    data = []
    for line in lines:
        if "I'm sorry" in line:
            return None
        if 'Movie:' in line and 'Year:' in line:
            if '. ' in line:
                _, info = line.split('. ')
            movie, year = info.split(', ')
            movie = movie.split(': ')[1]
            year = year.split(': ')[1]
            data.append([movie, year])
    return data


def fetch_movie_details(movies, omdb_api_key):
    movie_list = []
    print(f"Movies: {movies}")
    for movie in movies:
        movie_details = process_request('movie_name', movie['Movie'], omdb_api_key, movie['Year'])
        data = json.loads(movie_details.data)
        movie_uuid = data.get('uuid')
        movie_list.append(movie_uuid)
        # TODO - Add movie details to logging
        logging.info(f"Movie Details: {movie_uuid}")
    print(f"Movie List: {movie_list}")
    return movie_list


def store_movie_recommendation(movie_list, combined_message):
    # Check if any of the movies in movie_list are already in the database
    movie_id_str = ','.join(str(uuid) for uuid in movie_list)

    print(f'Movie List: {movie_list}')
    rec_uuid = uuid.uuid4()
    new_recommendation = MovieRecommendations(
        uuid=str(rec_uuid),
        movie_id=movie_id_str,
        topic_name=str(combined_message),
        date_generated=datetime.datetime.now(),
        casting_id=None
    )
    session.add(new_recommendation)
    session.commit()


def get_chatgpt_response(movie_type, value: int, input_message, api_model, omdb_api_key, openai_api_key):
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
    store_movie_recommendation(movie_list, combined_message)

    return resp_json
