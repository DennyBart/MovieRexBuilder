LOG_FILE = './logs/app.log'
TOP_MOVIES_FORMAT = 'Top {} {} movies'
TOP_FORMAT = 'Top {} {}'
MOVIE_CRITIC_BOT_MESSAGE = 'You are a movie critic bot that responds with ' \
    'popular and hidden gems of movies, with ONLY format Name: name, Year: year.' # noqa
REC_TITLE_BOT_MESSAGE = 'You give catchy titles for a group of movie lists on a website homepage' # noqa

GENERATE_MOVIE_RECOMMENDATION = 'Generate a list of interesting movie top ' \
    'list title recommendations. Like "Best Comedy Movies". ' \
    'Respond with the list in [] brackets title seperated with a comma'

GENERATE_PAGE_BLURB = "In under 250 words paragraph you are a movie ' \
    'reviewer and you are writing a summary intro to the best movies ' \
    'listed. Dont list the movies but combine in the summary."
GENERATION_REC_TITLES = "You are a movie blog writer that provides catch" \
    " titles for list of movies. Respond with a list of titles"
GENERATION_REC_QUESTION = "Generate 25 catchy movie recomendation titles. ' \
    'Use these as an example: (Must-Watch Movies of All Time) ' \
        '(Iconic Movies That Define the Genre)"

RENAME_TOPIC = 'Give me a collective title under 5 words for these movie recommendation titles {}' # noqa

CAST_PAGE_LIMIT = 5
DIRECTOR_HOMEPAGE_HEADER = 'Featured In'
ACTOR_HOMEPAGE_HEADER = 'Featured In'

# This will trigger the omdb response of the plot of full or short
# default is short if not set
OMDB_PLOT = 'full'

TMDB_API_RATE_CALLS = 40
TMDB_API_RATE_TIME = 1

MINIMIUM_MOVIE_GENERATION_SUM = 7
BLURB_GEN_MAX_TRIES = 3
MAX_TITLE_COUNT = 3
