import os
import uuid
import math
from typing import List
from flask import (
    Flask,
    jsonify,
    request
)
from dotenv import load_dotenv
from constants import (
    GENERATE_PAGE_BLURB,
    GENERATION_REC_TITLES,
    MOVIE_CRITIC_BOT_MESSAGE,
    TOP_FORMAT,
    TOP_MOVIES_FORMAT,
    GENERATION_REC_QUESTION
)
from movie_rec.openai_requestor import (
    generate_openai_response,
    get_chatgpt_movie_rec,
    get_existing_recommendations,
    get_limit_and_value,
    process_titles
)
from movie_rec.movie_search import (
    check_db,
    get_and_store_images,
    get_and_store_videos,
    get_movie_imdb_id_from_uuid,
    get_non_generated_movie_topics,
    get_recommendation_blurb,
    get_recommendation_name,
    get_recommendations,
    process_request,
    store_blurb_to_recommendation,
    store_search_titles
)
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
OMDB_API_KEY = os.environ['OMDB_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
OPENAI_API_MODEL = os.environ['OPENAI_API_MODEL']
app = Flask(__name__)


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


# Example: http://127.0.0.1:5000/movie_id?id=tt1392190
@app.route('/movie_id')
def movie_id():
    movie_id = request.args.get('id')
    if movie_id is None:
        return jsonify({'error': 'Invalid movie id'}), 400
    return process_request('movie_id', movie_id, OMDB_API_KEY)


# Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019
@app.route('/movie_name')
def movies_name():
    title = request.args.get('title')
    year = request.args.get('year')
    if title is None:
        return jsonify({'error': 'Invalid movie title'}), 400
    if year is None:
        return jsonify({'error': 'Invalid movie year'}), 400
    # TODO Drop year and search for title and compare to year in request if close then its right # noqa
    return process_request('movie_name', title, OMDB_API_KEY, year)


# http://127.0.0.1:5000/create_recommendation?movie_type=war&value=10
@app.route('/create_recommendation')
def ask_chatgpt():
    movie_type = request.args.get('movie_type')
    value = request.args.get('value')
    if value is None or value == 0 or value == ' ':
        input_value = 20
    else:
        input_value = int(value)
    if movie_type is None:
        return jsonify({'error': 'Invalid movie type or value'}), 400
    return generate_rec_movie_list(
        movie_type=movie_type,
        value=input_value)


def generate_rec_movie_list(value, uuid=None, movie_type=None):
    if movie_type is None and uuid is None:
        return {'error': 'Movie type or uuid arg missing'}, 400
    if movie_type and uuid:
        return {'error': 'Movie type and uuid arg present'}, 400
    if uuid:
        logging.info(f"Recommendation UUID: {uuid}")
        existing_recommendations = get_existing_recommendations(
            uuid=uuid)
        if existing_recommendations:
            return jsonify(existing_recommendations)
        else:
            return {'error': 'UUID not found'}, 400
    if 'documentaries' in movie_type.lower() or 'movies' in movie_type.lower():
        combined_message = TOP_FORMAT.format(value, movie_type)
    else:
        combined_message = TOP_MOVIES_FORMAT.format(value, movie_type)
    input_message = [{'role': 'system', 'content': MOVIE_CRITIC_BOT_MESSAGE},
                     {'role': 'user', 'content': f'List {combined_message} '
                      f'movies'}]
    existing_recommendations = get_existing_recommendations(
        value=value,
        movie_type=movie_type
        )
    logging.info(f"Existing recommendations: {existing_recommendations}")
    if existing_recommendations:
        return jsonify(existing_recommendations)
    movie_list = get_chatgpt_movie_rec(movie_type,
                                       value,
                                       input_message,
                                       OPENAI_API_MODEL,
                                       OMDB_API_KEY,
                                       OPENAI_API_KEY)
    return jsonify(movie_list)


# http://localhost:5000/generate_movie_rec_titles?total=25
@app.route('/generate_movie_rec_titles')
def generate_movie_recommendation_titles():
    generate_total = int(request.args.get('total'))
    if generate_total is None or generate_total < 25 or generate_total == ' ':
        return {'error': 'Invalid total - minimium is 25'}, 400
    else:
        total_request = math.ceil(generate_total / 25)
        if total_request > 10:
            return {'error': 'Total request cannot be more than 250'}, 400
    ai_question = GENERATION_REC_QUESTION
    openai_message = [
        {'role': 'system', 'content': GENERATION_REC_TITLES},
        {'role': 'user', 'content': ai_question}
    ]
    total_generated_titles = []
    for i in range(total_request):
        generated_titles = generate_openai_response(
            api_model=OPENAI_API_MODEL,
            openai_api_key=OPENAI_API_KEY,
            input_message=openai_message
        )
        generated_message = generated_titles['choices'][0
                                                        ]['message']['content']
        gen_lines = generated_message.split("\n")
        gen_items = [line.split(". ")
                     [1] for line in gen_lines if ". " in line]
        if gen_items is None:
            logging.info("No titles generated")
        else:
            store_search_titles(gen_items)
            total_generated_titles.extend(gen_items)
            logging.info("Total generated titles: "
                         f"{len(total_generated_titles)}")
    return {'generated_titles': total_generated_titles}


# http://localhost:5000/generate_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131&limit=10 # noqa
@app.route('/generate_blurb')
def generate_blurb():
    uuid = request.args.get('uuid')
    limit = request.args.get('limit')

    # check if uuid is valid
    if uuid is None:
        return 'Missing uuid', 400
    if not is_valid_uuid(uuid):
        return 'Invalid uuid', 400
    if limit is None or limit == 0 or limit == ' ':
        limit = 10

    return generate_recommendation_blurb(uuid, (limit))


def contains_items(s: str, items: List[str]) -> bool:
    return sum(item in s for item in items) >= 3


def generate_recommendation_blurb(uuid, limit: int):
    item_list = []
    try:
        recommendation_title = get_recommendation_name(uuid=uuid)
        if recommendation_title is None:
            return {'error': 'No titles found'}, 400
        existing_recommendation = get_existing_recommendations(uuid=uuid)
        for recommendation in existing_recommendation:
            item_list.append(recommendation['title'])
    except ValueError as e:
        return {'error': str(e)}, 400
    if not item_list:
        return {'error': 'No titles found'}, 400
    if item_list and len(item_list) < limit:
        limit = len(item_list)
    limited_item_list = item_list[:limit]
    ai_question = 'Why are the following ' \
        f'{recommendation_title} ({", ".join(limited_item_list)})'
    openai_message = [
        {'role': 'system', 'content': GENERATE_PAGE_BLURB},
        {'role': 'user', 'content': ai_question}
    ]

    max_tries = 3
    logging.info(f"Generating blurb for {recommendation_title} {uuid}")
    for i in range(max_tries):
        blurb = generate_openai_response(
            api_model=OPENAI_API_MODEL,
            openai_api_key=OPENAI_API_KEY,
            input_message=openai_message
        )
        blurb_message = blurb['choices'][0]['message']['content']
        if contains_items(blurb_message,
                          limited_item_list) or i == max_tries - 1:
            store_blurb_to_recommendation(uuid, blurb_message)
            logging.info(f"{recommendation_title} {uuid} - "
                         f"Blurb message stored: {blurb_message} - "
                         f"Attempt: {i + 1}")
            return {'recommendation_title': recommendation_title,
                    'blurb_heading': blurb_message}

    return {'error': 'Unable to generate a suitable blurb '
            'after maximum attempts'}


# http://localhost:5000/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST - # noqa
@app.route('/provide_movie_rec_titles', methods=['POST'])
def provide_movie_recommendation_titles():
    search_titles = request.json.get('titles')

    if search_titles is None or not isinstance(search_titles, list):
        return 'Invalid search titles data', 400
    sotred_title = store_search_titles(search_titles)

    return {'generated_titles': sotred_title}


# http://localhost:5000/generate_recs_in_db?limit=10&value=10
@app.route('/generate_recs_in_db')
def generate_recs_from_list():
    logging.info('Generating recommendations from list')
    limit, value = get_limit_and_value(request)

    try:
        titles = get_non_generated_movie_topics()
    except ValueError as e:
        return {'error': str(e)}, 400

    processed_titles = process_titles(
        titles,
        limit,
        value,
        OPENAI_API_MODEL,
        OMDB_API_KEY,
        OPENAI_API_KEY
    )

    if processed_titles == []:
        return {'completed_topic_list': processed_titles, 'message': 'No topics to process in list'} # noqa
    else:
        return {'completed_topic_list': processed_titles}


# http://localhost:5000/recommendations_list?search=Comedy
@app.route('/recommendations_list')
def recommendations_list():
    search = request.args.get('search')
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)

    recommendations = get_recommendations(
        search=search, limit=limit, offset=offset
    )

    results = [recommendation.to_dict() for recommendation in recommendations]

    return jsonify(results)


# http://localhost:5000/get_recommendation?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131?limit=10 # noqa
@app.route('/get_recommendation')
def get_recommendations_by_uuid():
    # Todo add movie_type to search
    try:
        uuid = request.args.get('uuid')
        # check if uuid is valid
        if uuid is None:
            return 'Missing uuid', 400
        if not is_valid_uuid(uuid):
            return 'Invalid uuid', 400
        value = request.args.get('limit', type=int, default=50)
        existing_recommendations = get_existing_recommendations(
            value=value,
            uuid=uuid
            )
        if existing_recommendations:
            return jsonify(existing_recommendations)
        else:
            return {'error': 'No recommendations found'}, 400
    except ValueError as e:
        return {'error': str(e)}, 400


# http://localhost:5000/get_recommendation_blurb?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f # noqa
@app.route('/get_recommendation_blurb')
def get_recommendations_blurb():
    # get uuid from the request
    uuid = request.args.get('uuid')

    # check if uuid is valid
    if uuid is None:
        return 'Missing uuid', 400
    if not is_valid_uuid(uuid):
        return 'Invalid uuid', 400

    # remove leading and trailing whitespace from uuid
    uuid = uuid.strip()

    # get recommendation from the database
    recommendation_blurb = get_recommendation_blurb(uuid=uuid)

    # check if recommendation is found
    if recommendation_blurb is not None:
        logging.debug(recommendation_blurb)
        return jsonify({'blurb': recommendation_blurb})
    else:
        return 'No recommendation found for this UUID', 404


# http://localhost:5000/get_movie_videos?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=True # noqa
@app.route('/get_movie_videos')
def get_movie_videos():
    # get uuid from the request
    uuid = request.args.get('uuid')
    overwrite = request.args.get('overwrite', default=False, type=bool)
    if overwrite is None:
        overwrite = False

    # check if uuid is valid
    if uuid is None:
        return 'Missing uuid', 400
    if not is_valid_uuid(uuid):
        return 'Invalid uuid', 400

    # remove leading and trailing whitespace from uuid
    uuid = uuid.strip()

    movie_imdb_id = get_movie_imdb_id_from_uuid(uuid=uuid)

    # check if recommendation is found
    if movie_imdb_id is not None:
        response = get_and_store_videos(movie_imdb_id, overwrite=overwrite)
        return jsonify({'message': f'{response}'})
    else:
        return 'No recommendation found for this UUID', 404


# http://localhost:5000/get_movie_images?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=true # noqa
@app.route('/get_movie_images')
def get_movie_images():
    # get uuid from the request
    uuid = request.args.get('uuid')
    overwrite = request.args.get('overwrite', default=False, type=bool)
    if overwrite is None:
        overwrite = False

    # check if uuid is valid
    if uuid is None:
        return 'Missing uuid', 400
    if not is_valid_uuid(uuid):
        return 'Invalid uuid', 400

    # remove leading and trailing whitespace from uuid
    uuid = uuid.strip()

    movie_imdb_id = get_movie_imdb_id_from_uuid(uuid=uuid)

    # check if recommendation is found
    if movie_imdb_id is not None:
        response = get_and_store_images(movie_imdb_id, overwrite=overwrite)
        return jsonify({'message': f'{response}'})
    else:
        return 'No recommendation found for this UUID', 404


def setup_logging():
    log_file = 'logs/app.log'
    max_log_size = 10 * 1024 * 1024  # 10 MB
    backup_count = 5

    # Create the logs directory if it doesn't exist
    logs_dir = os.path.dirname(log_file)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(log_file, mode='a',
                                maxBytes=max_log_size,
                                backupCount=backup_count)
        ]
    )


if __name__ == '__main__':
    check_db()
    setup_logging()
    app.run(debug=True)
