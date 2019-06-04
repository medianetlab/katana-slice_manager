# -*- coding: utf-8 -*-
from flask_classful import FlaskView
from pymongo import MongoClient


class DBView(FlaskView):
    route_prefix = '/api/'
    """
    Init database and collections
    """
    def post(self):

        client = MongoClient("mongodb://mongo")
        db = client.katana

        collection = db.vim
        return collection
