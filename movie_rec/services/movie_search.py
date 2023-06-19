from datetime import datetime
from dotenv import load_dotenv
import os
from psycopg2 import OperationalError
from sqlalchemy.sql import exists
import uuid
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    sessionmaker,
    joinedload
)
import requests
import logging
import urllib.parse
from constants import OMDB_PLOT

from movie_rec.services.models.model import (
    Base,
    CastName,
    MovieCast,
    MovieData,
    MovieRecommendations,
    MovieRecommendationsSearchList,
    MoviesNotFound
)

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def get_cast(name, cast_type):
    cast_name = session.query(CastName).filter(
        CastName.name == name, CastName.cast_type == cast_type).first()
    return cast_name if cast_name else None


def create_cast(cast_list, cast_type):
    cast_instances = []
    for cast_member in cast_list:
        cast_name = get_cast(cast_member, cast_type)
        if cast_name is None:
            cast_name = CastName(
                name=cast_member, cast_type=cast_type, uuid=uuid.uuid4())
        cast_instances.append(cast_name)
    return cast_instances


def get_movie_cast(movie_uuid):
    # Fetch the movie by UUID and eager-load the cast
    movie = session.query(MovieData)\
        .options(joinedload(MovieData.cast))\
        .filter(MovieData.uuid == movie_uuid)\
        .one()

    # Organize the cast by their type
    cast_by_type = {
        'actor': [],
        'director': [],
        'writer': []
    }

    for movie_cast in movie.cast:
        cast_by_type[movie_cast.cast.cast_type].append(movie_cast.cast.name)

    # Return cast_by_type as a Python dictionary
    return cast_by_type


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


def store_failed_request(title, year, rec_topic=None):
    not_found_movie = MoviesNotFound(
        title=title,
        year=year,
        rec_topic=rec_topic,
        searched_at=datetime.utcnow()
    )
    session.add(not_found_movie)
    session.commit()


def process_request_by_id(identifier, api_key):
    movie_data = query_movie_by_id(identifier)
    if movie_data:
        logging.info(f"Movie_ID {identifier} found in local database")
        movie_dict = movie_data.to_dict()
        movie_dict["cast"] = get_movie_cast(movie_data.uuid)
        return jsonify(movie_dict)

    logging.info(f"Movie_id {identifier} not found in local database")
    movie_data = search_movie_by_id(identifier, api_key)
    if movie_data:
        store_new_movie(movie_data)
        get_stored_movie = query_movie_by_id(movie_data['imdbID'])
        movie_dict = get_stored_movie.to_dict()
        movie_dict["cast"] = get_movie_cast(get_stored_movie.uuid)
        return jsonify(movie_dict)

    logging.info(f"Movie_id {identifier} not found in OMDB")
    store_failed_request(identifier, None)
    return jsonify({"error": f"Movie_id {identifier} not found"}), 404


def process_request_by_name(identifier, api_key, year, rec_topic=None):
    movie_data = query_movie_by_name(identifier)
    print(f'Movie data: {identifier}')
    if movie_data:
        logging.info(f"Movie_title {identifier} {year} "
                     f"found in local database")
        movie_dict = movie_data.to_dict()
        movie_dict["cast"] = get_movie_cast(movie_data.uuid)
        return jsonify(movie_dict)
    logging.info(f"Movie_title {identifier} not found in local database")
    movie_data = search_movie_by_title(identifier, year, api_key)
    if movie_data and movie_data.get('Type') != 'series':
        is_movie_local = query_movie_by_id(movie_data['imdbID'])
        if is_movie_local:
            movie_dict = is_movie_local.to_dict()
            movie_dict["cast"] = get_movie_cast(is_movie_local.uuid)
            return jsonify(movie_dict)
        else:
            # Store movie in local database
            store_new_movie(movie_data)
            # Get movie from local database since data is now available
            get_stored_movie = query_movie_by_id(movie_data['imdbID'])
            movie_dict = get_stored_movie.to_dict()
            movie_dict["cast"] = get_movie_cast(get_stored_movie.uuid)
            return jsonify(movie_dict)

    logging.info(f"Movie_title {identifier} not found in OMDB")
    store_failed_request(identifier, year, rec_topic)


def process_request(request_type, identifier,
                    api_key, year=None, rec_topic=None):
    if request_type == 'movie_id':
        return process_request_by_id(identifier, api_key)
    elif request_type == 'movie_name':
        return process_request_by_name(identifier, api_key, year, rec_topic)


def query_movie_by_id(identifier):
    return session.query(MovieData).filter(
        MovieData.imdbid == identifier).first()


def check_db():
    try:
        # Replace the connection URL with your actual database connection URL
        engine = create_engine(DATABASE_URL)
        engine.connect()
    except OperationalError:
        raise DBNotFoundError("Database not found or connection refused.")


class DBNotFoundError(Exception):
    pass


def query_movie_by_uuid(uuid):
    return session.query(MovieData).filter(
        MovieData.uuid == uuid).first()


def query_movie_by_name(identifier):
    return session.query(MovieData).filter(
        MovieData.title.ilike(identifier)).first()


def get_non_generated_movie_topics():
    return session.query(MovieRecommendationsSearchList.title).filter_by(
        generated=False).all()


def set_movie_topic_to_generated(movie_topic):
    movie_topic = session.query(MovieRecommendationsSearchList).filter_by(
        title=movie_topic).first()
    movie_topic.generated = True
    session.commit()


def store_new_movie(movie_data):
    new_movie = process_movie_data(movie_data)
    logging.info(f"Storing new movie {new_movie.title}")
    session.add(new_movie)
    session.commit()


def search_movie_by_id(movie_id, api_key):
    plot = OMDB_PLOT
    logging.info(f"Searching OMDB movie with id {movie_id}")
    if plot == 'full':
        url = f"http://www.omdbapi.com/?i={movie_id}"
        f"&apikey={api_key}&plot=full"
    else:
        url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    logging.info(f"OMDB response: {data}")

    if data.get('Response') == 'True':
        return data
    else:
        return None


# "http://127.0.0.1:5000/movies?title=Swallow&year=2019"
def search_movie_by_title(title, year, api_key):
    plot = OMDB_PLOT
    encoded_title = urllib.parse.quote_plus(title)
    logging.info(f"Searching OMDB for movie with "
                 f"title {title} and year {year}")
    if plot == 'full':
        url = f"http://www.omdbapi.com/?t={encoded_title}&y={year}&apikey={api_key}&plot={plot}"  # noqa
    else:
        url = f"http://www.omdbapi.com/?t={encoded_title}&y={year}&apikey={api_key}" # noqa
    try:
        response = requests.get(url)
        data = response.json()
        logging.info(f"OMDB response: {data}")

        if data.get('Response') == 'True':
            return data
        else:
            return None
    except requests.exceptions.ConnectionError as e:
        print(f"ConnectionError occurred while searching movie by title: {e}")
        return None


def store_search_titles(titles):
    processed_title = []
    for title in titles:
        if session.query(exists().where(
             MovieRecommendationsSearchList.title == title)).scalar():
            continue
        logging.info(f"Storing movie topic {title} in database")
        movie_rec_search = MovieRecommendationsSearchList(
            title=title,
            generated=False,
            generated_at=datetime.now()
        )
        session.add(movie_rec_search)
        processed_title.append(title)

    session.commit()
    return processed_title


def get_recommendations(search=None, limit=50, offset=0):
    query = session.query(MovieRecommendations)

    if search:
        query = query.filter(MovieRecommendations.topic_name.ilike(f'%{search}%'))
    recommendations = query.offset(offset).limit(limit).all()
    return recommendations


def get_recommendation_name(uuid):
    return session.query(MovieRecommendations).filter_by(
        uuid=uuid).first().topic_name


def store_blurb_to_recommendation(uuid, blurb):
    recommendation = session.query(MovieRecommendations).filter_by(
        uuid=uuid).first()
    recommendation.blurb = blurb
    session.commit()


def get_recommendation_blurb(uuid):
    # Get the blurb for the given uuid.
    # Return None if no matching record found.
    record = session.query(MovieRecommendations).filter_by(uuid=uuid).first()
    return record.blurb if record else None
