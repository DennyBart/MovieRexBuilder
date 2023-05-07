import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from movie_rec.services.movie_search import process_request

load_dotenv()
API_KEY = os.environ['OMDB_API_KEY']

app = Flask(__name__)

@app.route('/movie_id')
def movie_id():
    movie_id = request.args.get('id')
    return process_request('movie_id', movie_id, API_KEY)

@app.route('/movies_name')
def movies_name():
    title = request.args.get('title')
    return process_request('movies_name', title, API_KEY)

if __name__ == '__main__':
    app.run(debug=True)
