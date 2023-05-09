from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class OpenAIHistory(Base):
    __tablename__ = 'openai_prompts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(String(256), nullable=False)
    response = Column(String(256), nullable=False)
    searched_time = Column(DateTime, nullable=False)
