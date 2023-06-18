import os
from flask import (
    Flask,
    jsonify,
    request
)
from dotenv import load_dotenv
from constants import MOVIE_CRITIC_BOT_MESSAGE, TOP_FORMAT, TOP_MOVIES_FORMAT
from movie_rec.ai_service.openai_requestor import (
    get_chatgpt_movie_rec,
    get_existing_recommendations,
    get_limit_and_value,
    get_recommendation_titles,
    get_related_movies,
    process_titles
)
from movie_rec.services.movie_search import (
    check_db,
    get_non_generated_movie_topics,
    get_recommendations,
    process_request,
    store_search_titles
)
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
OMDB_API_KEY = os.environ['OMDB_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
OPENAI_API_MODEL = os.environ['OPENAI_API_MODEL']
app = Flask(__name__)


# Example: http://127.0.0.1:5000/movie_id?id=tt1392190
@app.route('/movie_id')
def movie_id():
    movie_id = request.args.get('id')
    return process_request('movie_id', movie_id, OMDB_API_KEY)


# Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019
@app.route('/movie_name')
def movies_name():
    title = request.args.get('title')
    year = request.args.get('year')
    # TODO Drop year and search for title and compare to year in request if close then its right # noqa
    return process_request('movie_name', title, OMDB_API_KEY, year)


# http://127.0.0.1:5000/recommendations?movie_type=war&value=10
@app.route('/recommendations')
def ask_chatgpt():
    movie_type = request.args.get('movie_type')
    value = request.args.get('value')
    if value is None or value == 0 or value == ' ':
        input_value = 10
    else:
        input_value = int(value)
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
    print(f"Existing recommendations: {existing_recommendations}")
    if existing_recommendations:
        return jsonify(existing_recommendations)
    movie_list = get_chatgpt_movie_rec(movie_type,
                                       input_value, 
                                       input_message,
                                       OPENAI_API_MODEL, 
                                       OMDB_API_KEY,
                                       OPENAI_API_KEY)
    return jsonify(movie_list)


# http://localhost:5000/generate_movie_rec_titles?total=10
@app.route('/generate_movie_rec_titles')
def generate_movie_recommendation_titles():
    generate_total = request.args.get('total')
    if generate_total is None or generate_total == 0 or generate_total == ' ':
        input_value = 10
    else:
        input_value = int(generate_total)
    search_titles = get_recommendation_titles(
        input_value,
        OPENAI_API_MODEL,
        OPENAI_API_KEY
    )
    stored_title = store_search_titles(search_titles)
    return {'generated_titles': stored_title}


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

    recommendations = get_recommendations(search=search, limit=limit)

    # Now turn our results into a list of dictionaries so we can return them as JSON
    results = [recommendation.to_dict() for recommendation in recommendations]

    return jsonify(results)


# http://localhost:5000/get_recommendation?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131?limit=10
@app.route('/get_recommendation')
def get_recommendations_by_uuid():
    # Todo add movie_type to search
    try:
        uuid = request.args.get('uuid')
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
