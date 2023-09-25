import datetime
import os
import uuid
import math
from typing import List
from flask import (
    Flask,
    jsonify,
    request,
    render_template,
)
from constants import (
    GENERATE_PAGE_BLURB,
    GENERATION_REC_TITLES,
    MOVIE_CRITIC_BOT_MESSAGE,
    TOP_FORMAT,
    TOP_MOVIES_FORMAT,
    GENERATION_REC_QUESTION,
    LOG_FILE,
)
from movie_rec.data_converter import format_recommendation_list
from movie_rec.openai_requestor import (
    generate_openai_response,
    get_chatgpt_movie_rec,
    get_existing_recommendations,
    get_limit_and_value,
    process_titles
)
from movie_rec.movie_search import (
    check_db,
    fetch_recommendations,
    generate_genre_homepage_data,
    generate_rec_list,
    generte_cast_data,
    generte_rec_genre_data,
    get_and_store_images,
    get_and_store_videos,
    get_movie_imdb_id_from_uuid,
    get_non_generated_movie_topics,
    get_recommendation_blurb,
    get_recommendation_name,
    get_recommendations,
    is_valid_api_key,
    process_request,
    query_movie_by_uuid,
    remove_movie_by_uuid,
    replace_movie_uuid,
    search_movies,
    store_blurb_to_recommendation,
    store_search_titles
)
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_MODEL = os.getenv('OPENAI_API_MODEL')
OPENAI_API_MODEL_RECOMENDATIONS = os.getenv('OPENAI_API_MODEL_RECOMENDATIONS')
app = Flask(__name__)


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def get_device_type():
    user_agent = request.headers.get('User-Agent', '').lower()

    if "iphone" in user_agent:
        return 'mobile'
    elif "android" in user_agent:
        return 'mobile'
    else:
        return 'desktop'


@app.route('/')
def hello():
    page = request.args.get('page', default=1, type=int)
    user_agent = get_device_type()
    if page < 1:
        page = 1
    recommendations = fetch_recommendations(page=page)
    recommendations['page'] = page

    return render_template(f'{user_agent}/index.html',
                           recommendations=recommendations)


@app.route('/web/rec/<uuid>')
def display_recommendation(uuid):
    device_type = get_device_type()
    try:
        processed_recs = process_recommendation_by_uuid(uuid)
        if processed_recs is None:
            raise ValueError("No recommendations found for given UUID.")

        rec_movie_list = processed_recs.get_json()

        response_blurb = process_recommendation_blurb(uuid)
        if response_blurb is not None:
            rec_blurb = response_blurb.get_json()
        else:
            rec_blurb = None

        return render_template(f'{device_type}/rec.html',
                               rec_movie_list=rec_movie_list,
                               rec_blurb=rec_blurb)
    except (SQLAlchemyError, AttributeError, ValueError) as e:
        # Log the error for debugging purposes
        print(f"Error: {e}")

        # Render the error template
        return render_template(f'{device_type}/error.html'), 500


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter missing."}), 400

    results = search_movies(query.lower())
    return jsonify(results)


# API Endpoints
@app.route('/api/gen_data')
def gen_data():
    gen_rec_list = request.args.get('gen_rec_list', default=False, type=bool)
    if gen_rec_list:
        generate_rec_list()
    generte_cast_data('actor')
    generte_cast_data('director')
    generate_genre_homepage_data()
    return f"Data generated: {datetime.datetime.now()}"


# Example: http://127.0.0.1:5000/api/get_movie_id?id=tt1392190
@app.route('/api/get_movie_id')
def movie_by_id():
    movie_id = request.args.get('id')
    if not movie_id:
        return jsonify({'error': 'Invalid movie id'}), 400
    movie_data = process_request(
        request_type='movie_id',
        identifier=movie_id,
        api_key=OMDB_API_KEY)
    if movie_data:
        return jsonify(movie_data)
    else:
        return f'ID:{movie_id} Not Found', 404


# Example: http://127.0.0.1:5000/api/get_movie_uuid?uuid=88841ced-35c5-4828-be5c-f0cfe4732192 # noqa
@app.route('/api/get_movie_uuid')
def movie_by_uuid():
    movie_uuid = request.args.get('uuid')
    if not movie_uuid:
        return jsonify({'error': 'Invalid movie uuid'}), 400

    try:
        movie_data = query_movie_by_uuid(movie_uuid).to_dict()
        data_output = format_recommendation_list([movie_data],
                                                 cast=True,
                                                 plot=True,
                                                 media=True,
                                                 info=True)
        return jsonify(data_output)
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': 'Movie uuid not found'}), 404


# Example: http://127.0.0.1:5000/api/get_movie_name?title=Goodfellas&year=1990
@app.route('/api/get_movie_name')
def movies_name():
    title = request.args.get('title')
    year = request.args.get('year')
    if title is None:
        return jsonify({'error': 'Invalid movie title'}), 400
    if year is None:
        return jsonify({'error': 'Invalid movie year'}), 400
    # TODO Drop year and search for title and compare to year in request if close then its right # noqa
    response = process_request(
        request_type='movie_name',
        identifier=title,
        api_key=OMDB_API_KEY,
        year=year)
    if response:
        return jsonify(response)
    else:
        return f'Title:{title} Year:{year} Not Found', 404


# http://127.0.0.1:5000/api/add_recommendation?movie_type=war&value=10
@app.route('/api/add_recommendation')
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
    movie_list, rec_uuid = get_chatgpt_movie_rec(movie_type,
                                                 value,
                                                 input_message,
                                                 OPENAI_API_MODEL,
                                                 OMDB_API_KEY,
                                                 OPENAI_API_KEY)
    return jsonify(movie_list)


# http://localhost:5000/api/process_movie_rec_titles?total=25
@app.route('/api/process_movie_rec_titles')
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
            api_model=OPENAI_API_MODEL_RECOMENDATIONS,
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


# http://localhost:5000/api/generate_rec_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131&limit=10 # noqa
@app.route('/api/generate_rec_blurb')
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


# TODO - Refactor this 
def contains_items(s: str, items: List[str]) -> bool:
    return sum(item in s for item in items) >= 3


# TODO - Refactor this
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


# http://localhost:5000/api/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST - # noqa
@app.route('/api/provide_movie_rec_titles', methods=['POST'])
def provide_movie_recommendation_titles():
    search_titles = request.json.get('titles')

    if search_titles is None or not isinstance(search_titles, list):
        return 'Invalid search titles data', 400
    sotred_title = store_search_titles(search_titles)

    return {'generated_titles': sotred_title}


# http://localhost:5000/api/generate_recs_in_db?limit=10&value=10&blurb=True # noqa
# Limit: How many movies per recommendation
# Value: How many recommendations to generate
@app.route('/api/generate_recs_in_db')
def generate_recs_in_db():
    blurb = request.args.get('blurb', type=bool, default=False)
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
    # Generate blurb for each recommendation
    if blurb:
        # Before: generate_recommendation_blurb(title['uuid'], 10)
        for title_dict in processed_titles:
            for key, rec_uuid in title_dict.items():
                generate_recommendation_blurb(rec_uuid, 10)

    if processed_titles == []:
        return {'completed_topic_list': processed_titles, 'message': 'No topics to process in list'} # noqa
    else:
        return {'completed_topic_list': processed_titles}


# http://localhost:5000/list_recommendations?search=Comedy&blurb=True&limit=10&offset=0 # noqa
@app.route('/api/list_recommendations')
def list_reccomendations():
    search = request.args.get('search')
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)
    blurb = request.args.get('blurb', type=bool, default=False)

    recommendations = get_recommendations(
        search=search, limit=limit, offset=offset
    )

    results = [recommendation.to_dict() for recommendation in recommendations]
    for result in results:
        if not blurb and 'blurb' in result:
            del result['blurb']

    return jsonify(results)


# http://localhost:5000/api/get_recommendation?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131?limit=10 # noqa
@app.route('/api/get_recommendation_by_uuid')
def get_recommendation_by_uuid():
    uuid = request.args.get('uuid')
    if uuid is None:
        return "Sorry! Not found"
    return process_recommendation_by_uuid(uuid)


def process_recommendation_by_uuid(uuid):
    try:
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
            # Format json data
            # TODO Return in a better format
            return jsonify(existing_recommendations)
        else:
            return {'error': 'No recommendations found'}, 404
    except ValueError as e:
        return {'error': str(e)}, 400


# http://127.0.0.1:5000/api/get_recommendation_by_title?search=Character Driven Movies # noqa
@app.route('/api/get_recommendation_by_title')
def get_recommendation_by_title():
    try:
        rec_title = request.args.get('search')
        # Check if rec_title is valid
        if rec_title is None:
            return 'Missing recommendation title', 400
        if not rec_title.strip():
            return 'Invalid recommendation title', 400
        value = request.args.get('limit', type=int, default=50)
        existing_recommendations = get_existing_recommendations(
            value=value,
            movie_type=rec_title
            )
        if existing_recommendations:
            # Format json data
            return jsonify(existing_recommendations)
        else:
            return {'error': 'No recommendations found'}, 404
    except ValueError as e:
        return {'error': str(e)}, 400


# http://localhost:5000/api/get_recommendation_blurb?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f # noqa
@app.route('/api/get_recommendation_blurb')
def get_recommendations_blurb():
    # get uuid from the request
    uuid = request.args.get('uuid')

    # check if uuid is valid
    if uuid is None:
        return 'Missing uuid', 400
    if not is_valid_uuid(uuid):
        return 'Invalid uuid', 400
    process_rec = process_recommendation_blurb(uuid)
    if process_rec is None:
        return {'No recommendation found for this UUID'}, 404
    else:
        return process_rec


def process_recommendation_blurb(uuid):
    # remove leading and trailing whitespace from uuid
    uuid = uuid.strip()

    # get recommendation from the database
    recommendation_blurb = get_recommendation_blurb(uuid=uuid)

    # check if recommendation is found
    if recommendation_blurb is not None:
        logging.debug(recommendation_blurb)
        return jsonify({'blurb': recommendation_blurb})
    else:
        return None


# http://localhost:5000/api/get_movie_videos?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=True # noqa
@app.route('/api/get_movie_videos')
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


# http://localhost:5000/api/get_movie_images?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=true # noqa
@app.route('/api/get_movie_images')
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


# Example: http://127.0.0.1:5000/api/replace_movie_id?imbdid=tt1392190&replace_uuid=88841ced-35c5-4828-be5c-f0cfe4732192 # noqa
@app.route('/api/replace_movie_id')
def replace_movie_by_id():
    api_key = request.headers.get('x-api-key')
    if not is_valid_api_key(api_key):
        return jsonify(error="Invalid or missing API key (x-api-key)"), 403
    movie_id = request.args.get('imbdid')
    replace_uuid = request.args.get('replace_uuid')
    validate_uuid = is_valid_uuid(replace_uuid)
    if not validate_uuid:
        return jsonify({'error': 'Invalid uuid'}), 400
    if not movie_id or not replace_uuid:
        return jsonify({'error': 'Invalid movie id or uuid'}), 400
    movie_data = process_request(
        request_type='movie_id',
        identifier=movie_id,
        api_key=OMDB_API_KEY)
    if movie_data:
        replace_movie_uuid(original_uuid=replace_uuid,
                           new_uuid=movie_data['uuid'])
        remove_movie_by_uuid(replace_uuid)
        return jsonify(movie_data)
    else:
        return f'ID:{movie_id} Not Found', 404


@app.route('/api/generate_recommendations_genre')
def generate_recommendations_genre():
    recommendation_uuid = request.args.get('recommendation_uuid')

    if not recommendation_uuid:
        return jsonify({"error": "recommendation_uuid is required"}), 400

    gen_rec_data = generte_rec_genre_data(recommendation_uuid)

    if not gen_rec_data:
        return jsonify({"error": "No such recommendation exists"}), 404

    return jsonify(gen_rec_data.to_dict())


# TODO: Secure this endpoint for generation
# Example: http://127.0.0.1:5000/api/generate_api_key
# @app.route('/api/generate_api_key')
# def generate_api_key():
#     data = generate_and_store_api_key()
#     return jsonify(data), 200


@app.route('/api/get_homepage_data')
def frontpage_reccomendations():
    page = request.args.get('page', default=1, type=int)
    if page < 1:
        page = 1
    recommendations = fetch_recommendations(page=page)
    recommendations['page'] = page
    return jsonify(recommendations)


def setup_logging():
    log_file = LOG_FILE
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


setup_logging()
check_db()

if __name__ == '__main__':
    app.run(debug=True)
