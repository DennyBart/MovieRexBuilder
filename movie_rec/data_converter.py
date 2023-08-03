import json

from movie_rec.movie_search import get_cast_info


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
    }


def add_cast(output, data_dict):
    # Get cast information
    cast_info = get_cast_info(data_dict.get('uuid'))
    # Add cast information to output
    output['director'] = ', '.join(cast_info['directors']) if cast_info['directors'] else None
    output['actors'] = ', '.join(cast_info['actors']) if cast_info['actors'] else None
    output['writer'] = ', '.join(cast_info['writers']) if cast_info['writers'] else None


def add_plot(output, data_dict):
    output['plot'] = data_dict.get('plot', None)


def add_media(output, data_dict):
    output['video_keys'] = None   # To be populated later
    output['image_keys'] = data_dict.get('poster', None)


def add_info(output, data_dict):
    output['awards'] = data_dict.get('awards', None)
    output['ratings'] = data_dict.get('ratings', None)
    output['rated'] = data_dict.get('rated', None)
    output['release'] = data_dict.get('released', None)
    output['runtime'] = data_dict.get('runtime', None)


def format_recommendation_list(data_list, cast=False, plot=False,
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
            add_media(output, data_dict)

        if info:
            add_info(output, data_dict)

        output_list.append(output)

    return output_list
