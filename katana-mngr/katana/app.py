# -*- coding: utf-8 -*-
from flask import Flask, request
import io
import yaml
import json
import uuid
from katana.api.db import DBView
from katana.api.vim import VimView
from katana.api.wim import WimView
from katana.api.nfvo import NFVOView
from katana.api.ems import EmsView
from katana.api.slice import SliceView
from katana.api.service import ServiceView


def create_app():
    """
    Create a Flask application using the app factory pattern.

    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    DBView.register(app, trailing_slash=False)
    VimView.register(app, trailing_slash=False)
    WimView.register(app, trailing_slash=False)
    EmsView.register(app, trailing_slash=False)
    NFVOView.register(app, trailing_slash=False)
    SliceView.register(app, trailing_slash=False)
    ServiceView.register(app, trailing_slash=False)

    return app
