# Movie Recommendation API

The Movie Recommendation API is a Flask-based web application that provides movie-related functionalities such as searching movies by ID or name, generating movie recommendations, and storing movie titles for recommendation generation.

## Requirements

Before running the Movie Recommendation API, make sure you have the following:

- OpenAI API Key: You will need an API key from OpenAI to use their GPT model for generating movie recommendations. You can sign up for an API key on the [OpenAI website](https://openai.com/).
- OMDB Account: You will need an account on OMDB (Open Movie Database) to access movie information and search for movies by ID or name. You can create an account on the [OMDB website](https://www.omdbapi.com/) and obtain an API key.
- PSQL Database: The application requires a PostgreSQL (PSQL) database to store movie recommendation titles and other relevant data. Make sure you have a running PSQL database and the necessary credentials to connect to it. You can install PostgreSQL from the official [PostgreSQL website](https://www.postgresql.org/).

Once you have obtained the OpenAI API key, OMDB API key, and set up the PSQL database, you can proceed with the setup and configuration steps mentioned in the previous section.

## Endpoints

The API provides the following endpoints:
## API Overview

### 1. Search Movie by ID

- Endpoint: `/movie_id`
- Method: GET
- Parameters: `id` (required) - the IMDBID of the movie to search
- Description: Retrieves movie information by its ID using the OMDB API.
- Example: http://127.0.0.1:5000/movie_id?id=tt1392190

### 2. Search Movie by Name

- Endpoint: `/movie_name`
- Method: GET
- Parameters: `title` (required), `year` (required) - the title and the year of the movie to search
- Description: Retrieves movie information by its name and year using the OMDB API.
- Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019

### 3. Create Movie Recommendation

- Endpoint: `/create_recommendation`
- Method: GET
- Parameters: `movie_type` (required), `value` (required) - the type of the movie and a value for how many movies will be in the reccomendation
- Description: Generates a list of recommended movies based on the type.
- Example: http://127.0.0.1:5000/create_recommendation?movie_type=war&value=10

### 4. Generate Movie Recommendation Titles

- Endpoint: `/generate_movie_rec_titles`
- Method: GET
- Parameters: `total` (required) - the total number of movie recommendation titles to generate
- Description: Generates a specified number of movie recommendation titles.
- Example: http://localhost:5000/generate_movie_rec_titles?total=10

### 5. Generate Blurb for Recommendations

- Endpoint: `/generate_blurb`
- Method: GET
- Parameters: `uuid` (required), `limit` (optional, default=10) - the UUID of the recommendation and the number of movies to generate blurbs for
- Description: Generates a blurb for the movie recommendations associated with the provided UUID.
- Example: http://localhost:5000/generate_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131&limit=10 

### 6. Provide Movie Recommendation Titles

- Endpoint: `/provide_movie_rec_titles`
- Method: POST
- Data: `{ "titles": ["title1", "title2"] }` - a JSON array of titles
- Description: Store provided movie recommendation titles to the database.
- Example: http://localhost:5000/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST

### 7. Generate Recommendations from Database

- Endpoint: `/generate_recs_in_db`
- Method: GET
- Parameters: `limit` (optional), `value` (optional, default=20) - the number of recommendations to generate from the DB and the value parameter for how many movies in the recomendation
- Description: Generates movie recommendations from existing data in the database.
- Example: http://localhost:5000/generate_recs_in_db?limit=10&value=20

### 8. Recommendations List

- Endpoint: `/recommendations_list`
- Method: GET
- Parameters: `search` (optional), `limit` (optional), `offset` (optional) - search keyword, number of recommendations to retrieve, and offset for pagination
- Description: Retrieves a list of movie recommendations from the database.
- Example: http://localhost:5000/recommendations_list?search=Comedy

### 9. Get Recommendations by UUID

- Endpoint: `/get_recommendation`
- Method: GET
- Parameters: `uuid` (required), `limit` (optional) - the UUID of the recomendation and the number of movies to retrieve
- Description: Retrieves a list of movie recommendations by UUID.
- Example: http://localhost:5000/get_recommendation?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131?limit=10

### 10. Get Recommendation Blurb

- Endpoint: `/get_recommendation_blurb`
- Method: GET
- Parameters: `uuid` (required) - the UUID of the recomendation uuid
- Description: Retrieves the blurb of a movie recommendation.
- Example: http://localhost:5000/get_recommendation_blurb?uuid=8d2c1f01-ef70-46f6-b8a4-f8db0f44b131


## Setup

To set up and run the Movie Recommendation API locally, follow these steps:

1. Clone the repository: `https://github.com/DennyBart/MovieRexBuilder.git`
2. Navigate to the project directory: `cd movie-recommendation-api`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Set the required environment variables:
    - `OMDB_API_KEY` - Your API key for the OMDB API
    - `OPENAI_API_KEY` - Your API key for the OpenAI API
    - `OPENAI_API_MODEL` - The name or ID of the OpenAI GPT model to use
    - `DATABASE_URL` - Database location
5. Run the application: `python app.py`
6. The API will be available at `http://localhost:5000`

Note: Make sure to replace the environment variable values with your own API keys and model information.

## Logging

The application logs are stored in the `logs/app.log` file. The log file is rotated when it reaches a size of 10 MB, and a maximum of 5 backup log files are kept.

## TODO
Improved logging of Errors

## License

This project is licensed under the [MIT License](LICENSE).
