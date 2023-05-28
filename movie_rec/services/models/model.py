from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class CastName(Base):
    __tablename__ = 'cast_name'
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    cast_type = Column(String(16), nullable=False)
    movies = relationship('MovieCast', back_populates='cast')

class MoviesNotFound(Base):
    __tablename__ = 'movies_not_found'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    searched_at = Column(DateTime, nullable=False)

# class MovieRecommendations(Base):
#     __tablename__ = 'movie_recommendations'
#     uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
#     count = Column(Integer, nullable=True)
#     topic_name = Column(String(256), nullable=False)
#     date_generated = Column(DateTime, nullable=True)
#     casting_id = Column(String(256), nullable=True)


class SearchHistory(Base):
    __tablename__ = 'search_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True)
    searched_at = Column(DateTime, nullable=False)

class MovieData(Base):
    __tablename__ = 'movie_data'
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
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
    type = Column(String(32), nullable=True)
    dvd = Column(String(32), nullable=True)
    boxoffice = Column(String(32), nullable=True)
    production = Column(String(256), nullable=True)
    website = Column(String(256), nullable=True)
    cast = relationship('MovieCast', back_populates='movie')
    def to_dict(self):
        return {
            c.name: str(getattr(self, c.name)) if isinstance(getattr(self, c.name), UUID) else getattr(self, c.name)
            for c in self.__table__.columns
        }


class MovieRecommendations(Base):
    __tablename__ = 'movie_recommendations'
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    count = Column(Integer, nullable=True)
    topic_name = Column(String(256), nullable=False)
    date_generated = Column(DateTime, nullable=True)
    casting_id = Column(String(256), nullable=True)

class MovieRecommendationRelation(Base):
    __tablename__ = 'movie_recommendation_relation'
    recommendation_uuid = Column(UUID(as_uuid=True), ForeignKey('movie_recommendations.uuid'), primary_key=True)
    movie_uuid = Column(UUID(as_uuid=True), ForeignKey('movie_data.uuid'), primary_key=True)


class MovieCast(Base):
    __tablename__ = 'movie_cast'
    movie_uuid = Column(UUID(as_uuid=True), ForeignKey('movie_data.uuid'), primary_key=True)
    cast_id = Column(UUID(as_uuid=True), ForeignKey('cast_name.uuid'), primary_key=True)
    movie = relationship('MovieData', back_populates='cast')
    cast = relationship('CastName', back_populates='movies')
