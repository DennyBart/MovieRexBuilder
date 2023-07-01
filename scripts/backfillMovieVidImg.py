import sys
sys.path.append('C:/Users/denis/Dev/MovieRexBuilder')  # Your project root directory

import time
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from movie_rec.movie_search import (
    get_and_store_images,
    get_and_store_videos)
from movie_rec.models import MovieData

# Modify this with your actual SQLAlchemy connection string
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
session = Session(engine)

# Set the rate limit (10 per second => 0.1s delay)
total_time = 10  # Total time in seconds
num_requests = 35  # Number of requests

RATE_LIMIT = total_time / num_requests
RETRY_LIMIT = 3

# Setup logging
success_logger = logging.getLogger('success')
success_handler = logging.FileHandler('successful.log')
success_logger.addHandler(success_handler)

failure_logger = logging.getLogger('failure')
failure_handler = logging.FileHandler('failed.log')
failure_logger.addHandler(failure_handler)


def process_movie(movie):
    """Process a single movie and handle exceptions"""
    for _ in range(RETRY_LIMIT):
        try:
            video_response = get_and_store_videos(movie.imdbid, overwrite=False)
            output =[]
            if video_response == 'Video Request not found':
                output.append(f"Video {movie.imdbid} not found")
            logging.info(f'Successfully processed videos for movie with id {movie.imdbid}. Response: {video_response}')
            success_logger.info(f'Successfully processed videos for movie with id {movie.imdbid}. Response: {video_response}')

            time.sleep(RATE_LIMIT)

            image_response = get_and_store_images(movie.imdbid, overwrite=False)
            if image_response == 'Image Request not found':
                output.append(f"Image {movie.imdbid} not found")
            logging.info(f'Successfully processed images for movie with id {movie.imdbid}. Response: {image_response}')
            success_logger.info(f'Successfully processed images for movie with id {movie.imdbid}. Response: {image_response}')

            # if there is an error with either video or image processing
            if output:
                with open("failed.log", "r") as file:
                    lines = file.readlines()

                # If the movie's UUID is not in the file, write it
                if str(movie.uuid) + '\n' not in lines:
                    with open("failed.log", "a") as file:  # use "a" for appending to the file
                        file.write(f'{str(movie.uuid)}\n')

            # If both calls were successful, remove the movie's UUID from the file
            else:
                with open("uuids.txt", "r") as file:
                    lines = file.readlines()
                with open("uuids.txt", "w") as file:
                    for line in lines:
                        if line.strip("\n") != str(movie.uuid):
                            file.write(line)
            break  # Break the loop if processing was successful
        except Exception as e:
            failure_logger.error(f"Error processing movie with id {movie.imdbid}. Error message: {e}")
            time.sleep(RATE_LIMIT)  # Wait before retrying

# Get all movies (or one movie) from the DB
movies = session.query(MovieData).all()

# Write the UUIDs of movies to a file, only if the file does not already exist
if not os.path.exists("uuids.txt"):
    with open("uuids.txt", "w") as file:
        for movie in movies:
            file.write(f'{movie.uuid}\n')

# Process each movie from the file
with open("uuids.txt", "r") as file:
    uuids = file.readlines()

for uuid in uuids:
    movie = session.query(MovieData).filter(MovieData.uuid == uuid.strip()).first()
    if movie is not None:
        process_movie(movie)
    time.sleep(RATE_LIMIT)

# Close the DB session
session.close()
