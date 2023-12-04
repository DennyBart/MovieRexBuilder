from datetime import datetime
import hashlib
import random
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload
import os
import re
from psycopg2 import OperationalError
import uuid
from sqlalchemy import create_engine, desc, func, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import requests
import logging
import urllib.parse
from constants import OMDB_PLOT
from movie_rec.cast_service import CastProcessor
from movie_rec.homepage_data import (add_featured_content,
                                     fetch_genres_for_movies,
                                     fetch_movie_uuids,
                                     generate_movie_cast_homepage_data,
                                     get_genre,
                                     get_movie_recommendations,
                                     get_top_genres,
                                     update_recommendation)
from movie_rec.image_video_service import MovieMediaProcessor

from movie_rec.models import (
    APIKey,
    Base,
    CastName,
    FeaturedContent,
    Genre,
    MovieCast,
    MovieData,
    MovieGenre,
    MovieImage,
    MovieRecommendationRelation,
    MovieRecommendations,
    MovieRecommendationsSearchList,
    MovieVideo,
    MoviesNotFound
)
from movie_rec.types import ContentType


load_dotenv()
THEMOVIEDB_API_KEY = os.environ['THEMOVIEDB_API_KEY']
DATABASE_URL = os.environ['DATABASE_URL']
IMAGE_DOMAIN = os.getenv("IMAGE_DOMAIN")


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
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
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
        return movie_dict

    logging.info(f"Movie_id {identifier} not found in local database")
    movie_data = search_movie_by_id(identifier, api_key)
    if movie_data:
        store_new_movie(cast_processor, movie_data)
        get_stored_movie = query_movie_by_id(movie_data['imdbID'])
        movie_dict = get_stored_movie.to_dict()
        movie_dict["cast"] = cast_processor.get_movie_cast(
            get_stored_movie.uuid
        )
        return movie_dict

    logging.info(f"Movie_id {identifier} not found in OMDB")
    store_failed_request(identifier, None)
    return None


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
        return movie_dict
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
            return movie_dict
        else:
            # Store movie in local database
            store_new_movie(cast_processor, movie_data)
            # Get movie from local database since data is now available
            get_stored_movie = query_movie_by_id(movie_data['imdbID'])
            movie_dict = get_stored_movie.to_dict()
            movie_dict["cast"] = cast_processor.get_movie_cast(
                get_stored_movie.uuid
            )
            return movie_dict

    logging.info(f"Movie_title {identifier} not found in OMDB")
    store_failed_request(identifier, year, rec_topic)
    return None


def process_request(request_type,
                    identifier,
                    api_key,
                    year=None,
                    rec_topic=None):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    cast_processor = CastProcessor(session)
    logging.info(f'Process request: {request_type}')
    if request_type == 'movie_id':
        return process_request_by_id(cast_processor,
                                     identifier,
                                     api_key)
    elif request_type == 'movie_name':
        process_movie_data = process_request_by_name(cast_processor,
                                                     identifier,
                                                     api_key, year, rec_topic)
        return process_movie_data


def query_movie_by_id(identifier):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session.query(MovieData).filter(
        MovieData.imdbid == identifier).first()


def check_db():
    try:
        # Replace the connection URL with your actual database connection URL
        engine = create_engine(DATABASE_URL, pool_recycle=280)
        engine.connect()
    except OperationalError:
        raise DBNotFoundError("Database not found or connection refused.")


class DBNotFoundError(Exception):
    pass


def query_movie_by_uuid(uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session.query(MovieData).filter(
        MovieData.uuid == uuid).first()


def query_movie_by_name(identifier):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session.query(MovieData).filter(
        MovieData.title.ilike(identifier)).first()


def get_non_generated_movie_topics():
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session.query(MovieRecommendationsSearchList.title).filter_by(
        is_generated=False).all()


def set_movie_topic_to_generated(movie_topic):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_topic = session.query(MovieRecommendationsSearchList).filter_by(
        title=movie_topic).first()
    movie_topic.is_generated = True
    session.commit()
    session.close()


def store_new_movie(cast_processor, movie_data):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        new_movie = process_movie_data(cast_processor, movie_data)
        logging.info(f"Storing new movie {new_movie.title}")
        imdbid = str(new_movie.imdbid)
        session.add(new_movie)
        session.commit()
        store_movie_genre(session=session, new_movie=new_movie, genre_string=str(new_movie.genre)) # noqa
        get_and_store_videos(imdbid)
        get_and_store_images(imdbid)
    except IntegrityError as e:
        logging.error(f"IntegrityError occurred: {e}")
        session.rollback()
    finally:
        session.close()


def store_movie_genre(session, new_movie, genre_string):
    try:
        genres = genre_string.split(', ')

        for genre_name in genres:
            genre = session.query(Genre).filter_by(name=genre_name).first()

            if genre is None:
                genre = Genre(name=genre_name)
                session.add(genre)
                session.commit()

            existing_relation = session.query(MovieGenre).filter_by(
                movie_uuid=new_movie.uuid,
                genre_id='Action'
            ).first()

            if existing_relation is None:
                new_movie_genre = MovieGenre(movie_uuid=new_movie.uuid,
                                             genre_id=genre.id)
                session.add(new_movie_genre)
                session.commit()

            if genre not in new_movie.genres:
                new_movie.genres.append(genre)

    except IntegrityError as e: # noqa
        session.rollback()


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
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Fetch all titles from the database
    existing_titles_query = session.query(MovieRecommendationsSearchList.title)
    existing_titles = {row[0] for row in existing_titles_query}

    # Process titles
    processed_titles = []
    for title in titles:
        # Remove leading and trailing quotes
        title = title.strip('"')
        title = title.replace('25 ', '')
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
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    query = session.query(MovieRecommendations)

    if search:
        query = query.filter(MovieRecommendations.
                             topic_name.ilike(f'%{search}%'))
    recommendations = query.offset(offset).limit(limit).all()
    return recommendations


def get_recommendation_name(uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    recommendation = session.query(MovieRecommendations).filter_by(
        uuid=uuid).first()
    if recommendation:
        return recommendation.topic_name
    else:
        return None


def set_rec_image(movie_uuid, rec_uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        # Get the IMDb ID from the movie UUID
        imdbid = get_movie_imdb_id_from_uuid(movie_uuid)

        # Get the image URL from the IMDb ID
        img_uri = get_imdb_image_url(imdbid=imdbid)

        movie_rec_search = session.query(MovieRecommendations
                                         ).filter_by(uuid=rec_uuid).first()

        if movie_rec_search:
            movie_rec_search.topic_image = img_uri[0] 
            session.commit()
        else:
            logging.warning(f"No rec found with UUID {rec_uuid}")

    except Exception as e:  # Consider catching more specific exceptions
        logging.error(f"Error occurred: {e}")
        session.rollback()


def get_recommendation_blurb(uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Get the blurb for the given uuid.
    # Return None if no matching record found.
    record = session.query(MovieRecommendations).filter_by(uuid=uuid).first()
    return record.blurb if record else None


def store_blurb_to_recommendation(uuid, blurb):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    recommendation = session.query(MovieRecommendations).filter_by(
        uuid=uuid).first()
    recommendation.blurb = blurb
    session.commit()
    session.close()


def get_movie_imdb_id_from_uuid(uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    result = session.query(MovieData.imdbid).filter_by(uuid=uuid).first()
    if result is not None:
        return result[0]
    else:
        return None


def get_and_store_images(imdbid: str,
                         include_image_language: str = 'en,null',
                         overwrite: bool = False):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_media_processor = MovieMediaProcessor(session)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {THEMOVIEDB_API_KEY}"
    }
    session.close()
    return movie_media_processor.tmdb_request(
        imdbid, 'images', include_image_language, headers,
        overwrite, MovieImage, 5,
        movie_media_processor.process_image_data)


def get_and_store_videos(imdbid: str,
                         language: str = 'en-US',
                         overwrite: bool = False):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_media_processor = MovieMediaProcessor(session)
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {THEMOVIEDB_API_KEY}"
    }
    session.close()
    return movie_media_processor.tmdb_request(
        imdbid, 'videos', language, headers,
        overwrite, MovieVideo, 10,
        movie_media_processor.process_video_data)


def get_imdb_image_url(imdbid: str):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_media_processor = MovieMediaProcessor(session)
    return movie_media_processor.get_movie_image(imdbid)


def get_imdb_video_url(imdbid: str):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_media_processor = MovieMediaProcessor(session)
    return movie_media_processor.get_movie_video(imdbid)


def get_cast_info(movie_uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Query the 'movie_cast' table to get cast_ids
    movie_casts = session.query(MovieCast).filter_by(
        movie_uuid=movie_uuid).all()

    # Initialize dictionary to hold cast info
    cast_info = {'actors': [], 'directors': [], 'writers': []}

    # Loop through the movie_casts list and fill cast_info dict
    for movie_cast in movie_casts:
        # Get cast_name object using cast_id
        cast_name = session.query(CastName).filter_by(
            uuid=movie_cast.cast_id).first()

        if cast_name:
            if cast_name.cast_type == 'actor':
                cast_info['actors'].append(cast_name.name)
            elif cast_name.cast_type == 'director':
                cast_info['directors'].append(cast_name.name)
            elif cast_name.cast_type == 'writer':
                cast_info['writers'].append(cast_name.name)

    return cast_info


def remove_movie_by_uuid(movie_uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        # Get movie data
        movie_data = session.query(MovieData).filter_by(
            uuid=movie_uuid).first()

        if not movie_data:  # if movie_data is None or doesn't exist
            logging.warning(f"Movie with uuid {movie_uuid} not found.")
            return

        imdbid = movie_data.imdbid  # retrieve imdbid from the movie_data

        # Remove movie-cast associations
        session.query(MovieCast).filter(MovieCast.movie_uuid == movie_uuid).delete() # noqa

        # Remove movie-recommendation relations
        session.query(MovieData).filter(MovieData.uuid == movie_uuid).delete()

        # Remove movie images
        session.query(MovieImage).filter(MovieImage.imdbid == imdbid).delete()

        # Remove movie videos
        session.query(MovieVideo).filter(MovieVideo.imdbid == imdbid).delete()

        session.commit()
        logging.info(f'Removed all data related to uuid {movie_uuid} and imdbid {imdbid} Movie Data') # noqa
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()


def replace_movie_uuid(original_uuid, new_uuid):
    """
    Replace the movie_uuid in the MovieRecommendationRelation table.

    Parameters:
    - original_uuid (str): The original UUID that needs to be replaced.
    - new_uuid (str): The new UUID value that will replace the original.

    Returns:
    - int: Number of rows updated.
    """
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        updated_rows = session.query(MovieRecommendationRelation) \
                              .filter(MovieRecommendationRelation.
                                      movie_uuid == original_uuid) \
                              .update({MovieRecommendationRelation.
                                       movie_uuid: new_uuid})

        session.commit()
        logging.info(f'REC UUID {str(original_uuid)} has been replaced with {str(new_uuid)}') # noqa
        return updated_rows
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def is_valid_api_key(api_key):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if api_key is not None:
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        key_record = session.query(APIKey).filter(
            APIKey.hashed_key == hashed_key).first()
        if key_record and key_record.expires_at > datetime.utcnow():
            return True
    return False


def generate_and_store_api_key():
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        # Generate a simple UUID based API key
        api_key = str(uuid.uuid4())
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        # Store the hashed key in the database
        new_key_record = APIKey(hashed_key=hashed_key)
        session.add(new_key_record)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    # Return the raw API key to the user (it's the only time it'll be visible)
    return api_key


# TODO Move
def generte_cast_data(cast_type):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if cast_type in ['actor', 'director']:
        cast = getattr(ContentType, cast_type.upper()).value.upper()
        return generate_movie_cast_homepage_data(session, cast)
    else:
        return None


# TODO Move
def generte_rec_genre_data(recommendation_uuid):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    movie_uuids = fetch_movie_uuids(session, recommendation_uuid)
    genres = fetch_genres_for_movies(session, movie_uuids)
    top_genres = get_top_genres(genres)

    updated_recommendation = update_recommendation(session,
                                                   recommendation_uuid,
                                                   top_genres)

    return updated_recommendation


def generate_genre_homepage_data():
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    genre_list = get_genre(session)  # Assuming this returns a list of genres like ['Action', 'Comedy', 'Drama'] # noqa

    max_retries = 5  # Limit the number of retries
    retries = 0

    while retries < max_retries:
        if genre_list:
            # Select a random genre from the list
            genre_to_search = random.choice(genre_list)
            if genre_to_search.name == 'N/A':
                genre_to_search = random.choice(genre_list)
        else:
            genre_to_search = "Action"  # Default genre if no genres are available # noqa

        recommendations = get_movie_recommendations(session, genre_to_search)
        uuid_list = [rec.uuid for rec in recommendations]

        # If recommendations were found, break out of the loop
        if uuid_list:
            break

        retries += 1

    if uuid_list:  # If recommendations were found
        # clear_previous_featured_content(session, genre_to_search)
        add_featured_content(session, genre_to_search, uuid_list)
    else:
        logging.info("No recommendations found after {} retries".format(
            max_retries))


def fetch_genre_name_by_id(genre_id):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    genre = session.query(Genre).filter(Genre.id == genre_id).first()
    return genre.name if genre else None


def generate_rec_list():
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Get all recommendation_uuids from the database where topic_image is null
    rec_uuids = session.query(MovieRecommendations.uuid).filter(
        or_(MovieRecommendations.topic_image == '',
            MovieRecommendations.topic_image == None) # noqa
            ).all()
    # Get a random movie for each rec_uuid
    for rec_uuid_tuple in rec_uuids:
        rec_uuid = rec_uuid_tuple[0]
        random_movie_form_rec = session.query(MovieData.uuid).join(
            MovieRecommendationRelation,
            MovieRecommendationRelation.movie_uuid == MovieData.uuid
        ).filter(
            MovieRecommendationRelation.recommendation_uuid == rec_uuid
        ).order_by(func.random()).first()
        # Check if random_movie_tuple has a value, extract if it does
        if random_movie_form_rec:
            random_movie = random_movie_form_rec[0]

            # Update the topic_image for the rec_uuid
            set_rec_image(random_movie, rec_uuid)
        else:
            logging.info("No random movie found.")
    logging.info(f"Finished generating {len(rec_uuids)} rec list images.")


def fetch_recommendations(page=1, items_per_page=10):
    recommendations = {}
    # Calculate the offset for pagination
    offset = (page - 1) * items_per_page
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Fetch all records from FeaturedContent, sorted by date
    # and limited for pagination
    featured_contents = session.query(FeaturedContent).options(
        joinedload(FeaturedContent.movie_recommendation)
    ).order_by(FeaturedContent.replaced_at.desc()).slice(
        offset, offset + items_per_page).all()

    for featured_content in featured_contents:
        recommendation = featured_content.movie_recommendation
        group_title = featured_content.group_title

        if group_title not in recommendations:
            recommendations[group_title] = []

        genre_1_name = fetch_genre_name_by_id(recommendation.genre_1)
        genre_2_name = fetch_genre_name_by_id(recommendation.genre_2)
        genre_3_name = fetch_genre_name_by_id(recommendation.genre_3)

        # Convert the DateTime object to a string in MM-DD-YY format
        replaced_at_date = None
        if featured_content.replaced_at:
            replaced_at_date = featured_content.replaced_at.strftime(
                '%m-%d-%y')

        if recommendation.topic_image:
            image_uri = IMAGE_DOMAIN + recommendation.topic_image
        else:
            image_uri = ''
        recommendations[group_title].append({
            "topic_name": recommendation.topic_name,
            "topic_uuid": recommendation.uuid,
            "topic_image": image_uri,
            "genre_1": genre_1_name,
            "genre_2": genre_2_name,
            "genre_3": genre_3_name,
            "replaced_at_date": replaced_at_date,
            "poster_1": recommendation.poster_1,
            "poster_2": recommendation.poster_2,
            "poster_3": recommendation.poster_3,
        })

    return recommendations


def search_movies(query):
    # Performing a case-insensitive search for both topic_name and genre names
    search_results = session.query(
        MovieRecommendations.uuid,
        MovieRecommendations.topic_name
    ).join(
        Genre, or_(
            Genre.id == MovieRecommendations.genre_1,
            Genre.id == MovieRecommendations.genre_2,
        )
    ).filter(
        or_(
            MovieRecommendations.topic_name.ilike(f"%{query}%"),
            Genre.name.ilike(f"%{query}%")
        )
    ).order_by(
        desc(MovieRecommendations.date_generated)
    ).all()

    # Removing duplicates
    unique_results = set()
    filtered_results = []

    for uuid, topic_name in search_results: # noqa
        if (uuid, topic_name) not in unique_results:
            unique_results.add((uuid, topic_name))
            filtered_results.append({"uuid": uuid, "topic_name": topic_name})

    return filtered_results


def set_posters_for_recommendation(recommendation_uuid, top_movies):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        rec = session.query(MovieRecommendations).filter_by(
            uuid=recommendation_uuid).one()

        # If the top_movies list has data, assign posters
        if len(top_movies) > 0:
            rec.poster_1 = top_movies[0]
        if len(top_movies) > 1:
            rec.poster_2 = top_movies[1]
        if len(top_movies) > 2:
            rec.poster_3 = top_movies[2]

        session.commit()
    except Exception as e:
        logging.error(f"Error while updating posters: {e}")
        session.rollback()


def get_random_posters(movie_uuids):
    engine = create_engine(DATABASE_URL, pool_recycle=280)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    try:
        # Query the database for movies with the given UUIDs and 
        # order them by metascore
        movies = session.query(MovieData).filter(MovieData.uuid.in_(
            movie_uuids)).order_by(desc(MovieData.metascore)).all()

        # If there are fewer than 7 movies, use the available movies
        top_movies = movies[:7]

        # Randomly select three movies from the top_movies
        selected_movies = random.sample(top_movies, min(3, len(top_movies)))

        # Extract the posters
        posters = [movie.poster for movie in selected_movies]

        return posters

    finally:
        session.close()
