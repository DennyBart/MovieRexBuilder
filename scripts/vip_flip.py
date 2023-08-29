import os
import logging
import re
from sqlalchemy import ForeignKey, create_engine, Column, String, Boolean, CHAR, update
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base

# Configure SQLAlchemy
DATABASE_URL = 'mysql+pymysql://root:123456@localhost:3306/TestDB'
engine = create_engine(DATABASE_URL, pool_recycle=280)
session = Session(engine)
Base = declarative_base()

# Configure logging
success_logger = logging.getLogger('success')
success_handler = logging.FileHandler('successful.log')
success_logger.addHandler(success_handler)

failure_logger = logging.getLogger('failure')
failure_handler = logging.FileHandler('failed.log')
failure_logger.addHandler(failure_handler)

# DB table definition for MovieData
class MovieData(Base):
    __tablename__ = 'movie_data'
    uuid = Column(CHAR(36), primary_key=True, unique=True, nullable=False)
    # Add other fields
    cast = relationship('MovieCast', back_populates='movie')

# DB table definition for MovieCast
class MovieCast(Base):
    __tablename__ = 'movie_cast'
    movie_uuid = Column(CHAR(36), ForeignKey('movie_data.uuid'), primary_key=True)
    cast_id = Column(CHAR(36), ForeignKey('cast_name.uuid'), primary_key=True)
    movie = relationship('MovieData', back_populates='cast')
    cast = relationship('CastName', back_populates='movies')

# DB table definition for CastName
class CastName(Base):
    __tablename__ = 'cast_name'
    uuid = Column(CHAR(36), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    cast_type = Column(String(16), nullable=False)
    vip = Column(Boolean, nullable=False, default=False)
    movies = relationship('MovieCast', back_populates='cast')


# Function to update the VIP status
def update_vip_status(names_list, cast_type='actor'):
    not_found = []
    for line in names_list:
        # Remove numeric prefixes (if present) and extra spaces
        name = re.sub(r'^\d+\.\s*', '', line).strip()
        print(name)
        
        cast_entry = session.query(CastName).filter(CastName.name == name, CastName.cast_type == cast_type).first()
        
        if cast_entry:
            cast_entry.vip = True
            session.commit()
            success_logger.info(f"VIP status updated for {name}")
        else:
            # Try a fuzzy search to find a similar name
            similar_cast = session.query(CastName).filter(CastName.name.like(f"%{name}%"), CastName.cast_type == cast_type).first()
            
            if similar_cast:
                similar_cast.vip = True
                session.commit()
                success_logger.info(f"VIP status updated for similar name {similar_cast.name} for search term {name}")
            else:
                not_found.append(name)
                failure_logger.info(f"{name} not found")
    
    return not_found

if __name__ == "__main__":
    # Read the list of names from a file
    with open("dir_names_list.txt", "r") as f:
        names_list = [line.strip() for line in f.readlines()]

    # Update the VIP status
    not_found = update_vip_status(names_list, cast_type='DIRECTOR')

    # Output the list of names not found
    if not_found:
        with open("not_found.txt", "w") as f:
            for name in not_found:
                f.write(f"{name}\n")
