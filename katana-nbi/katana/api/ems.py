# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
from bson.binary import Binary
import pickle
import time
import logging

from katana.utils.mongoUtils import mongoUtils
from katana.utils.emsUtils import emsUtils

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
                               ems_id=iems['id'],
                               created_at=iems['created_at']))
        return dumps(return_data), 200

    # @route('/all/') #/ems/all
    def all(self):
        """
        Same with index(self) above, but returns all EMS details
        """
        return dumps(mongoUtils.index("ems")), 200

    def get(self, uuid):
        """
        Returns the details of specific EMS,
        used by: `katana ems inspect [uuid]`
        """
        data = (mongoUtils.get("ems", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def post(self):
        """
        Add a new EMS. The request must provide the ems details.
        used by: `katana ems add -f [yaml file]`
        """
        # TODO: Test connectivity with the EMS
        new_uuid = str(uuid.uuid4())
        # Create the object and store it in the object collection
        ems = emsUtils.Ems(request.json['url'])
        thebytes = pickle.dumps(ems)
        obj_json = {"_id": new_uuid, "id": request.json["id"],
                    "obj": Binary(thebytes)}
        mongoUtils.add('ems_obj', obj_json)
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        return mongoUtils.add('ems', request.json), 201

    def delete(self, uuid):
        """
        Delete a specific EMS.
        used by: `katana ems rm [uuid]`
        """
        # TODO: Check if there is anything running by this ems before delete
        mongoUtils.delete("ems_obj", uuid)
        result = mongoUtils.delete("ems", uuid)
        if result:
            return "Deleted EMS {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such EMS: {}".format(uuid), 404

    def put(self, uuid):
        """
        Update the details of a specific EMS.
        used by: `katana ems update -f [yaml file] [uuid]`
        """
        # TODO: Validate what data should not change
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("ems", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            mongoUtils.update("ems", uuid, data)
            return f"Modified {uuid}", 200
        else:
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            return "Created " + str(mongoUtils.add('ems', data)), 201
