import json

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

with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Conversion completed. Output written to {output_file}.")
