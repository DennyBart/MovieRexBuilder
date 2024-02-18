# MovieRex

This Movie Recommendation API is a Flask-based web application that provides a range of recomendation services for movies. The application interacts with artificial intelligence (OpenAI's GPT API) to generate movie recommendations based on popular topics such as ***"Best Zombie Movies to Keep You Up at Night"***. The service uses the GPT API to generate the list of recommendation titles, the movies for each title, an introduction to the recommendation title and also query additional APIs to store movie data. After the data is stored any request to the API will server the data from the local DB.

### API Key Features

**Intelligent Recommendations:** At the core of this application is its powerful recommendation system. The system uses the user defined OpenAI's GPT model (gpt-3.5-turbo, gpt-4, etc) to generate suggestions based on user-provided parameters. It's able to parse and understand complex requests, such as asking for the best animated films of the last decade or cult classics that deal with specific themes. The application also creates a summary of the movie recomendation and some details about those movies.

### Search
- **Movie Search:** Allows users to search for movies by ID or name, facilitating the easy location of specific movies in the database and enhancing the user's navigation experience.
- **Recommendation Search:** Enables users to search for movie recommendations based on specific topics or genres. This feature assists in discovering new movies that align with the user's interests.
- **Genre Search:** Offers the ability to search movies by genre, aiding users in finding films that fit their preferred style or thematic interest. This function streamlines the process of exploring movies within specific genres.

**Movie Details Retrieval:** The application interfaces with the OMDB API and TMDB to retrieve additional details about the movies. This adds a layer of depth to the recommendations by providing more information about each suggested title, including actors, directors, genre, trailers, images and more.

**Movie Data Archive:** A key feature of this tool is to store API responses to the DB and if a repeat request is made the service will server the response from the DB instead of making a request to an external API.

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [API Overview](#api-overview)
- [Logging](#logging)
- [ToDo](#todo)
- [License](#license)

## Requirements

Before running the Movie Recommendation API, make sure you have the following:

- OpenAI API Key: You will need an API key from OpenAI to use their GPT model for generating movie recommendations. You can sign up for an API key on the [OpenAI website](https://openai.com/).
- OMDB API Key: You will need an account on OMDB (Open Movie Database) to access movie information and search for movies by ID or name. You can create an account on the [OMDB website](https://www.omdbapi.com/) and obtain an API key.
- TMDB API Key: The Movie DB (TMDB) API key can be generated on the site after creating an account [TMDB](https://www.themoviedb.org/). A rate limit is advised for TMDB and it is implemented in the applicaiton for up to date information on the rate limit see [TMDB API Rate Limit](https://developer.themoviedb.org/docs/rate-limiting)
- MySQL Database: The application requires a MySQL database to store movie recommendation titles and other relevant data. Make sure you have a running MySQL database and the necessary credentials to connect to it. You can install MySQL from the official [Mysql website](https://www.mysql.com/).


Once you have obtained the OpenAI API key, OMDB API key, and set up the MySQL database, you can proceed with the setup and configuration steps mentioned in the previous section.

## Setup

To set up and run the Movie Recommendation API locally, follow these steps:

1. Clone the repository: `https://github.com/DennyBart/MovieRexBuilder.git`
2. Navigate to the project directory: `cd movie-recommendation-api`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Set the required environment variables:
    - `DATABASE_URL` - Database location
    - `OMDB_API_KEY` - Your API key for the OMDB API
    - `OPENAI_API_KEY` - Your API key for the OpenAI API
    - `OPENAI_API_BLURB_MODEL` - The name or ID of the OpenAI GPT model to use [OpenAI API Models] (https://platform.openai.com/docs/models)
    - `
    - `OPENAI_API_MODEL` - The name or ID of the OpenAI GPT model to use [OpenAI API Models] (https://platform.openai.com/docs/models)
    - `OPENAI_API_MODEL_RECOMENDATIONS` - The name or ID of the OpenAI GPT model to use [OpenAI API Models] (https://platform.openai.com/docs/models)
    - `THEMOVIEDB_API_KEY` - Your API ker for TMDB
    - `LOG_FILE_LOCATION` - LOG Files location
    - `SCHEDULED_PAGE_API_KEY` - Internal API key for Scheduled tasks
    - `IMAGE_DOMAIN` - https://www.themoviedb.org/t/p/w533_and_h300_bestv2/ (Used to fetch image URIs)
    - `VIDEO_DOMAIN` - https://www.youtube.com/watch?v= (Fetch youtube links)

5. Run the application: `python app.py`
6. The API will be available at `http://localhost:5000`

Note: Make sure to replace the environment variable values with your own API keys and model information.

## Endpoints

The API provides the following endpoints:

## API Overview

[API Documentation](API_DOCS.md)


## Logging

The application logs are stored in the `logs/app.log` file. The log file is rotated when it reaches a size of 10 MB, and a maximum of 5 backup log files are kept.

## ToDo
- Improved logging of Errors and Info
- Add support for other API providers
- Add caching service to flask
- Track errors for missing movies

## License

This project is licensed under the [MIT License](LICENSE).
