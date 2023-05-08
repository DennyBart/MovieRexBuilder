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

def get_cast(name=str, cast_type=str):
    cast_name = session.query(CastName).filter(CastName.name == name, CastName.cast_type == cast_type).first()
    return cast_name if cast_name else None


def process_request(request_type=str, identifier=str, year=None, api_key=str):
    print(f'APIIIIII{api_key}')
    if request_type == 'movie_id':
        movie = session.query(MovieData).filter(MovieData.imdbid == identifier).first()
        if not movie:
            movie_data = search_movie_by_id(identifier, api_key)
            if movie_data:
                # Create a list of actors and remove the 'actors' key from the movie_data dictionary
                actors = movie_data['Actors'].split(', ')
                directors = movie_data['Director'].split(', ')
                writers = movie_data['Writer'].split(', ')
                del movie_data['Response']
                movie_data = {
                    key.lower(): value
                    for key, value in movie_data.items()
                    if key.lower() != 'actors' and key.lower() != 'director' and key.lower() != 'writer'
                }
                movie_data['uuid'] = uuid.uuid4()
                # print(f'DATA: {movie_data}')
                # print(f'DIRECTORS: {directors}')
                # print(f'ACTORS: {actors}')
                # print(f'Writers: {writers}')



                # Create a new MovieData instance using the modified movie_data dictionary
                new_movie = MovieData(**movie_data)

                # Iterate through the actors, create CastName instances, and add them to the new_movie.cast relationship through MovieCast
                for actor in actors:
                    cast_name = get_cast(actor, 'actor')
                    if cast_name is None:
                        cast_name = CastName(name=actor, cast_type='actor', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for director in directors:
                    cast_name = get_cast(director, 'director')
                    if cast_name is None:
                        cast_name = CastName(name=director, cast_type='director', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for writer in writers:
                    cast_name = get_cast(writer, 'writer')
                    if cast_name is None:
                        cast_name = CastName(name=writer, cast_type='writer', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)

                # Add the new_movie instance to the database session and commit the changes
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                return jsonify({"error": "Movie ID not found"}), 404

        print(f"Movie DICT: {movie.to_dict()}")
        return jsonify(movie.title)

    elif request_type == 'movie_name':
        movie = session.query(MovieData).filter(MovieData.title == identifier).first()
        print(movie)
        if not movie:
            print('Movie not found')
            movie_data = search_movie_by_title(identifier, year, api_key)
            if movie_data:
                # Create a list of actors and remove the 'actors' key from the movie_data dictionary
                actors = movie_data['Actors'].split(', ')
                directors = movie_data['Director'].split(', ')
                writers = movie_data['Writer'].split(', ')
                del movie_data['Response']
                movie_data = {
                    key.lower(): value
                    for key, value in movie_data.items()
                    if key.lower() != 'actors' and key.lower() != 'director' and key.lower() != 'writer'
                }
                movie_data['uuid'] = uuid.uuid4()

                # Create a new MovieData instance using the modified movie_data dictionary
                new_movie = MovieData(**movie_data)

                # Iterate through the actors, create CastName instances, and add them to the new_movie.cast relationship through MovieCast
                for actor in actors:
                    cast_name = get_cast(actor, 'actor')
                    if cast_name is None:
                        cast_name = CastName(name=actor, cast_type='actor', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for director in directors:
                    cast_name = get_cast(director, 'director')
                    if cast_name is None:
                        cast_name = CastName(name=director, cast_type='director', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)
                for writer in writers:
                    cast_name = get_cast(writer, 'writer')
                    if cast_name is None:
                        cast_name = CastName(name=writer, cast_type='writer', uuid=uuid.uuid4())
                    movie_cast = MovieCast(movie=new_movie, cast=cast_name)
                    new_movie.cast.append(movie_cast)

                # Add the new_movie instance to the database session and commit the changes
                session.add(new_movie)
                session.commit()
                return jsonify(movie_data)
            else:
                return jsonify({"error": "Movie Name not found"}), 404

        return jsonify(f'Title:{movie.title} - Year: {movie.year}')


def search_movie_by_id(movie_id, api_key):
    url = f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}"
    print(f'URL: {url}')
    response = requests.get(url)
    print(f'ID_REPSONSE: {response.json()}')
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None

# "http://127.0.0.1:5000/movies?title=Swallow&year=2019"
def search_movie_by_title(title, year, api_key):
    print(f'API_KEY:')
    url = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={api_key}"
    print(url)
    response = requests.get(url)
    print(response.json())
    data = response.json()

    if data.get('Response') == 'True':
        return data
    else:
        return None
