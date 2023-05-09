from datetime import datetime
import uuid
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests
import logging
import urllib.parse

from movie_rec.services.models.model import Base, CastName, MovieCast, MovieData, MoviesNotFound

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_database"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def get_cast(name, cast_type):
    cast_name = session.query(CastName).filter(CastName.name == name, CastName.cast_type == cast_type).first()
    return cast_name if cast_name else None


def create_cast(cast_list, cast_type):
    cast_instances = []
    for cast_member in cast_list:
        cast_name = get_cast(cast_member, cast_type)
        if cast_name is None:
            cast_name = CastName(name=cast_member, cast_type=cast_type, uuid=uuid.uuid4())
        cast_instances.append(cast_name)
    return cast_instances


def process_movie_data(movie_data):
    actors = movie_data['Actors'].split(', ')
    directors = movie_data['Director'].split(', ')
    writers = movie_data['Writer'].split(', ')
    del movie_data['Response']

    movie_data = {
        key.lower(): value
        for key, value in movie_data.items()
        if key.lower() not in ['actors', 'director', 'writer']
    }
    movie_data['uuid'] = uuid.uuid4()
    new_movie = MovieData(**movie_data)

    for actor in create_cast(actors, 'actor'):
        movie_cast = MovieCast(movie=new_movie, cast=actor)
        new_movie.cast.append(movie_cast)

    for director in create_cast(directors, 'director'):
        movie_cast = MovieCast(movie=new_movie, cast=director)
        new_movie.cast.append(movie_cast)

    for writer in create_cast(writers, 'writer'):
        movie_cast = MovieCast(movie=new_movie, cast=writer)
        new_movie.cast.append(movie_cast)

    return new_movie


def store_failed_request(title, year):
    not_found_movie = MoviesNotFound(
        title=title,
        year=year,
        searched_at=datetime.utcnow()
    )
    session.add(not_found_movie)
    session.commit()

from sqlalchemy import or_


def process_request(request_type, identifier, api_key, year=None):
    if request_type == 'movie_id':
        movie_data = session.query(MovieData).filter(MovieData.imdbid == identifier).first()
        if not movie_data:
            logging.info(f"Movie_id {identifier} not found in local database")
            movie_data = search_movie_by_id(identifier, api_key)
            if movie_data:
                new_movie = process_movie_data(movie_data)
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                logging.info(f"Movie_id {identifier} not found in OMDB")
                store_failed_request(identifier, None)
                return jsonify({"error": f"Movie_id {identifier} not found"}), 404
        else:
            return jsonify(movie_data.to_dict())

    elif request_type == 'movie_name':
        movie_data = session.query(MovieData).filter(MovieData.title == identifier).first()
        if not movie_data:
            logging.info(f"Movie_title {identifier} not found in local database")
            movie_data = search_movie_by_title(identifier, year, api_key)
            # TODO Optimiise this DB query
            if movie_data and movie_data.get('Type') != 'series':
                title_exists = session.query(MovieData).filter(MovieData.imdbid == movie_data['imdbID']).first()
                if title_exists:
                    return jsonify(title_exists.to_dict())
                new_movie = process_movie_data(movie_data)
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                logging.info(f"Movie_title {identifier} not found in OMDB")
                store_failed_request(identifier, year)
                return jsonify({"error": f"Movie_title {identifier} not found"}), 404
        else:
            return jsonify(movie_data.to_dict())


def search_movie_by_id(movie_id, api_key):
    logging.info(f"Searching OMDB movie with id {movie_id}")
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None

# "http://127.0.0.1:5000/movies?title=Swallow&year=2019"
def search_movie_by_title(title, year, api_key):
    encoded_title = urllib.parse.quote_plus(title)
    logging.info(f"Searching OMDB for movie with title {title} and year {year}")
    url = f"http://www.omdbapi.com/?t={encoded_title}&y={year}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None
