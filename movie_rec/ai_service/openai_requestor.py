import datetime
from lib2to3.pytree import Base
from flask import session
import requests
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from movie_rec.ai_service.models import Base, OpenAIHistory

# Replace with your own database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/movie_database"
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def get_chatgpt_response(prompt, api_key, api_model):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    url = f'https://api.openai.com/v1/engines/{api_model}/completions'

    data = {
        'prompt': prompt,
        'max_tokens': 10,
        'n': 1,
        'stop': None,
        'temperature': 1.0,
    }

    response = requests.post(url, headers=headers, json=data)
    response_json = json.loads(response.text)
    print(response_json)
    answer = response_json['choices'][0]['text'].strip()

    # Save the history to the database
    openai_history = OpenAIHistory(prompt=prompt, response=answer, searched_time=datetime.datetime.now())
    session.add(openai_history)
    session.commit()

    return answer
