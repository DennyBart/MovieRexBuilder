import os
from flask import (
    Flask,
    request
)
from dotenv import load_dotenv
from constants import MOVIE_CRITIC_BOT_MESSAGE, TOP_FORMAT, TOP_MOVIES_FORMAT
from movie_rec.ai_service.openai_requestor import (
    get_chatgpt_movie_rec,
    get_recommendation_titles
)
from movie_rec.services.movie_search import (
    get_non_generated_movie_topics,
    process_request,
    set_movie_topic_to_generated,
    store_search_titles
)
import logging
from logging.handlers import RotatingFileHandler

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
    movie_list = get_chatgpt_movie_rec(movie_type,
                                       input_value, 
                                       input_message,
                                       OPEN_API_MODEL, 
                                       OMDB_API_KEY,
                                       OPEN_API_KEY)
    return {'movie_list': movie_list}


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
        OPEN_API_MODEL,
        OPEN_API_KEY
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


# http://localhost:5000/generate_recs_in_db?limit=2
@app.route('/generate_recs_in_db')
def generate_recs_from_list():
    logging.info('Generating recommendations from list')
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
        return {'error': str(e)}, 400

    try:
        titles = get_non_generated_movie_topics()
    except ValueError as e:
        return {'error': str(e)}, 400  # Return error message with 400 status
    processed_titles = []
    count = 0
    for title in titles:
        logging.info(f'Generating {value} - {title}')
        if count == limit:
            return {'completed_topic_list Limit': processed_titles}
        movie_type = title[0]  # Extract the title from the tuple
        if 'documentaries' in movie_type.lower() or 'movies' in movie_type.lower(): # noqa
            combined_message = TOP_FORMAT.format(value, movie_type)
        else:
            combined_message = TOP_MOVIES_FORMAT.format(value, movie_type)
        input_message = [
            {'role': 'system',
             'content': MOVIE_CRITIC_BOT_MESSAGE}, {'role': 'user',
                                                    'content':
                                                    f'List {combined_message}'
                                                    }]
        try:
            get_chatgpt_movie_rec(movie_type, value,
                                  input_message,
                                  OPEN_API_MODEL,
                                  OMDB_API_KEY,
                                  OPEN_API_KEY
                                  )
            processed_titles.append(title[0])
        except ValueError as e:
            logging.error(f'Error processing {title} - {str(e)}')
            continue
        set_movie_topic_to_generated(movie_type)
        logging.info(f'Completed Processing {title}')
        count += 1
    if processed_titles == []:
        return {'completed_topic_list': processed_titles,
                'message': 'No topics to process in list'}
    else:
        return {'completed_topic_list': processed_titles}


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
    setup_logging()
    app.run(debug=True)
