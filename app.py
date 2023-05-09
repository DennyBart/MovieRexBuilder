import os
from flask import Flask, request
from dotenv import load_dotenv
from movie_rec.services.movie_search import process_request
import logging
from logging.handlers import RotatingFileHandler


load_dotenv()
API_KEY = os.environ['OMDB_API_KEY']
app = Flask(__name__)


# Example: http://127.0.0.1:5000/movie_id?id=tt1392190
@app.route('/movie_id')
def movie_id():
    movie_id = request.args.get('id')
    return process_request('movie_id', movie_id, API_KEY)


# Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019
@app.route('/movie_name')
def movies_name():
    title = request.args.get('title')
    year = request.args.get('year')
    return process_request('movie_name', title, API_KEY, year)


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
