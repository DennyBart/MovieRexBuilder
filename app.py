import os
from flask import Flask, request
from dotenv import load_dotenv
from movie_rec.ai_service.openai_requestor import get_chatgpt_response
from movie_rec.services.movie_search import process_request
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
    # TODO Drop year and search for title and compare to year in request if close then its right
    return process_request('movie_name', title, OMDB_API_KEY, year)


# http://127.0.0.1:5000/ask?movie_type=war
@app.route('/ask')
def ask_chatgpt():
    movie_type = request.args.get('movie_type')
    value = request.args.get('value')
    if value is None:
        input_value = 10
    else:
        input_value = int(value)
        # if input_value < 5 or input_value > 20:
        #     input_value = 5
    combined_message = f"Top {str(value)} {movie_type} movies"
    input_message=[{'role': 'system', 'content': 'You are a movie critic bot that responds with top X movies, with ONLY format Movie: movie_name, Year: year.'},
                 {'role': 'user', 'content': f'List {combined_message} movies'}]
    movie_list = get_chatgpt_response(movie_type, input_value, input_message, OPEN_API_MODEL, OMDB_API_KEY, OPEN_API_KEY)
    return {'movie_list': movie_list}


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
