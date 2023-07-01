import uuid
from movie_rec.models import CastName, MovieData
from sqlalchemy.orm import joinedload


class CastProcessor:
    def __init__(self, session):
        self.session = session

    def get_cast(self, name, cast_type):
        cast_name = self.session.query(CastName).filter(
            CastName.name == name, CastName.cast_type == cast_type).first()
        return cast_name if cast_name else None

    def create_cast(self, cast_list, cast_type):
        cast_instances = []
        for cast_member in cast_list:
            cast_name = self.get_cast(cast_member, cast_type)
            if cast_name is None:
                cast_name = CastName(
                    name=cast_member, cast_type=cast_type, uuid=uuid.uuid4())
            cast_instances.append(cast_name)
        return cast_instances

    def get_movie_cast(self, movie_uuid):
        # Fetch the movie by UUID and eager-load the cast
        movie = self.session.query(MovieData)\
            .options(joinedload(MovieData.cast))\
            .filter(MovieData.uuid == movie_uuid)\
            .one()

        # Organize the cast by their type
        cast_by_type = {
            'actor': [],
            'director': [],
            'writer': []
        }

        for movie_cast in movie.cast:
            cast_by_type[movie_cast.cast.cast_type].append(
                movie_cast.cast.name)

        # Return cast_by_type as a Python dictionary
        return cast_by_type
