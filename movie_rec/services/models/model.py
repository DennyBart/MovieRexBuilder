from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class CastName(Base):
    __tablename__ = 'cast_name'
    uuid = Column(String(36), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    cast_type = Column(String(16), nullable=False)
    movies = relationship('MovieCast', back_populates='cast')

class MoviesNotFound(Base):
    __tablename__ = 'movies_not_found'
    uuid = Column(String(36), primary_key=True, unique=True, nullable=False)
    title = Column(String(256), nullable=False)
    searched_at = Column(DateTime, nullable=False)

class MovieRecommendations(Base):
    __tablename__ = 'movie_recommendations'
    uuid = Column(String(36), primary_key=True, unique=True, nullable=False)
    movie_id = Column(ARRAY(String(36)), nullable=False)
    topic_name = Column(String(256), nullable=False)
    date_generated = Column(DateTime, nullable=True)
    casting_id = Column(String(256), nullable=True)

class SearchHistory(Base):
    __tablename__ = 'search_history'
    uuid = Column(String(36), primary_key=True, unique=True, nullable=False)
    title = Column(String(256), nullable=False)
    searched_at = Column(DateTime, nullable=False)

class MovieData(Base):
    __tablename__ = 'movie_data'
    uuid = Column(String(36), primary_key=True, unique=True, nullable=False)
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
    imdb_rating = Column(String(16), nullable=True)
    imdb_votes = Column(String(32), nullable=True)
    imdb_id = Column(String(16), nullable=False, unique=True)
    movie_type = Column(String(32), nullable=True)
    dvd_release = Column(String(32), nullable=True)
    box_office = Column(String(32), nullable=True)
    production = Column(String(256), nullable=True)
    website = Column(String(256), nullable=True)
    cast = relationship('MovieCast', back_populates='movie')

class MovieCast(Base):
    __tablename__ = 'movie_cast'
    movie_uuid = Column(String(36), ForeignKey('movie_data.uuid'), primary_key=True)
    cast_id = Column(String(36), ForeignKey('cast_name.uuid'), primary_key=True)
    movie = relationship('MovieData', back_populates='cast')
    cast = relationship('CastName', back_populates='movies')
