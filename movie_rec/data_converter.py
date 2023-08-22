import json
import os

from movie_rec.movie_search import (
    get_cast_info,
    get_imdb_image_url,
    get_imdb_video_url)

IMAGE_DOMAIN = os.getenv("IMAGE_DOMAIN")
VIDEO_DOMAIN = os.getenv("VIDEO_DOMAIN")


def json_to_dict(data_json):
    if isinstance(data_json, str):
        return json.loads(data_json)
    else:
        return data_json


def init_output(data_dict):
    return {
        'title': data_dict.get('title', None),
        'uuid': data_dict.get('uuid', None),
        'year': data_dict.get('year', None),
        'genre': data_dict.get('genre', None),
        'metascore': data_dict.get('metascore', None),
    }


def add_cast(output, data_dict):
    # Get cast information
    cast_info = get_cast_info(data_dict.get('uuid'))
    # Add cast information to output
    output['director'] = [{'name': director} for director in cast_info['directors']] if cast_info['directors'] else None # noqa
    output['actors'] = [{'name': actor} for actor in cast_info['actors']] if cast_info['actors'] else None # noqa
    output['writer'] = [{'name': writer} for writer in cast_info['writers']] if cast_info['writers'] else None # noqa


def add_plot(output, data_dict):
    output['plot'] = data_dict.get('plot', None)


def add_rec_title(output, rec_title):
    title_name, uuid = rec_title
    recommendation = {
        "recommendation_title": title_name,
        "rec_uuid": uuid
    }
    output['recommendation'] = [recommendation]


def add_media(output, data_dict, imdbid):
    image_urls = get_imdb_image_url(imdbid)
    video_data = get_imdb_video_url(imdbid)
    # Process image URLs
    if image_urls:
        for i, url in enumerate(image_urls):
            output[f'image_key_{i+1}'] = IMAGE_DOMAIN + str(url)
    else:
        output['image_keys'] = data_dict.get('poster', None)
    # Process video data
    if video_data:
        # Transform each tuple into a dictionary and append to 'video_keys'
        output['video_keys'] = [{'key': VIDEO_DOMAIN + str(k), 'name': str(n)} for k, n in video_data] # noqa
    else:
        output['video_keys'] = None


def add_info(output, data_dict):
    output['awards'] = data_dict.get('awards', None)
    output['ratings'] = data_dict.get('ratings', None)
    output['rated'] = data_dict.get('rated', None)
    output['release'] = data_dict.get('released', None)
    output['runtime'] = data_dict.get('runtime', None)


def format_recommendation_list(data_list, rec_data=None,
                               cast=False, plot=False,
                               media=False, info=False):
    output_list = []
    for data_json in data_list:
        data_dict = json_to_dict(data_json)
        output = init_output(data_dict)

        if cast:
            add_cast(output, data_dict)

        if plot:
            add_plot(output, data_dict)

        if media:
            add_media(output, data_dict, data_dict.get('imdbid'))

        if info:
            add_info(output, data_dict)

        if rec_data is not None:
            add_rec_title(output, rec_data)

        output_list.append(output)

    sorted_movies = sorted(output_list, key=lambda x: x['metascore'] if x['metascore'] is not None else -1, reverse=True) # noqa
    return sorted_movies
