from datetime import timedelta
import os


DEBUG = False

# SERVER_NAME = 'katana-ui:8080'
SECRET_KEY = 'insecurekeyfordev'

db_uri = 'postgresql://{0}:{1}@postgres:5432/{2}'.format(os.environ['POSTGRES_USER'],
                                                         os.environ['POSTGRES_PASSWORD'],
                                                         os.environ['POSTGRES_DB'])
SQLALCHEMY_DATABASE_URI = db_uri
SQLALCHEMY_TRACK_MODIFICATIONS = False

SEED_USER_EMAIL = 'admin@local.host'
SEED_USER_USERNAME = 'admin'
SEED_USER_PASSWORD = 'password'

# Allow browsers to securely persist auth tokens but also include it in the
# headers so that other clients can use the auth token too.
JWT_TOKEN_LOCATION = ['cookies', 'headers']

# Only allow JWT cookies to be sent over https. In production, this should
# likely be True.
JWT_COOKIE_SECURE = False

# When set to False, cookies will persist even after the browser is closed.
JWT_SESSION_COOKIE = True

# Expire tokens in 1 year (this is unrelated to the cookie's duration).
JWT_ACCESS_TOKEN_EXPIRES = timedelta(weeks=52)

# We are authenticating with this auth token for a number of endpoints.
JWT_ACCESS_COOKIE_PATH = '/'

# Enable CSRF double submit protection. See this for a thorough
# explanation: http://www.redotheweb.com/2015/11/09/api-security.html
JWT_COOKIE_CSRF_PROTECT = True
