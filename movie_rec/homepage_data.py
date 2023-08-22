from collections import Counter
import logging
import random
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from movie_rec.models import (FeaturedContent,
                              Genre,
                              MovieCast,
                              MovieGenre,
                              MovieRecommendationRelation,
                              MovieRecommendations)
from movie_rec.models import CastName
from datetime import datetime
from random import choice
from constants import (
    DIRECTOR_HOMEPAGE_HEADER,
    ACTOR_HOMEPAGE_HEADER,
    CAST_PAGE_LIMIT)
from movie_rec.types import ContentType


def get_vip_cast(session: Session, cast_type: str):
    """
    Fetches the VIP cast members from the 'cast_name' table.

    :param session: SQLAlchemy Session object
    :return: List of VIP cast members
    """
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
    Fetches all the recommendation_uuids for movies directed by a VIP director, up to a given limit. # noqa

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

    # 4. Extract and return the recommendation_uuids
    recommendation_uuids = [rec.recommendation_uuid for rec in recommendations]
    return recommendation_uuids


def generate_movie_cast_homepage_data(session: Session, cast_type: str):
    vip_cast_list = get_vip_cast(session, cast_type)

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
            unique_recommendation_uuids = list(set(list_recommendation_uuids))
            limited_recommendation_uuids = random.sample(unique_recommendation_uuids, min(CAST_PAGE_LIMIT, len(unique_recommendation_uuids)))  # noqa

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


def fetch_movie_uuids(session: Session, recommendation_uuid):
    query = session.query(MovieRecommendationRelation.movie_uuid).filter(
        MovieRecommendationRelation.recommendation_uuid == recommendation_uuid
    )
    return [record[0] for record in query.all()]


def fetch_genres_for_movies(session: Session, movie_uuids):
    genre_query = session.query(Genre.name).join(MovieGenre).filter(
        MovieGenre.movie_uuid.in_(movie_uuids)
    )
    return [record[0] for record in genre_query.all()]


def get_top_genres(genres):
    genre_counter = Counter(genres)
    return genre_counter.most_common(3)


def update_recommendation(session: Session, recommendation_uuid, top_genres):
    recommendation = session.query(MovieRecommendations).filter_by(
        uuid=recommendation_uuid).first()

    if not recommendation:
        return None

    for i, (genre_name, _) in enumerate(top_genres):
        genre = session.query(Genre).filter_by(name=genre_name).first()
        if genre:
            setattr(recommendation, f'genre_{i+1}', genre.id)
    logging.info(f'Updated recommendation {recommendation_uuid} with genres')

    session.commit()
    return recommendation


def get_genre(session: Session, genre_name=None):    
    if genre_name:
        genre = session.query(Genre).filter(Genre.name.ilike(genre_name)).first()
        if genre:
            return genre

    # Ensure that the query actually returns something before choosing
    all_genres = session.query(Genre).all()
    if all_genres:
        return choice(all_genres)
    else:
        return None  # Handle this case appropriately


def get_movie_recommendations(session: Session, genre, num_items=10):
    return session.query(MovieRecommendations).filter_by(
        genre_1=genre.id).limit(num_items).all()


def clear_previous_featured_content(session: Session, genre):
    session.query(FeaturedContent).filter(
        and_(
            FeaturedContent.content_type == 'genre'
        )
    ).delete()
    session.commit()


def add_featured_content(session: Session, genre, uuids):
    for u in uuids:
        content = FeaturedContent(
            content_type=ContentType.GENRE.value,
            group_title=f"Featured in {genre.name}",
            recommendation_uuid=u,
            replaced_at=datetime.utcnow()
        )
        session.add(content)
    session.commit()
