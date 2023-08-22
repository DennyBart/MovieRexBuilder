import json
import os

input_file = 'movie_list_topics.txt'
output_file = 'movie_list_topics_output.json'

titles = []

with open(input_file, 'r') as f:
    for line in f:
        title = line.strip().strip('"')
        titles.append(title)

data = {
    'titles': titles
}

# Check if the output file exists
if os.path.exists(output_file):
    # Remove the file to ensure it is created fresh
    os.remove(output_file)

with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)
