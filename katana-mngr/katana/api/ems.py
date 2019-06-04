# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
import time

from katana.api.mongoUtils import mongoUtils


class EmsView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of EMS and their details,
        used by: `katana ems ls`
        """
        return dumps(mongoUtils.index("ems"))

    def get(self, uuid):
        """
        Returns the details of specific EMS,
        used by: `katana ems inspect [uuid]`
        """
        return dumps((mongoUtils.get("ems", uuid)))

    def post(self):
        """
        Add a new EMS. The request must provide the wim details.
        used by: `katana wim add -f [yaml file]`
        """
        # TODO: Test connectivity with the EMS
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        return mongoUtils.add('ems', request.json)
