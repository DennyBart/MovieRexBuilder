from sqlalchemy import (
    Column,
    Float,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    UniqueConstraint
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class CastName(Base):
    __tablename__ = 'cast_name'
    uuid = Column(UUID(as_uuid=True),
                  primary_key=True,
                  unique=True,
                  nullable=False)
    name = Column(String(256), nullable=False)
    cast_type = Column(String(16), nullable=False)
    movies = relationship('MovieCast', back_populates='cast')


class SearchHistory(Base):
    __tablename__ = 'search_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    searched_at = Column(DateTime, nullable=False)


class MovieData(Base):
    __tablename__ = 'movie_data'
    uuid = Column(UUID(as_uuid=True),
                  primary_key=True,
                  unique=True,
                  nullable=False)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=False)
    rated = Column(String(16), nullable=True)
    released = Column(String(32), nullable=True)
    runtime = Column(String(32), nullable=True)
    genre = Column(String(256), nullable=True)
    director = Column(String(36), ForeignKey('cast_name.uuid'), nullable=True)
    writer = Column(String(512), nullable=True)
    plot = Column(Text, nullable=True)
    language = Column(String(256), nullable=True)
    country = Column(String(256), nullable=True)
    awards = Column(String(256), nullable=True)
    poster = Column(String(512), nullable=True)
    ratings = Column(JSON, nullable=True)
    metascore = Column(String(32), nullable=True)
    imdbrating = Column(String(16), nullable=True)
    imdbvotes = Column(String(32), nullable=True)
    imdbid = Column(String(16), nullable=False, unique=True)
    images = relationship('MovieImage', back_populates='movie_data')
    videos = relationship('MovieVideo', back_populates='movie_data')
    type = Column(String(32), nullable=True)
    dvd = Column(String(32), nullable=True)
    boxoffice = Column(String(32), nullable=True)
    production = Column(String(256), nullable=True)
    website = Column(String(256), nullable=True)
    cast = relationship('MovieCast', back_populates='movie')

    def to_dict(self):
        return {
            c.name: str(getattr(self, c.name)) if isinstance(
                getattr(self, c.name), UUID) else getattr(self, c.name)
            for c in self.__table__.columns
        }


class MovieRecommendations(Base):
    __tablename__ = 'movie_recommendations'
    uuid = Column(UUID(as_uuid=True),
                  primary_key=True,
                  unique=True,
                  nullable=False)
    count = Column(Integer, nullable=True)
    topic_name = Column(String(256), nullable=False)
    date_generated = Column(DateTime, nullable=True)
    casting_id = Column(String(256), nullable=True)
    blurb = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class MovieRecommendationRelation(Base):
    __tablename__ = 'movie_recommendation_relation'
    id = Column(Integer, primary_key=True)
    recommendation_uuid = Column(UUID(as_uuid=True), 
                                 ForeignKey('movie_recommendations.uuid'),
                                 nullable=False)
    movie_uuid = Column(UUID(as_uuid=True),
                        ForeignKey('movie_data.uuid'),
                        nullable=False)

    __table_args__ = (
        UniqueConstraint('recommendation_uuid',
                         'movie_uuid',
                         name='unique_recommendation_movie'),
    )


class MovieCast(Base):
    __tablename__ = 'movie_cast'
    movie_uuid = Column(UUID(as_uuid=True),
                        ForeignKey('movie_data.uuid'),
                        primary_key=True)
    cast_id = Column(UUID(as_uuid=True),
                     ForeignKey('cast_name.uuid'),
                     primary_key=True)
    movie = relationship('MovieData', back_populates='cast')
    cast = relationship('CastName', back_populates='movies')


class MovieRecommendationsSearchList(Base):
    __tablename__ = 'movie_recommendations_search_list'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    generated = Column(Boolean, nullable=False, default=False)
    generated_at = Column(DateTime, nullable=False)


class MoviesNotFound(Base):
    __tablename__ = 'movies_not_found'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    searched_at = Column(DateTime, nullable=False)
    rec_topic = Column(String(256), nullable=True)


class MovieImage(Base):
    __tablename__ = 'movie_images'
    id = Column(Integer, autoincrement=True, primary_key=True)
    aspect_ratio = Column(Float, nullable=True)
    height = Column(Integer, nullable=True)
    iso_639_1 = Column(String(length=2), nullable=True)
    file_path = Column(String(length=100), nullable=True)
    vote_average = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    imdbid = Column(String(16), ForeignKey('movie_data.imdbid'))
    movie_data = relationship("MovieData", back_populates="images")


class MovieVideo(Base):
    __tablename__ = 'movie_videos'
    id = Column(String(length=24), primary_key=True)
    iso_639_1 = Column(String(length=2), nullable=True)
    iso_3166_1 = Column(String(length=2), nullable=True)
    name = Column(String(length=200), nullable=True)
    key = Column(String(length=200), nullable=True)
    site = Column(String(length=100), nullable=True)
    size = Column(Integer, nullable=True)
    type = Column(String(length=200), nullable=True)
    official = Column(Boolean, nullable=True)
    published_at = Column(DateTime, nullable=True)
    imdbid = Column(String(16), ForeignKey('movie_data.imdbid'))
    movie_data = relationship("MovieData", back_populates="videos")
