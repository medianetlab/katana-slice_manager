# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from flask_jwt_extended import current_user

from ui.blueprints.page import page
from ui.blueprints.user import user
from ui.blueprints.user.models import User
from ui.api.auth import AuthView
from ui.api.v1.user import UserView
from ui.api.mngr.vim_view import VimView
from ui.api.mngr.wim_view import WimView

from ui.extensions import (
    debug_toolbar,
    db,
    jwt,
    marshmallow
)


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if settings_override:
        app.config.update(settings_override)

    app.register_blueprint(page)
    app.register_blueprint(user)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    AuthView.register(app)
    UserView.register(app)
    VimView.register(app)
    WimView.register(app)

    extensions(app)
    jwt_callbacks()

    app.jinja_env.globals.update(current_user=current_user)

    return app


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    debug_toolbar.init_app(app)
    jwt.init_app(app)
    db.init_app(app)
    marshmallow.init_app(app)

    return None


def jwt_callbacks():
    """
    Set up custom behavior for JWT based authentication.

    :return: None
    """
    @jwt.user_loader_callback_loader
    def user_loader_callback(identity):
        return User.query.filter((User.username == identity)).first()

    @jwt.unauthorized_loader
    def jwt_unauthorized_callback(self):
        response = {
            'error': {
                'message': 'Your auth token or CSRF token are missing'
            }
        }

        return jsonify(response), 401

    @jwt.expired_token_loader
    def jwt_expired_token_callback():
        response = {
            'error': {
                'message': 'Your auth token has expired'
            }
        }

        return jsonify(response), 401

    return None
