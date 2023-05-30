"""create_project

Revision ID: 9c112b44c7fb
Revises: 
Create Date: 2023-05-25 19:10:07.443008

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '9c112b44c7fb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # op.create_extension('uuid-ossp') # Uncomment this if your PostgreSQL database doesn't have this extension enabled by default.
    op.create_table(
        'cast_name',
        sa.Column('uuid', UUID(as_uuid=True), primary_key=True, unique=True, nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('cast_type', sa.String(16), nullable=False)
    )

    op.create_table(
        'movie_recommendations',
        sa.Column('uuid', UUID(as_uuid=True), primary_key=True, unique=True, nullable=False),
        sa.Column('topic_name', sa.String(256), nullable=False),
        sa.Column('count', sa.Integer, nullable=False, default=0),
        sa.Column('date_generated', sa.DateTime, nullable=True),
        sa.Column('casting_id', sa.String(256), nullable=True)
    )

    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('searched_at', sa.DateTime, nullable=False)
    )

    op.create_table(
        'movie_data',
        sa.Column('uuid', UUID(as_uuid=True), primary_key=True, unique=True, nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('rated', sa.String(16), nullable=True),
        sa.Column('released', sa.String(32), nullable=True),
        sa.Column('runtime', sa.String(32), nullable=True),
        sa.Column('genre', sa.String(256), nullable=True),
        sa.Column('director', UUID(as_uuid=True), sa.ForeignKey('cast_name.uuid'), nullable=True),
        sa.Column('writer', sa.String(512), nullable=True),
        sa.Column('plot', sa.Text, nullable=True),
        sa.Column('language', sa.String(256), nullable=True),
        sa.Column('country', sa.String(256), nullable=True),
        sa.Column('awards', sa.String(256), nullable=True),
        sa.Column('poster', sa.String(512), nullable=True),
        sa.Column('ratings', sa.JSON, nullable=True),
        sa.Column('metascore', sa.String(32), nullable=True),
        sa.Column('imdbrating', sa.String(16), nullable=True),
        sa.Column('imdbvotes', sa.String(32), nullable=True),
        sa.Column('imdbid', sa.String(16), nullable=False, unique=True),
        sa.Column('type', sa.String(32), nullable=True),
        sa.Column('dvd', sa.String(32), nullable=True),
        sa.Column('boxoffice', sa.String(32), nullable=True),
        sa.Column('production', sa.String(256), nullable=True),
        sa.Column('website', sa.String(256), nullable=True)
    )

    op.create_table(
        'movie_cast',
        sa.Column('movie_uuid', UUID(as_uuid=True), sa.ForeignKey('movie_data.uuid'), primary_key=True),
        sa.Column('cast_id', UUID(as_uuid=True), sa.ForeignKey('cast_name.uuid'), primary_key=True)
    )

    op.create_table(
        'movie_recommendation_relation',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('recommendation_uuid', UUID(as_uuid=True), sa.ForeignKey('movie_recommendations.uuid'), nullable=False),
        sa.Column('movie_uuid', UUID(as_uuid=True), sa.ForeignKey('movie_data.uuid'), nullable=False),
        sa.UniqueConstraint('recommendation_uuid', 'movie_uuid', name='unique_recommendation_movie'),
    )


    op.create_table(
        'movie_recommendations_search_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('generated', sa.Boolean(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'movie_recommendations_not_found',
        sa.Column('uuid', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('generated', sa.Boolean, nullable=False, default=False),
        sa.Column('generated_at', sa.DateTime, nullable=False),
        sa.Column('openai_response', sa.String(1024), nullable=True)
    )

    op.create_table(
        'movies_not_found',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('rec_topic', sa.String(256), nullable=True),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('searched_at', sa.DateTime, nullable=False),
    )

    pass


def downgrade() -> None:
    op.drop_table('movies_not_found')
    op.drop_table('movie_recommendations_not_found')
    op.drop_table('movie_recommendations_search_list')
    op.drop_table('movie_recommendation_relation')
    op.drop_table('movie_cast')
    op.drop_table('movie_data')
    op.drop_table('search_history')
    op.drop_table('movie_recommendations')
    op.drop_table('cast_name')
    pass
