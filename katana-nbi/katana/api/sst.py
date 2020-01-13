# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
import time
import logging

from katana.utils.mongoUtils import mongoUtils


# Logging Parameters
logger = logging.getLogger(__name__)
file_handler = logging.handlers.RotatingFileHandler(
    'katana.log', maxBytes=10000, backupCount=5)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
stream_formatter = logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class SstView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of supported sst and their details,
        used by: `katana sst ls`
        """
        sst_data = mongoUtils.index("sst")
        return_data = []
        for iservice in sst_data:
            return_data.append(dict(_id=iservice['_id'],
                               created_at=iservice['created_at'],
                               sst=iservice['sst']))
        return dumps(return_data), 200

    def get(self, uuid):
        """
        Returns the details of specific sst,
        used by: `katana sst inspect [uuid]`
        """
        return dumps(mongoUtils.get("sst", uuid)), 200

    def post(self):
        """
        Add a new supported sst. The request must provide the sst details.
        used by: `katana sst add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        data = request.json
        data['_id'] = new_uuid
        data['created_at'] = time.time()  # unix epoch
        return str(mongoUtils.add('sst', data)), 201

    def delete(self, uuid):
        """
        Delete a specific sst.
        used by: `katana sst rm [uuid]`
        """
        result = mongoUtils.delete("sst", uuid)
        if result:
            return "Deleted SST {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such pdu: {}".format(uuid), 404

    def put(self, uuid):
        """
        Add or update a new supported sst.
        The request must provide the service details.
        used by: `katana sst update -f [yaml file]`
        """
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("sst", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            mongoUtils.update("sst", uuid, data)
            return f"Modified {uuid}", 200
        else:
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            return "Created " + str(mongoUtils.add('sst', data)), 201
