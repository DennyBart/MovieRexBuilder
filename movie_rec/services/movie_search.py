import uuid
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests

from movie_rec.services.models.model import Base, CastName, MovieCast, MovieData

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_database"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def process_request(request_type, identifier, api_key):
    if request_type == 'movie_id':
        movie = session.query(MovieData).filter(MovieData.imdb_id == identifier).first()

        if not movie:
            movie_data = search_movie_by_id(identifier, api_key)
            if movie_data:
                # Create a list of actors and remove the 'actors' key from the movie_data dictionary
                actors = movie_data['Actors'].split(', ')
                directors = movie_data['Director'].split(', ')
                writers = movie_data['Writer'].split(', ')
                del movie_data['Response']
                movie_data = {
                    key.lower().replace('imdbrating', 'imdb_rating').replace('imdbvotes', 'imdb_votes').replace('imdbid', 'imdb_id').replace('type', 'movie_type').replace('dvd', 'dvd_release').replace('boxoffice', 'box_office'): value
                    for key, value in movie_data.items()
                    if key.lower() != 'actors' and key.lower() != 'director' and key.lower() != 'writer'
                }
                movie_data['uuid'] = uuid.uuid4()
                print(f'DATA: {movie_data}')
                print(f'DIRECTORS: {directors}')
                print(f'ACTORS: {actors}')
                print(f'Writers: {writers}')



                # Create a new MovieData instance using the modified movie_data dictionary
                new_movie = MovieData(**movie_data)

                # Iterate through the actors, create CastName instances, and add them to the new_movie.cast relationship through MovieCast
                for actor in actors:
                    cast_name = CastName(name=actor, cast_type='actor', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for director in directors:
                    cast_name = CastName(name=director, cast_type='director', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for writer in writers:
                    cast_name = CastName(name=writer, cast_type='writer', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)

                # Add the new_movie instance to the database session and commit the changes
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                return jsonify({"error": "Movie not found"}), 404

        return jsonify(movie.to_dict())

    elif request_type == 'movies_name':
        movie = session.query(MovieData).filter(MovieData.title == identifier).first()

        if not movie:
            movie_data = search_movie_by_title(identifier, api_key)
            if movie_data:
                # Create a list of actors and remove the 'actors' key from the movie_data dictionary
                actors = movie_data['actors'].split(', ')
                movie_data = {key.lower(): value for key, value in movie_data.items() if key.lower() != 'actors'}

                # Create a new MovieData instance using the modified movie_data dictionary
                new_movie = MovieData(**movie_data)

                # Iterate through the actors, create CastName instances, and add them to the new_movie.cast relationship through MovieCast
                for actor in actors:
                    cast_name = CastName(name=actor)
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)

                # Add the new_movie instance to the database session and commit the changes
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                return jsonify({"error": "Movie not found"}), 404

        return jsonify(movie.to_dict())


def search_movie_by_id(movie_id, api_key):
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None


def search_movie_by_title(title, api_key):
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None
