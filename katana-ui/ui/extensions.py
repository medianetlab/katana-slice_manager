from flask_debugtoolbar import DebugToolbarExtension
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

debug_toolbar = DebugToolbarExtension()
jwt = JWTManager()
db = SQLAlchemy()
marshmallow = Marshmallow()
