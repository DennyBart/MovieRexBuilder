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

### 1. Search Movie by ID

- Endpoint: `/movie_id`
- Method: GET
- Parameters: `id` (required) - the ID of the movie to search
- Description: Retrieves movie information by its ID using the OMDB API.
- Example: http://127.0.0.1:5000/movie_id?id=tt1392190

### 2. Search Movie by Name

- Endpoint: `/movie_name`
- Method: GET
- Parameters: 
    - `title` (required) - the title of the movie to search
    - `year` (optional) - the release year of the movie
- Description: Retrieves movie information by its title using the OMDB API. Optionally, you can provide the year to narrow down the search results.
- Example: http://127.0.0.1:5000/movie_name?title=Swallow&year=2019

### 3. Get Movie Recommendations

- Endpoint: `/recommendations`
- Method: GET
- Parameters: 
    - `movie_type` (required) - the type of movie for which recommendations are needed
    - `value` (optional) - the number of recommendations to generate (default is 10)
- Description: Generates movie recommendations based on the specified movie type using the OpenAI GPT model.
- Example: http://127.0.0.1:5000/recommendations?movie_type=war&value=10

### 4. Generate Movie Recommendation Titles
**--UNDER DEVELOPMENT--**
- Endpoint: `/generate_movie_rec_titles`
- Method: GET
- Parameters: 
    - `total` (optional) - the total number of recommendation titles to generate (default is 10)
- Description: Generates movie recommendation titles using the OpenAI GPT model and stores them in the database.
- **--UNDER DEVELOPMENT--**

### 5. Provide Movie Recommendation Titles

- Endpoint: `/provide_movie_rec_titles`
- Method: POST
- Request Body: JSON object with a list of movie recommendation titles (`titles`)
- Description: Stores the provided movie recommendation titles in the database.
- Example: http://localhost:5000/provide_movie_rec_titles -d '{"titles": ["Best Comedy Movies", "Best Action Movies"]}' -H "Content-Type: application/json" -X POST

### 6. Generate Recommendations from Movie List

- Endpoint: `/generate_recs_in_db`
- Method: GET
- Description: Generates recommendations from the list of movie topics stored in the database.

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
Add endpoints to return recomendation information

## License

This project is licensed under the [MIT License](LICENSE).
