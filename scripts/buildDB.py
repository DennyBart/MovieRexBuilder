import re
import requests
import chardet

file_path = 'movie_listAD.txt'  # Replace with the path to your file containing movie names and years

url = 'http://127.0.0.1:5000/movie_name'


def detect_encoding(file_path):
    with open(file_path, "rb") as file:
        result = chardet.detect(file.read())
    return result["encoding"]

encoding = detect_encoding(file_path)

with open(file_path, "r", encoding=encoding) as file:
    for line in file:
        match = re.match(r'^(.+?)\s*\((\d{4})\)$', line.strip())
        if match:
            title, year = match.groups()
            response = requests.get(url, params={"title": title, "year": year})
            print(response.json())
        else:
            print(f"Couldn't parse the line: {line.strip()}")
