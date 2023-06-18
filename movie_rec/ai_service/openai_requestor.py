import datetime
import re
import pandas as pd
import uuid
import openai
import logging
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from movie_rec.services.models.model import (
    MovieRecommendationRelation,
    MovieRecommendations,
    Base
)
from constants import (
    MOVIE_CRITIC_BOT_MESSAGE,
    TOP_FORMAT,
    TOP_MOVIES_FORMAT
)
from movie_rec.services.movie_search import (
    process_request,
    query_movie_by_uuid,
    set_movie_topic_to_generated
)
from movie_rec.utils import UUIDEncoder
import time

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

                # Remove leading and trailing white space
                movie = movie.strip()

                # Extract only the year as an integer
                # Search for a four digit number representing the year
                year = re.search(r'\d{4}', year)
                if year:
                    year = int(year.group())  # Convert the year to integer
                else:
                    year = None  # No valid year found

                # Append the movie data as a dictionary
                movie_data.append({"Index": index,
                                   "Movie": movie,
                                   "Year": year})

        except ValueError as e:
            print(f"An error occurred while processing line: "
                  f"{line}. Error: {e}")
            logging.error("An error occurred while processing "
                          "line: {line}. Error: {e}".format)
    if not movie_data:
        return None

    return movie_data


def fetch_movie_details(movies, omdb_api_key, rec_topic=None):
    movie_list = []
    for movie in movies:
        movie_details = process_request('movie_name',
                                        movie['Movie'],
                                        omdb_api_key, movie['Year'],
                                        rec_topic)
        if movie_details is not None:
            data = json.loads(movie_details.data)
            movie_uuid = data.get('uuid')
            movie_list.append(movie_uuid)
            # TODO - Add movie details to logging
            logging.info(f"Movie Details: {movie_uuid}")
    return movie_list


def store_movie_recommendation(movie_list, movie_type, total):
    unique_movie_list = list(set(movie_list))

    rec_uuid = uuid.uuid4()
    new_recommendations = MovieRecommendations(
        uuid=rec_uuid,
        topic_name=str(movie_type),
        count=len(unique_movie_list),
        date_generated=datetime.datetime.now(),
        casting_id=None
    )
    session.add(new_recommendations)
    session.commit()
    for movie_uuid in unique_movie_list:
        # add movie uuid and recomendation uuid to MovieRecommendation
        new_movie_recommendation = MovieRecommendationRelation(
            recommendation_uuid=rec_uuid,
            movie_uuid=movie_uuid
        )
        session.add(new_movie_recommendation)
    logging.info(f"New Movie Recommendation: {movie_type}")
    session.commit()


def get_existing_recommendations(value=10, movie_type=None, uuid=None) -> str:
    # No need to check if value is None, use default parameters in function definition.
    try:
        value = int(value)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        return None

    # Improved readability for uuid and movie_type check.
    if uuid:
        rec_uuid, rec_count = check_movie_recommendation(uuid=uuid)
    elif movie_type:
        rec_uuid, rec_count = check_movie_recommendation(search_term=movie_type)
    else:
        logging.error("Both uuid and movie_type cannot be None.")
        return None

    if rec_count is None:
        # Item not found
        return None

    if value > rec_count:
        value = rec_count

    # Use list comprehension for output_list.
    movie_list = get_related_movies(rec_uuid)
    output_list = [query_movie_by_uuid(movie_uuid).to_dict() 
                   for i, movie_uuid in enumerate(movie_list) if i < value]

    logging.info(f"Movie Recommendation UUID: {rec_uuid}")
    logging.info(f"Movie List: {output_list}")

    return output_list


def get_new_recommendations(api_model: str, openai_api_key: str,
                            movie_type: str, value: int,
                            input_message: list) -> str:
    openai.api_key = openai_api_key
    logging.info(f"OpenAI Request Message: {input_message}")
    retries = 0
    while retries < 3:
        try:
            response = openai.ChatCompletion.create(
                model=api_model,
                messages=input_message
            )
            break  # Break out of the loop if the request is successful
        except openai.error.RateLimitError:
            time.sleep(5)  # Wait for 5 seconds before retrying
            retries += 1
        except openai.error.Timeout as e:
            logging.error(f"Request timed out: {e}")
            retries += 1
            if retries < 3:
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                return "Request timed out after multiple retries."

    combined_message = f"Top {str(value)} {movie_type}"
    logging.info(f"OpenAI Request Message: "
                 f"{response['choices'][0]['message']}")
    resp_message = response['choices'][0]['message']['content']
    # TODO DO MONDAY - Prevent multiple same movie in list
    movie_data = create_movie_list(resp_message)
    # Check if duplicate data in movie_data
    if movie_data is None:
        return f'{combined_message} is not supported.'
    unique_combinations = set()
    new_movie_data = []
    for movie in movie_data:
        combination = f"{movie['Movie']}-{movie['Year']}"
        if combination not in unique_combinations:
            unique_combinations.add(combination)
            new_movie_data.append(movie)

    new_values = len(unique_combinations)

    if len(new_movie_data) < value:
        logging.info(f'Not all movies were found. '
                     f'Only {len(new_movie_data)} movies were found.')
        return f'Only {len(new_movie_data)} movies were found.'

    return new_movie_data, new_values


def get_recommendation_titles(api_model: str,
                              openai_api_key: str,
                              value: int,
                              input_message: list) -> str:
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=api_model,
        messages=input_message
    )
    return response['choices'][0]['message']['content']


def process_new_recommendations(movie_data: list,
                                omdb_api_key: str,
                                movie_type: str,
                                total: int) -> str:
    df = pd.DataFrame(movie_data, columns=['Movie', 'Year'])
    resp_json = df.to_json(orient='records')
    movies = json.loads(resp_json)

    movie_list = fetch_movie_details(movies, omdb_api_key, movie_type)
    store_movie_recommendation(movie_list, movie_type, total)
    return movie_list


def get_chatgpt_movie_rec(movie_type: str,
                          value: int,
                          input_message: list,
                          api_model: str,
                          omdb_api_key: str,
                          openai_api_key: str) -> str:
    movie_list_size_limit = 10
    existing_recommendations = get_existing_recommendations(
        value=value,
        movie_type=movie_type
        )
    if existing_recommendations is not None:
        return existing_recommendations
    num_attempts = 0
    while num_attempts < 3:
        try:
            new_recommendations, rec_total = get_new_recommendations(
                api_model, openai_api_key, movie_type, value, input_message)
            # Rerun if less than 10 movies found
            if len(new_recommendations) < movie_list_size_limit:
                raise ValueError(f"Not all movies were found. "
                                 f"Only {len(new_recommendations)} movies "
                                 f"were found.")
            elif new_recommendations is not None:
                return process_new_recommendations(
                    new_recommendations, omdb_api_key, movie_type, rec_total)
        except ValueError:
            num_attempts += 1

    return "Error: Failed to retrieve movie recommendations."


def check_movie_recommendation(search_term=None, uuid=None, value=None):
    # Raise an exception if both search_term and uuid are None
    if search_term is None and uuid is None:
        raise ValueError("At least one of search_term or uuid must be provided.")

    # Initialize movie_recommendation
    movie_recommendation = None

    # If uuid is provided, prioritize it over search_term
    if uuid is not None:
        movie_recommendation = (
            session.query(MovieRecommendations)
            .filter(MovieRecommendations.uuid == uuid)
            .first()
        )
    else:
        # Use '%' as a wildcard to find similar topic names
        movie_recommendation = (
            session.query(MovieRecommendations)
            .filter(MovieRecommendations.topic_name.ilike(f"%{search_term}%"))
            # .filter(MovieRecommendations.count == value)
            .first()
        )

    if movie_recommendation is None:
        return None, None
    else:
        return movie_recommendation.uuid, movie_recommendation.count


def get_related_movies(recommendation_uuid):
    # Query the relation table to get all associated movie UUIDs
    movie_relations = session.query(MovieRecommendationRelation).filter_by(
        recommendation_uuid=recommendation_uuid).all()

    # Create a list to hold all the movie_uuid values
    related_movies = [relation.movie_uuid for relation in movie_relations]

    return related_movies


def get_limit_and_value(request):
    try:
        limit = request.args.get('limit')
        value = request.args.get('value')
        if value is None or value.strip() == '':
            value = 10
        else:
            value = int(value)

        if limit is None or limit.strip() == '':
            limit = 100
        else:
            limit = int(limit)
    except ValueError as e:
        raise ValueError(str(e)) from None

    return limit, value


def process_titles(titles, limit, value, OPENAI_API_MODEL, OMDB_API_KEY, OPENAI_API_KEY):
    processed_titles = []
    count = 0

    for title in titles:
        logging.info(f'Generating {value} - {title}')
        if count == limit:
            return processed_titles

        movie_type = title[0]  # Extract the title from the tuple
        if 'documentaries' in movie_type.lower() or 'movies' in movie_type.lower(): # noqa
            combined_message = TOP_FORMAT.format(value, movie_type)
        else:
            combined_message = TOP_MOVIES_FORMAT.format(value, movie_type)
        input_message = [
            {'role': 'system', 'content': MOVIE_CRITIC_BOT_MESSAGE},
            {'role': 'user', 'content': f'List {combined_message}'}
        ]
        try:
            get_chatgpt_movie_rec(
                movie_type,
                value,
                input_message,
                OPENAI_API_MODEL,
                OMDB_API_KEY,
                OPENAI_API_KEY
            )
            processed_titles.append(title[0])
        except ValueError as e:
            logging.error(f'Error processing {title} - {str(e)}')
            continue

        set_movie_topic_to_generated(movie_type)
        logging.info(f'Completed Processing {title}')
        count += 1

    return processed_titles
