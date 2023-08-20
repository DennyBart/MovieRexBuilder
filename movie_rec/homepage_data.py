import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from movie_rec.models import FeaturedContent, MovieCast, MovieData, MovieRecommendationRelation
from movie_rec.models import CastName
from datetime import datetime
from constants import (
    DIRECTOR_HOMEPAGE_HEADER,
    ACTOR_HOMEPAGE_HEADER,
    CAST_PAGE_LIMIT)
from sqlalchemy.orm import joinedload


def get_vip_cast(session: Session, cast_type: str):
    """
    Fetches the VIP cast members from the 'cast_name' table.

    :param session: SQLAlchemy Session object
    :return: List of VIP cast members
    """
    print(str(cast_type))
    if cast_type.lower() == 'director' or cast_type.lower() == 'actor':
        return session.query(CastName).filter(
            func.lower(CastName.cast_type) == cast_type.lower(),
            CastName.vip.is_(True)
        ).all()
    else:
        return []


def get_recommendations_by_vip_cast(session: Session,
                                    cast_uuid: str,
                                    cast_type: str,
                                    limit: int):
    """
    Fetches all the recommendation_uuids for movies directed by a VIP director, up to a given limit.

    :param session: SQLAlchemy Session object
    :param director_uuid: The UUID of the director
    :param limit: The maximum number of recommendation_uuids to fetch
    :return: List of recommendation_uuids
    """
    if cast_type.lower() == 'director' or cast_type.lower() == 'actor':
        # 1. Fetch all movies directed by the VIP director
        movies_by_cast = session.query(MovieCast).filter(
            MovieCast.cast_id == cast_uuid
        ).all()
    else:
        return []

    # 2. Extract the uuids of those movies
    movie_uuids = [movie.movie_uuid for movie in movies_by_cast]

    # 3. Fetch the recommendation_uuids for these movies
    recommendations = session.query(
        MovieRecommendationRelation.recommendation_uuid).filter(
        MovieRecommendationRelation.movie_uuid.in_(movie_uuids)
    ).limit(limit).all()
    print(recommendations)

    # 4. Extract and return the recommendation_uuids
    recommendation_uuids = [rec.recommendation_uuid for rec in recommendations]
    return recommendation_uuids


def generate_movie_cast_homepage_data(session: Session, cast_type: str):
    vip_cast_list = get_vip_cast(session, cast_type)
    print(f'VIP Cast List: {str(vip_cast_list)}')

    if vip_cast_list:
        random_cast_vip = random.choice(vip_cast_list)

        list_recommendation_uuids = get_recommendations_by_vip_cast(session, random_cast_vip.uuid, cast_type, 10)  # noqa

        if list_recommendation_uuids:
            # Delete existing entries with the same cast_type
            # TODO - This is a temporary solution. We need to update
            # the existing entries with the new ones. No empyt data at any time
            session.query(FeaturedContent).filter_by(content_type=cast_type).delete() # noqa
            session.commit()

            # Limit the number of unique recommendation_uuids
            # based on CAST_PAGE_LIMIT
            limited_recommendation_uuids = random.sample(list_recommendation_uuids, min(CAST_PAGE_LIMIT, len(list_recommendation_uuids)))  # noqa

            header = DIRECTOR_HOMEPAGE_HEADER if cast_type == 'director' else ACTOR_HOMEPAGE_HEADER  # noqa

            # Populate FeaturedContent table
            for rec_uuid in limited_recommendation_uuids:
                featured_content = FeaturedContent(
                    content_type=cast_type,
                    group_title=f'{header} {random_cast_vip.name}',
                    recommendation_uuid=rec_uuid,
                    replaced_at=datetime.utcnow(),  # set the current date
                    live_list=True  # Set the new column
                )
                session.add(featured_content)

            session.commit()

            return {
                'header': header,
                'recommendation_uuids': limited_recommendation_uuids,
                'cast': random_cast_vip
            }
    else:
        return None
