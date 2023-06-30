# MovieRex

This Movie Recommendation API is a Flask-based web application that provides a range of recomendation services for movies. The application interacts with artificial intelligence (OpenAI's GPT API) to generate movie recommendations based on popular topics such as ***Best Inspirational Movies for a Pick-Me-Up***. The service uses the GPT API to generate the list of recommendation titles, the movies for each title, an introduction to the recommendation title and also query additional APIs to store movie data. After the data is stored any request to the API will server the data from the local DB.

***Built with a commitment to flexibility and user experience, the API has several key features:***

**Intelligent Recommendations:** At the core of this application is its powerful recommendation system. The system uses the user defined OpenAI's GPT model (gpt-3.5-turbo, gpt-4, etc) to generate suggestions based on user-provided parameters. It's able to parse and understand complex requests, such as asking for the best animated films of the last decade or cult classics that deal with specific themes. The application also creates a summary of the movie recomendation and some details about those movies.

**Movie Search:** Users can search for movies by ID or name. This function makes it easy to locate specific movies in the database, streamlining the user's navigation experience.

**Movie Details Retrieval:** The application interfaces with the OMDB API and TMDB to retrieve additional details about the movies. This adds a layer of depth to the recommendations by providing more information about each suggested title, including actors, directors, genre, trailers, images and more.


## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Endpoints](#endpoints)
    - [Search Movie by ID](#search-movie-by-id)
    - [Search Movie by Name](#search-movie-by-name)
    - [Create Movie Recommendation](#create-movie-recommendation)
    - [Generate Movie Recommendation Titles](#generate-movie-recommendation-titles)
    - [Generate Blurb for Recommendations](#generate-blurb-for-recommendations)
    - [Provide Movie Recommendation Titles](#provide-movie-recommendation-titles)
    - [Generate Recommendations from Database](#generate-recommendations-from-database)
    - [Recommendations List](#recommendations-list)
    - [Get Recommendations by UUID](#get-recommendations-by-uuid)
    - [Get Recommendation Blurb](#get-recommendation-blurb)
    - [Get Movie Videos](#get-movie-videos)
    - [Get Movie Images](#get-movie-images)
- [Logging](#logging)
- [ToDo](#todo)
- [License](#license)



## Requirements

Before running the Movie Recommendation API, make sure you have the following:

- OpenAI API Key: You will need an API key from OpenAI to use their GPT model for generating movie recommendations. You can sign up for an API key on the [OpenAI website](https://openai.com/).
- OMDB API Key: You will need an account on OMDB (Open Movie Database) to access movie information and search for movies by ID or name. You can create an account on the [OMDB website](https://www.omdbapi.com/) and obtain an API key.
- TMDB API Key: The Movie DB (TMDB) API key can be generated on the site after creating an account [TMDB](https://www.themoviedb.org/). A rate limit is advised for TMDB and it is implemented in the applicaiton for up to date information on the rate limit see [TMDB API Rate Limit](https://developer.themoviedb.org/docs/rate-limiting)
- PSQL Database: The application requires a PostgreSQL (PSQL) database to store movie recommendation titles and other relevant data. Make sure you have a running PSQL database and the necessary credentials to connect to it. You can install PostgreSQL from the official [PostgreSQL website](https://www.postgresql.org/).


Once you have obtained the OpenAI API key, OMDB API key, and set up the PSQL database, you can proceed with the setup and configuration steps mentioned in the previous section.

## Setup

To set up and run the Movie Recommendation API locally, follow these steps:

1. Clone the repository: `https://github.com/DennyBart/MovieRexBuilder.git`
2. Navigate to the project directory: `cd movie-recommendation-api`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Set the required environment variables:
    - `OMDB_API_KEY` - Your API key for the OMDB API
    - `OPENAI_API_KEY` - Your API key for the OpenAI API
    - `THEMOVIEDB_API_KEY` - Your API ker for TMDB
    - `OPENAI_API_MODEL` - The name or ID of the OpenAI GPT model to use [OpenAI API Models] (https://platform.openai.com/docs/models)
    - `DATABASE_URL` - Database location
5. Run the application: `python app.py`
6. The API will be available at `http://localhost:5000`

Note: Make sure to replace the environment variable values with your own API keys and model information.

## Endpoints

The API provides the following endpoints:
## API Overview

### Search Movie by ID

- Endpoint: `/movie_id`
- Method: GET
- Parameters:
    - `id` (required) - the IMDBID of the movie to search
- Description: Retrieves movie information by its ID using the OMDB API.
- Example: http://127.0.0.1:5000/movie_id?id=tt1392190

### Search Movie by Name

- Endpoint: `/movie_name`
- Method: GET
- Parameters:
    - `title` (required),
    - `year` (required) - the title and the year of the movie to search
- Description: Retrieves movie information by its name and year using the OMDB API.
- Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019

### Create Movie Recommendation

- Endpoint: `/create_recommendation`
- Method: GET
- Parameters:
    - `movie_type` (required),
    - `value` (required) - the type of the movie and a value for how many movies will be in the reccomendation
- Description: Generates a list of recommended movies based on the type. Like "Top 10 War Movies"
- Example: http://127.0.0.1:5000/create_recommendation?movie_type=war&value=10

### Generate Movie Recommendation Titles

- Endpoint: `/generate_movie_rec_titles`
- Method: GET
- Parameters:
    - `total` (required) - the total number of movie recommendation titles to generate
- Description: Generates a specified number of movie recommendation titles.
- Example: http://localhost:5000/generate_movie_rec_titles?total=10

### Generate Blurb for Recommendations

- Endpoint: `/generate_blurb`
- Method: GET
- Parameters:
    - `uuid` (required),
    - `limit` (optional, default=10) - the UUID of the recommendation and the number of movies to generate blurbs for
- Description: Generates a blurb for the movie recommendations associated with the provided UUID. A blurb is an intorduction to the movie list and this can go into detail about some of the movies in the list.
- Example: http://localhost:5000/generate_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131&limit=10

### Provide Movie Recommendation Titles

- Endpoint: `/provide_movie_rec_titles`
- Method: POST
- Data:
    - `{ "titles": ["Top War Movies", "Best Movies to Watch Hungover"] }` - a JSON array of titles
- Description: Store a list of movie recommendation titles to the database.
- Example: http://localhost:5000/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST

### Generate Recommendations from Database

- Endpoint: `/generate_recs_in_db`
- Method: GET
- Parameters:
    - `limit` (optional),
    - `value` (optional, default=20) - the number of recommendations to generate from the DB and the value parameter for how many movies in the recomendation
- Description: Generates movie recommendations from existing data in the database.
- Example: http://localhost:5000/generate_recs_in_db?limit=10&value=20

### Recommendations List

- Endpoint: `/recommendations_list`
- Method: GET
- Parameters:
    - `search` (optional),
    `limit` (optional), `offset` (optional) - search keyword, number of recommendations to retrieve, and offset for pagination
- Description: Retrieves a list of non generated movie recommendations from the database and process the titles. A limit can be passed in to stop after X items are generated.
- Example: http://localhost:5000/recommendations_list?search=Comedy

### Get Recommendations by UUID

- Endpoint: `/get_recommendation`
- Method: GET
- Parameters:
    - `uuid` (required),
    - `limit` (optional) - the UUID of the recomendation and the number of movies to retrieve
- Description: Retrieves a list of movie recommendations by UUID.
- Example: http://localhost:5000/get_recommendation?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131?limit=10

### Get Recommendation Blurb

- Endpoint: `/get_recommendation_blurb`
- Method: GET
- Parameters:
    - `uuid` (required) - the UUID of the recomendation uuid
- Description: Retrieves the blurb of a movie recommendation.
- Example: http://localhost:5000/get_recommendation_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131

### Get Movie Videos

- Endpoint: `/get_movie_videos`
- Method: GET
- Parameters: 
    - `uuid` (required) - the UUID of the movie
    - `overwrite` (optional, defaults to `False`) - a boolean value indicating whether to overwrite existing video data for the movie.
- Description: Retrieves and stores videos related to a movie identified by the provided UUID. If the `overwrite` parameter is set to `True`, it will overwrite any existing video data for this movie. (NOTE: A rate limit of 40 requests per 10 seconds is enabled to prevent overloading the TMDB API.)
- Example: http://localhost:5000/get_movie_videos?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=True

### Get Movie Images

- Endpoint: `/get_movie_images`
- Method: GET
- Parameters: 
    - `uuid` (required) - the UUID of the movie
    - `overwrite` (optional, defaults to `False`) - a boolean value indicating whether to overwrite existing image data for the movie.
- Description: Retrieves and stores images related to a movie identified by the provided UUID. If the `overwrite` parameter is set to `True`, it will overwrite any existing image data for this movie. (NOTE: A rate limit of 40 requests per 10 seconds is enabled to prevent overloading the TMDB API.)
- Example: http://localhost:5000/get_movie_images?uuid=3773a5d9-abea-49b2-8751-4b51bf4fe35f&overwrite=True

## Logging

The application logs are stored in the `logs/app.log` file. The log file is rotated when it reaches a size of 10 MB, and a maximum of 5 backup log files are kept.

## ToDo
- Improved logging of Errors and Info
- Add support for other API providers
- Add caching service to flask
- Track errors for missing movies
- Add support for MySql database

## License

This project is licensed under the [MIT License](LICENSE).
