import re
import requests
import chardet
import time

# Replace with the path to your file containing movie names and years
file_path = 'movie_list.txt'
# Replace with the path to the output file
output_file_path = 'movie_list_output.txt'

url = 'http://127.0.0.1:5000/movie_name'

limit = 100  # Set the limit of requests
wait_time = 2  # Set the waiting period in seconds


def detect_encoding(file_path):
    with open(file_path, "rb") as file:
        result = chardet.detect(file.read())
    return result["encoding"]


encoding = detect_encoding(file_path)


# try:
# TODO - Update the call to a function instead of url and add a TRY EXCEPT
with open(file_path, "r", encoding=encoding) as file, \
        open(output_file_path, "a", encoding=encoding) as output_file:
    counter = 0  # Initialize the request counter
    for line in file:
        # Write the original line to the output file
        output_file.write(line)

        match = re.match(r'^(.+?)\s*\((\d{4})\)$', line.strip())
        if match:
            title, year = match.groups()
            response = requests.get(url, params={"title": title, "year": year})
            movie_data = response.json()
            if movie_data and 'Title' in movie_data:
                # Write the title of the movie to the output file
                output_file.write(f"{movie_data['Title']}\n")
            else:
                output_file.write("Movie not found\n")
        else:
            output_file.write("Couldn't parse the line\n")

        # Increment the request counter
        counter += 1

        # Wait for the specified time if the request counter has reached limit
        if counter == limit:
            time.sleep(wait_time)
            counter = 0

# except Exception as e:
#     # Print the traceback message and stop the script
#     traceback.print_exc()
#     raise SystemExit(1)
