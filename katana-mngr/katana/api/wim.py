# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
import time

from katana.api.mongoUtils import mongoUtils


class WimView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of wims and their details,
        used by: `katana wim ls`
        """
        return dumps(mongoUtils.index("wim"))

    def get(self, uuid):
        """
        Returns the details of specific wim,
        used by: `katana wim inspect [uuid]`
        """
        return dumps((mongoUtils.get("wim", uuid)))

    def post(self):
        """
        Add a new wim. The request must provide the wim details.
        used by: `katana wim add -f [yaml file]`
        """
        # TODO: Test connectivity with the WIM
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        return mongoUtils.add('wim', request.json)
