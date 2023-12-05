import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

engine = create_engine(DATABASE_URL, pool_recycle=280)
DBSession = sessionmaker(bind=engine)


@contextmanager
def get_db_session():
    session = DBSession()
    try:
        yield session
    finally:
        session.close()
