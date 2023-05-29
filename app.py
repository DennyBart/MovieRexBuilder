import os
from flask import Flask, jsonify, request, session
from dotenv import load_dotenv
from constants import MOVIE_CRITIC_BOT_MESSAGE, TOP_FORMAT, TOP_MOVIES_FORMAT
from movie_rec.ai_service.openai_requestor import get_chatgpt_movie_rec, get_recommendation_titles
from movie_rec.services.models.model import MovieRecommendationsSearchList
from movie_rec.services.movie_search import get_non_generated_movie_topics, process_request, set_movie_topic_to_generated, store_search_titles
import logging
from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker


load_dotenv()
OMDB_API_KEY = os.environ['OMDB_API_KEY']
OPEN_API_KEY = os.environ['OPENAI_API_KEY']
OPEN_API_MODEL = os.environ['OPENAI_API_MODEL']
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
    # TODO Drop year and search for title and compare to year in request if close then its right
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
                     {'role': 'user', 'content': f'List {combined_message} movies'}]
    movie_list = get_chatgpt_movie_rec(movie_type, input_value, 
                                      input_message, OPEN_API_MODEL, 
                                      OMDB_API_KEY, OPEN_API_KEY)
    return {'movie_list': movie_list}


# http://localhost:5000/generate_movie_rec_titles?total=10
@app.route('/generate_movie_rec_titles')
def generate_movie_recommendation_titles():
    generate_total = request.args.get('total')
    if generate_total is None or generate_total == 0 or generate_total == ' ':
        input_value = 10
    else:
        input_value = int(generate_total)
    search_titles = get_recommendation_titles(input_value, OPEN_API_MODEL, OPEN_API_KEY)
    store_search_titles(search_titles)
    return {'message': 'success'}


# http://localhost:5000/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST
@app.route('/provide_movie_rec_titles', methods=['POST'])
def provide_movie_recommendation_titles():
    search_titles = request.json.get('titles')

    if search_titles is None or not isinstance(search_titles, list):
        return 'Invalid search titles data', 400
    store_search_titles(search_titles)

    return 'Search titles stored successfully'


# http://localhost:5000/generate_recs_in_db?limit=2
@app.route('/generate_recs_in_db')
def generate_recs_from_list():
    limit = request.args.get('limit')
    print(f'limit: {limit}')
    if limit is None or limit == 0 or limit == ' ':
        limit = 10
    count = 0
    value = 10
    titles = get_non_generated_movie_topics()
    print(titles)
    processed_titles = []
    for title in titles:
        if count == limit:
            break
        count += 1
        processed_titles.append(title[0])
        movie_type = title[0]  # Extract the title from the tuple
        if 'documentaries' in movie_type.lower() or 'movies' in movie_type.lower():
            combined_message = TOP_FORMAT.format(value, movie_type)
        else:
            combined_message = TOP_MOVIES_FORMAT.format(value, movie_type)
        input_message = [{'role': 'system', 'content': MOVIE_CRITIC_BOT_MESSAGE},
                     {'role': 'user', 'content': f'List {combined_message} movies'}]
        movie_list = get_chatgpt_movie_rec(movie_type, value, 
                                      input_message, OPEN_API_MODEL, 
                                      OMDB_API_KEY, OPEN_API_KEY)
        set_movie_topic_to_generated(movie_type)
    
    return {'movie_list': processed_titles}

    

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
            RotatingFileHandler(log_file, mode='a', maxBytes=max_log_size, backupCount=backup_count)
        ]
    )


if __name__ == '__main__':
    setup_logging()
    app.run(debug=True)
