from datetime import datetime
from dotenv import load_dotenv
import os
import re
from psycopg2 import OperationalError
import uuid
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests
import logging
import urllib.parse
from constants import OMDB_PLOT
from movie_rec.cast_service import CastProcessor
from movie_rec.image_video_service import MovieMediaProcessor

from movie_rec.models import (
    Base,
    MovieCast,
    MovieData,
    MovieImage,
    MovieRecommendations,
    MovieRecommendationsSearchList,
    MovieVideo,
    MoviesNotFound
)


load_dotenv()
THEMOVIEDB_API_KEY = os.environ['THEMOVIEDB_API_KEY']
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def process_movie_data(cast_processor, movie_data):
    actors = movie_data['Actors'].split(', ')
    directors = movie_data['Director'].split(', ')
    writers = movie_data['Writer'].split(', ')
    del movie_data['Response']

    movie_data = {
        key.lower(): value
        for key, value in movie_data.items()
        if key.lower() not in ['actors', 'director', 'writer']
    }
    movie_data['uuid'] = str(uuid.uuid4())
    new_movie = MovieData(**movie_data)

    for actor in cast_processor.create_cast(actors, 'actor'):
        movie_cast = MovieCast(movie=new_movie, cast=actor)
        new_movie.cast.append(movie_cast)

    for director in cast_processor.create_cast(directors, 'director'):
        movie_cast = MovieCast(movie=new_movie, cast=director)
        new_movie.cast.append(movie_cast)

    for writer in cast_processor.create_cast(writers, 'writer'):
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
    session.close()


def process_request_by_id(cast_processor, identifier, api_key):
    movie_data = query_movie_by_id(identifier)
    if movie_data:
        logging.info(f"Movie_ID {identifier} found in local database")
        movie_dict = movie_data.to_dict()
        movie_dict["cast"] = cast_processor.get_movie_cast(movie_data.uuid)
        return jsonify(movie_dict)

    logging.info(f"Movie_id {identifier} not found in local database")
    movie_data = search_movie_by_id(identifier, api_key)
    if movie_data:
        store_new_movie(cast_processor, movie_data)
        get_stored_movie = query_movie_by_id(movie_data['imdbID'])
        movie_dict = get_stored_movie.to_dict()
        movie_dict["cast"] = cast_processor.get_movie_cast(
            get_stored_movie.uuid
        )
        return jsonify(movie_dict)

    logging.info(f"Movie_id {identifier} not found in OMDB")
    store_failed_request(identifier, None)
    return jsonify({"error": f"Movie_id {identifier} not found"}), 404


def process_request_by_name(cast_processor, identifier,
                            api_key, year, rec_topic=None):
    identifier = re.sub(r'\s\(\d{4}\)$', '', identifier)
    movie_data = query_movie_by_name(identifier)
    if movie_data:
        logging.info(f"Movie_title {identifier} {year} "
                     f"found in local database")
        movie_dict = movie_data.to_dict()
        movie_dict["cast"] = cast_processor.get_movie_cast(movie_data.uuid)
        logging.debug(f"Movie cast: {movie_dict['cast']} - "
                      f"uuid {movie_data.uuid}")
        return jsonify(movie_dict)
    logging.info(f"Movie_title {identifier} not found in local database")
    movie_data = search_movie_by_title(identifier, year, api_key)
    if movie_data and movie_data.get('Type') != 'series' and movie_data.get('Type') != 'episode': # noqa
        is_movie_local = query_movie_by_id(movie_data['imdbID'])
        if is_movie_local:
            logging.info(f"Movie_title {identifier} {year} found in OMDB")
            movie_dict = is_movie_local.to_dict()
            movie_dict["cast"] = cast_processor.get_movie_cast(
                is_movie_local.uuid
            )
            return jsonify(movie_dict)
        else:
            # Store movie in local database
            store_new_movie(cast_processor, movie_data)
            # Get movie from local database since data is now available
            get_stored_movie = query_movie_by_id(movie_data['imdbID'])
            movie_dict = get_stored_movie.to_dict()
            movie_dict["cast"] = cast_processor.get_movie_cast(
                get_stored_movie.uuid
            )
            return jsonify(movie_dict)

    logging.info(f"Movie_title {identifier} not found in OMDB")
    store_failed_request(identifier, year, rec_topic)
    return None


def process_request(request_type, identifier,
                    api_key, year=None, rec_topic=None):
    cast_processor = CastProcessor(session)
    logging.info(f'Process request: {request_type}')
    if request_type == 'movie_id':
        return process_request_by_id(cast_processor, identifier, api_key)
    elif request_type == 'movie_name':
        response = process_request_by_name(cast_processor, identifier,
                                       api_key, year, rec_topic)
        if response:
            return response

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
        is_generated=False).all()


def set_movie_topic_to_generated(movie_topic):
    movie_topic = session.query(MovieRecommendationsSearchList).filter_by(
        title=movie_topic).first()
    movie_topic.is_generated = True
    session.commit()
    session.close()


def store_new_movie(cast_processor, movie_data):
    new_movie = process_movie_data(cast_processor, movie_data)
    logging.info(f"Storing new movie {new_movie.title}")
    imdbid = str(new_movie.imdbid)
    session.add(new_movie)
    session.commit()
    session.close()
    get_and_store_videos(imdbid)
    get_and_store_images(imdbid)


def search_movie_by_id(movie_id, api_key):
    plot = OMDB_PLOT
    logging.info(f"Searching OMDB movie with id {movie_id}")
    if plot == 'full':
        url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}&plot=full" # noqa
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
        logging.error("ConnectionError occurred while searching "
                      f"movie by title: {e}")
        return None


def store_search_titles(titles):
    # Fetch all titles from the database
    existing_titles_query = session.query(MovieRecommendationsSearchList.title)
    existing_titles = {row[0] for row in existing_titles_query}

    # Process titles
    processed_titles = []
    for title in titles:
        # Remove leading and trailing quotes
        title = title.strip('"')
        title = title.strip('25 ')
        if title not in existing_titles:
            logging.info(f'Storing movie topic "{title}" in database')
            movie_rec_search = MovieRecommendationsSearchList(
                title=title,
                is_generated=False,
                generated_at=datetime.now()
            )
            session.add(movie_rec_search)
            processed_titles.append(title)

    session.commit()
    session.close()
    return processed_titles


def get_recommendations(search=None, limit=50, offset=0):
    query = session.query(MovieRecommendations)

    if search:
        query = query.filter(MovieRecommendations.
                             topic_name.ilike(f'%{search}%'))
    recommendations = query.offset(offset).limit(limit).all()
    return recommendations


def get_recommendation_name(uuid):
    return session.query(MovieRecommendations).filter_by(
        uuid=uuid).first().topic_name


def get_recommendation_blurb(uuid):
    # Get the blurb for the given uuid.
    # Return None if no matching record found.
    record = session.query(MovieRecommendations).filter_by(uuid=uuid).first()
    return record.blurb if record else None


def store_blurb_to_recommendation(uuid, blurb):
    recommendation = session.query(MovieRecommendations).filter_by(
        uuid=uuid).first()
    recommendation.blurb = blurb
    session.commit()
    session.close()


def get_movie_imdb_id_from_uuid(uuid):
    result = session.query(MovieData.imdbid).filter_by(uuid=uuid).first()
    if result is not None:
        return result[0]
    else:
        return None


def get_and_store_images(imdbid: str,
                         include_image_language: str = 'en,null',
                         overwrite: bool = False):
    movie_media_processor = MovieMediaProcessor(session)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {THEMOVIEDB_API_KEY}"
    }
    return movie_media_processor.tmdb_request(
        imdbid, 'images', include_image_language, headers,
        overwrite, MovieImage, 5,
        movie_media_processor.process_image_data)


def get_and_store_videos(imdbid: str,
                         language: str = 'en-US',
                         overwrite: bool = False):
    movie_media_processor = MovieMediaProcessor(session)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {THEMOVIEDB_API_KEY}"
    }
    return movie_media_processor.tmdb_request(
        imdbid, 'videos', language, headers,
        overwrite, MovieVideo, 10,
        movie_media_processor.process_video_data)
