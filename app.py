import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from movie_rec.services.movie_search import process_request

load_dotenv()
API_KEY = os.environ['OMDB_API_KEY']

app = Flask(__name__)

# Example: http://127.0.0.1:5000/movie_id?id=tt1392190
@app.route('/movie_id')
def movie_id():
    movie_id = request.args.get('id')
    return process_request('movie_id', movie_id, API_KEY)

# Example: http://127.0.0.1:5000/movies?title=Swallow&year=2019"
@app.route('/movie_name')
def movies_name():
    title = request.args.get('title')
    return process_request('movie_name', title, API_KEY)

if __name__ == '__main__':
    app.run(debug=True)
