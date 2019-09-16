# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
from bson.binary import Binary
import pickle
import time
import logging
import ast
import base64

from katana.api.mongoUtils import mongoUtils
from katana.api.emsUtils import emsUtils

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


class EmsView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of EMS and their details,
        used by: `katana ems ls`
        """
        ems_data = mongoUtils.index("ems")
        return_data = []
        for iems in ems_data:
            return_data.append(dict(_id=iems['_id'],
                               created_at=iems['created_at']))
        return dumps(return_data)

    # @route('/all/') #/ems/all
    def all(self):
        """
        Same with index(self) above, but returns all EMS details
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
        Add a new EMS. The request must provide the ems details.
        used by: `katana ems add -f [yaml file]`
        """
        # TODO: Test connectivity with the EMS
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        ems = emsUtils.Ems(request.json['url'])
        thebytes = pickle.dumps(ems)
        request.json['ems'] = Binary(thebytes)
        return mongoUtils.add('ems', request.json)

    def delete(self, uuid):
        """
        Delete a specific EMS.
        used by: `katana ems rm [uuid]`
        """
        result = mongoUtils.delete("ems", uuid)
        if result == 1:
            return uuid
        elif result == 0:
            # if uuid is not found, return error
            return "Error: No such EMS: {}".format(uuid)

    def put(self, uuid):
        """
        Update the details of a specific EMS.
        used by: `katana ems update -f [yaml file] [uuid]`
        """
        request.json['_id'] = uuid

        """
        Make binary data acceptable by Mongo
          - REST api sends: 'ems': {'$binary':'gANja2F0YW5h....a base64 string...', '$type': '00'} which is rejected when passed to Mongo
        By decoding the base64 string and then using Binary() it works
          - Inside Mongo  : "ems" : BinData(0,"gANja2F0YW5h....a base64 string...")
        """
        request.json['ems'] = Binary(base64.b64decode(request.json['ems']['$binary']))
        result = mongoUtils.update("ems", uuid, request.json)

        if result == 1:
            return uuid
        elif result == 0:
            # if no object was modified, return error
            return "Error: No such EMS: {}".format(uuid)
