# MovieRecs Flask API Documentation

## General Information
- **Base URL:** The base URL for all endpoints will depend on where the Flask app is hosted.
- **Content-Type:** All requests and responses are formatted as JSON unless otherwise specified.
- **Authentication:** Some endpoints require an API key passed in the header as `x-api-key`.

## Endpoints

### 1. Landing Page
- **URL:** `/`
- **Method:** `GET`
- **Description:** Serves the landing page of the MovieRexDev1 application.
- **Query Parameters:**
  - `page` (int): Page number for pagination.
- **Responses:**
  - **200**: Successfully renders the landing page.
  - **500**: Internal server error.

### 2. Display Recommendation
- **URL:** `/web/rec/<uuid>`
- **Method:** `GET`
- **Description:** Displays detailed information about a specific movie recommendation.
- **URL Parameters:**
  - `uuid` (string): UUID of the movie recommendation.
- **Responses:**
  - **200**: Successfully renders the recommendation page.
  - **500**: Internal server error if UUID is not found or there is a database error.

### 3. Search Movies
- **URL:** `/search`
- **Method:** `GET`
- **Description:** Searches movies based on a query.
- **Query Parameters:**
  - `query` (string): The search keyword.
- **Responses:**
  - **200**: Returns search results.
  - **400**: Bad request if query parameter is missing.

### 4. Generate Homepage Data
- **URL:** `/api/gen_homepage_data`
- **Method:** `POST`
- **Description:** Generates and populates data for the homepage.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Responses:**
  - **200**: Data generation successful.
  - **403**: Forbidden if API key is missing or invalid.

### 5. Movie by IMDb ID
- **URL:** `/api/get_movie_id`
- **Method:** `GET`
- **Description:** Retrieves movie data using an IMDb ID.
- **Query Parameters:**
  - `id` (string): IMDb ID of the movie.
- **Responses:**
  - **200**: Returns movie data.
  - **400**: Bad request if movie ID is invalid.
  - **404**: Not found if movie ID does not exist.

### 6. Get Movie Data by UUID
- **URL:** `/api/get_movie_uuid`
- **Method:** `GET`
- **Description:** Retrieves detailed movie data using a movie UUID.
- **Query Parameters:**
  - `uuid` (string): UUID of the movie.
- **Responses:**
  - **200**: Returns detailed movie data including cast, plot, media, and other info.
  - **400**: Bad request if movie UUID is invalid.
  - **404**: Not found if movie UUID does not exist.

### 7. Get Movie Data by Title and Year
- **URL:** `/api/get_movie_name`
- **Method:** `GET`
- **Description:** Retrieves movie data based on the movie title and release year.
- **Query Parameters:**
  - `title` (string): Title of the movie.
  - `year` (string): Release year of the movie.
- **Responses:**
  - **200**: Returns movie data.
  - **400**: Bad request if movie title or year is missing or invalid.
  - **404**: Not found if the combination of title and year does not match any movie.

### 8. Add a New Movie Recommendation Manually
- **URL:** `/api/add_recommendation`
- **Method:** `POST`
- **Description:** Adds a new movie recommendation to the system manually.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Request Body:**
  - `movie_type` (string): Type of the movie.
  - `value` (int, optional): Number of movies to generate, default is 20.
- **Responses:**
  - **200**: Successfully generated movie recommendations.
  - **400**: Bad request if data provided is invalid or missing.
  - **403**: Forbidden if API key is missing or invalid.

### 9. Generate Movie Recommendation Titles
- **URL:** `/api/generate_movie_rec_titles`
- **Method:** `POST`
- **Description:** Generates movie recommendation titles from the "to be generated" list in batches.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Request Body:**
  - `total` (int): Total number of titles to generate.
- **Responses:**
  - **200**: Returns a list of generated movie titles.
  - **400**: Bad request if input data is invalid or missing.
  - **403**: Forbidden if API key is missing or invalid.
  - **400**: Validation error for the 'total' parameter.

### 10. Generate Recommendation Blurb
- **URL:** `/api/generate_rec_blurb`
- **Method:** `POST`
- **Description:** Generates a blurb for a specific movie recommendation.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Request Body:**
  - `uuid` (string): UUID of the movie recommendation.
  - `limit` (int, optional): Limit for the number of items in the blurb, default is 10.
- **Responses:**
  - **200**: Returns the generated blurb for the recommendation.
  - **400**: Bad request if input data is invalid or missing.
  - **403**: Forbidden if API key is missing or invalid.

### 11. Provide Movie Recommendation Titles
- **URL:** `/api/provide_movie_rec_titles`
- **Method:** `POST`
- **Description:** Adds a list of movie recommendation titles to the "to be generated" list.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Request Body:**
  - `titles` (list of strings): List of movie titles to be added.
- **Responses:**
  - **200**: Returns the list of stored titles.
  - **400**: Bad request if input data is invalid.
  - **403**: Forbidden if API key is missing or invalid.

### 12. Generate Recommendations in Database
- **URL:** `/api/generate_recs_in_db`
- **Method:** `POST`
- **Description:** Processes and generates recommendations stored in the database.
- **Headers:**
  - `x-api-key` (string): Required API key for authentication.
- **Request Body:**
  - `blurb` (string, optional): Whether to generate blurbs, default is 'False'.
  - `lists_to_generate` (int, optional): Limit of recommendation titles to generate, default is 1.
  - `movies_per_list` (int, optional): Number of movie titles each recommendation to generate, default is 20.
- **Responses:**
  - **200**: Indicates the start of the recommendation data generation process.
  - **400**: Bad request if input data is invalid or missing.
  - **403**: Forbidden if API key is missing or invalid.

### 13. List Recommendations
- **URL:** `/api/list_recommendations`
- **Method:** `GET`
- **Description:** Retrieves a list of movie recommendations.
- **Query Parameters:**
  - `search` (string, optional): Search term for recommendations.
  - `limit` (int, optional): Number of recommendations to retrieve, default is 50.
  - `offset` (int, optional): Offset for pagination, default is 0.
  - `blurb` (bool, optional): Whether to include blurbs in the results, default is False.
- **Responses:**
  - **200**: Returns a list of recommendations.
  
### 14. Get Recommendation by UUID
- **URL:** `/api/get_recommendation_by_uuid`
- **Method:** `GET`
- **Description:** Retrieves already generated recommendation data by UUID.
- **Query Parameters:**
  - `uuid` (string): UUID of the recommendation.
- **Responses:**
  - **200**: Returns recommendation data.
  - **400**: Bad request if UUID is missing or invalid.
  - **404**: Not found if no recommendations are found for the UUID.

### 15. Get Recommendation by Title
- **URL:** `/api/get_recommendation_by_title`
- **Method:** `GET`
- **Description:** Retrieves already generated recommendation data by title.
- **Query Parameters:**
  - `search` (string): Title of the recommendation.
- **Responses:**
  - **200**: Returns recommendation data.
  - **400**: Bad request if title is missing or invalid.
  - **404**: Not found if no recommendations are found for the title.

### 16. Get Recommendation Blurb
- **URL:** `/api/get_recommendation_blurb`
- **Method:** `GET`
- **Description:** Retrieves already generated recommendation blurb data.
- **Query Parameters:**
  - `uuid` (string): UUID of the recommendation.
- **Responses:**
  - **200**: Returns recommendation blurb data.
  - **400**: Bad request if UUID is missing or invalid.
  - **404**: Not found if no blurb is found for the UUID.

### 17. Get Movie Videos
- **URL:** `/api/get_movie_videos`
- **Method:** `GET`
- **Description:** Retrieves movie video data for a specific movie, with an option to overwrite existing data.
- **Query Parameters:**
  - `uuid` (string): UUID of the movie.
  - `overwrite` (bool, optional): Whether to overwrite existing video data, default is False.
- **Responses:**
  - **200**: Returns message indicating the status of video data retrieval.
  - **400**: Bad request if UUID is missing or invalid.
  - **404**: Not found if no movie data is found for the UUID.

### 18. Get Movie Images
- **URL:** `/api/get_movie_images`
- **Method:** `GET`
- **Description:** Retrieves movie image data for a specific movie, with an option to overwrite existing data.
- **Query Parameters:**
  - `uuid` (string): UUID of the movie.
  - `overwrite` (bool, optional): Whether to overwrite existing image data, default is False.
- **Responses:**
  - **200**: Returns message indicating the status of image data retrieval.
  - **400**: Bad request if UUID is missing or invalid.
  - **404**: Not found if no movie data is found for the UUID.

### 19. Replace Movie by ID
- **URL:** `/api/replace_movie_id`
- **Method:** `GET`
- **Description:** Replaces movie data for a given UUID with new data based on an IMDb ID.
- **Query Parameters:**
  - `imbdid` (string): IMDb ID of the new movie data.
  - `replace_uuid` (string): UUID of the movie to be replaced.
- **Responses:**
  - **200**: Returns the new movie data.
  - **400**: Bad request if IMDb ID or UUID is missing or invalid.
  - **403**: Forbidden if API key is missing or invalid.
  - **404**: Not found if IMDb ID does not exist.

### 20. Generate Recommendations Genre Data
- **URL:** `/api/generate_recommendations_genre`
- **Method:** `GET`
- **Description:** Generates recommendations genre data for a given UUID.
- **Query Parameters:**
  - `recommendation_uuid` (string): UUID of the recommendation.
- **Responses:**
  - **200**: Returns genre data for the recommendation.
  - **400**: Bad request

## Error Handling
- All endpoints return appropriate HTTP status codes along with error messages in the case of failure.
- Common HTTP status codes used:
  - **200**: OK
  - **400**: Bad Request
  - **403**: Forbidden
  - **404**: Not Found
  - **500**: Internal Server Error