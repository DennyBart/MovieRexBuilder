"""First Version

Revision ID: b9991574a199
Revises: 
Create Date: 2023-05-05 18:13:55.869161

"""
from alembic import op
import sqlalchemy as sa
import psycopg2
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b9991574a199'
down_revision = None
branch_labels = None
depends_on = None



def upgrade():

    op.create_table(
        'cast_name',
        sa.Column('uuid', sa.String(36), primary_key=True, unique=True, nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('cast_type', sa.String(16), nullable=False)
    )

    op.create_table(
        'movies_not_found',
        sa.Column('uuid', sa.String(36), primary_key=True, unique=True, nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('searched_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'movie_recommendations',
        sa.Column('uuid', sa.String(36), primary_key=True, unique=True, nullable=False),
        sa.Column('movie_id', postgresql.ARRAY(sa.String(36)), nullable=False),
        sa.Column('topic_name', sa.String(256), nullable=False),
        sa.Column('date_generated', sa.DateTime, nullable=True),
        sa.Column('casting_id', sa.String(256), nullable=True)
    )

    op.create_table(
        'search_history',
        sa.Column('uuid', sa.String(36), primary_key=True, unique=True, nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('searched_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'movie_data',
        sa.Column('uuid', sa.String(36), primary_key=True, unique=True, nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('rated', sa.String(16), nullable=True),
        sa.Column('released', sa.String(32), nullable=True),
        sa.Column('runtime', sa.String(32), nullable=True),
        sa.Column('genre', sa.String(256), nullable=True),
        sa.Column('director', sa.String(36), sa.ForeignKey('cast_name.uuid'), nullable=True),
        sa.Column('writer', sa.String(512), nullable=True),
        sa.Column('plot', sa.Text, nullable=True),
        sa.Column('language', sa.String(256), nullable=True),
        sa.Column('country', sa.String(256), nullable=True),
        sa.Column('awards', sa.String(256), nullable=True),
        sa.Column('poster', sa.String(512), nullable=True),
        sa.Column('ratings', sa.JSON, nullable=True),
        sa.Column('metascore', sa.String(32), nullable=True),
        sa.Column('imdb_rating', sa.String(16), nullable=True),
        sa.Column('imdb_votes', sa.String(32), nullable=True),
        sa.Column('imdb_id', sa.String(16), nullable=False, unique=True),
        sa.Column('movie_type', sa.String(32), nullable=True),
        sa.Column('dvd_release', sa.String(32), nullable=True),
        sa.Column('box_office', sa.String(32), nullable=True),
        sa.Column('production', sa.String(256), nullable=True),
        sa.Column('website', sa.String(256), nullable=True),
        sa.Column('response', sa.Boolean, nullable=True)
    )

    op.create_table(
        'movie_cast',
        sa.Column('movie_uuid', sa.String(36), sa.ForeignKey('movie_data.uuid'), primary_key=True),
        sa.Column('cast_id', sa.String(36), sa.ForeignKey('cast_name.uuid'), primary_key=True)
    )

def downgrade():
    op.drop_table('movie_cast')
    op.drop_table('movie_data')
    op.drop_table('search_history')
    op.drop_table('movie_recommendations')
    op.drop_table('movies_not_found')
    op.drop_table('cast_name')
