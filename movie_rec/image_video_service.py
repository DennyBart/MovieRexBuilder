from constants import TMDB_API_RATE_CALLS, TMDB_API_RATE_TIME
import requests
from ratelimit import limits
from movie_rec.models import (
    MovieData,
    MovieImage,
    MovieVideo
)
import logging
from dateutil import parser


class MovieMediaProcessor:
    def __init__(self, session):
        self.session = session

    @limits(calls=TMDB_API_RATE_CALLS, period=TMDB_API_RATE_TIME)
    def tmdb_call_api(self, url, headers):
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response

    def tmdb_request(self, imdbid: str, endpoint: str,
                     include_language: str = 'en,null',
                     headers: dict = None, overwrite: bool = False,
                     entity=None, hard_limit=None, process_func=None):

        # Check if the entity is already stored in the database
        is_data_in_db = self._is_entity_stored(imdbid, entity, overwrite)
        if is_data_in_db and not overwrite:
            logging.info(f"Entity for movie with IMDB ID {imdbid} is "
                         "already stored. Skipping request")
            return "Entity already stored."
        elif is_data_in_db and overwrite:
            logging.info(f"Removing existing entity for movie "
                         f"with IMDB ID {imdbid}")
            self.session.query(entity).filter_by(imdbid=imdbid).delete()
            self.session.commit()
            self.session.close()

        url = self._generate_url(imdbid, endpoint, include_language)
        response = self._make_api_call(url, headers)

        if response and response.status_code == 200:
            data = response.json()
            self._process_data(
                imdbid, data, entity, overwrite,
                endpoint, hard_limit, process_func)
        else:
            logging.info(f"{endpoint.capitalize()} OMDB request "
                         f"{imdbid} failed")
            return f"{endpoint.capitalize()} Request Not Found"

        self.session.close()
        return f"{endpoint.capitalize()} Request Generated and Stored."

    def get_movie_image(self, imdbid, file_path_only=True):
        # If file_path_only option is True, query only for the file_paths
        if file_path_only:
            movie_images = self.session.query(MovieImage.file_path).filter_by(
                imdbid=imdbid).all()
            return [img.file_path for img in movie_images]
        else:
            # Otherwise, query for the full movie_images objects
            movie_images = self.session.query(MovieImage).filter_by(
                imdbid=imdbid).all()
            return movie_images

    def get_movie_video(self, imdbid, key_and_name=True):
        # If key_and_name option is True, query only for the keys and names
        if key_and_name:
            movie_videos = self.session.query(MovieVideo.key, MovieVideo.name
                                              ).filter_by(imdbid=imdbid).all()
            return movie_videos
        else:
            # Otherwise, query for the full movie_videos objects
            movie_videos = self.session.query(MovieVideo
                                              ).filter_by(imdbid=imdbid).all()
            return movie_videos


    def _is_entity_stored(self, imdbid, entity, overwrite):
        logging.debug(f"Checking if entity for movie with IMDB "
                      f"ID {imdbid} is already stored")
        movie_exists = self.session.query(entity).filter_by(
            imdbid=imdbid).first() is not None
        if movie_exists and overwrite:
            logging.info(f"Overwrite is set to True. Deleting "
                         f"existing entity for movie with IMDB ID {imdbid}")
            return True
        return False

    def _generate_url(self, imdbid, endpoint, include_language):
        return f"https://api.themoviedb.org/3/movie/{imdbid}/{endpoint}?include_image_language={include_language}" # noqa

    def _make_api_call(self, url, headers):
        count = 0
        max_attempts = 3
        while count < max_attempts:
            logging.info(f"Making API call to {url}")
            response = self.tmdb_call_api(url, headers=headers)
            if response is not None:
                break
            count += 1
        return response

    def _process_data(self, imdbid, data, entity, overwrite, endpoint,
                      hard_limit, process_func, trailer=True):
        logging.info(f"Adding {endpoint} for movie with IMDB ID {imdbid}")
        item_list = data.get('backdrops', []) if endpoint == 'images' else data.get('results', []) # noqa
        if endpoint == 'videos':
            # Filter out trailers in type and name
            item_list_trailer = [item for item in item_list if 'trailer' in item['type'].lower()] # noqa
            if item_list_trailer == []:
                logging.info(f"No Trailer found for {imdbid}. "
                             f"Trying to find Trailer in name")
                item_list_trailer = [item for item in item_list if 'trailer' in item['name'].lower()] # noqa
            item_list = item_list_trailer
        self._add_items_to_db(imdbid, item_list, hard_limit, process_func, endpoint) # noqa

    def _add_items_to_db(self, imdbid, item_list,
                         hard_limit, process_func, endpoint):
        counter = 0
        for item in item_list:
            if counter == hard_limit:
                break
            movie_data = self.session.query(MovieData).filter_by(imdbid=imdbid).first() # noqa
            if movie_data:
                processed_item = process_func(item, movie_data)
                self.session.add(processed_item)
                counter += 1

        self._log_items_added(counter, endpoint, imdbid)
        self.session.commit()
        self.session.close()

    def _log_items_added(self, counter, endpoint, imdbid):
        if counter > 0:
            logging.info(f"Adding {endpoint} {imdbid} to database")
        else:
            logging.info(f"No {endpoint} found for {imdbid}")

    @staticmethod
    def process_image_data(backdrop, movie_data):
        if backdrop['file_path'].startswith('/'):
            backdrop['file_path'] = backdrop['file_path'][1:]
        return MovieImage(
            aspect_ratio=backdrop['aspect_ratio'],
            height=backdrop['height'],
            iso_639_1=backdrop['iso_639_1'],
            file_path=backdrop['file_path'],
            vote_average=backdrop['vote_average'],
            vote_count=backdrop['vote_count'],
            width=backdrop['width'],
            imdbid=movie_data.imdbid
        )

    @staticmethod
    def process_video_data(video, movie_data):
        return MovieVideo(
            id=video['id'],
            iso_639_1=video['iso_639_1'],
            iso_3166_1=video['iso_3166_1'],
            name=video['name'],
            key=video['key'],
            site=video['site'],
            size=video['size'],
            type=video['type'],
            official=video['official'],
            published_at=parser.parse(video['published_at']),
            imdbid=movie_data.imdbid
        )
