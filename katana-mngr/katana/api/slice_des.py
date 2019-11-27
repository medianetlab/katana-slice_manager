# -*- coding: utf-8 -*-
from flask_classful import FlaskView
import logging
from bson.json_util import dumps

from katana.api.mongoUtils import mongoUtils

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


class Slice_desView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of Slice Descriptors and their details,
        used by: `katana slice_des ls`
        """
        slice_des_data = mongoUtils.index("slice_des_ref")
        return_data = []
        for islicedes in slice_des_data:
            return_data.append(dict(_id=islicedes['_id']))
        return dumps(return_data), 200

    def get(self, uuid):
        """
        Returns the details of specific Slice Descriptor,
        used by: `katana slice_des inspect [uuid]`
        """
        data = (mongoUtils.get("slice_des_ref", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def delete(self, uuid):
        """
        Delete a specific Slice Descriptor.
        used by: `katana slice_des rm [uuid]`
        """
        result = mongoUtils.delete("slice_des", uuid)
        if result:
            return "Deleted Slice Descriptor {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such Slice Descriptor: {}".format(uuid), 404
