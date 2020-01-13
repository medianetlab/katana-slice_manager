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
from katana.utils.wimUtils import wimUtils

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


class WimView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of wims and their details,
        used by: `katana wim ls`
        """
        wim_data = mongoUtils.index("wim")
        return_data = []
        for iwim in wim_data:
            return_data.append(dict(_id=iwim['_id'],
                               wim_id=iwim['id'],
                               created_at=iwim['created_at']))
        return dumps(return_data), 200

    # @route('/all/') #/wim/all
    def all(self):
        """
        Same with index(self) above, but returns all wim details
        """
        return dumps(mongoUtils.index("wim")), 200

    def get(self, uuid):
        """
        Returns the details of specific wim,
        used by: `katana wim inspect [uuid]`
        """
        data = (mongoUtils.get("wim", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def post(self):
        """
        Add a new wim. The request must provide the wim details.
        used by: `katana wim add -f [yaml file]`
        """
        # TODO: Test connectivity with the WIM
        new_uuid = str(uuid.uuid4())
        # Create the object and store it in the object collection
        wim = wimUtils.Wim(request.json['url'])
        thebytes = pickle.dumps(wim)
        obj_json = {"_id": new_uuid, "id": request.json["id"],
                    "obj": Binary(thebytes)}
        mongoUtils.add('wim_obj', obj_json)
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        request.json['slices'] = {}
        return mongoUtils.add('wim', request.json), 201

    def delete(self, uuid):
        """
        Delete a specific wim.
        used by: `katana wim rm [uuid]`
        """
        wim = mongoUtils.get("wim", uuid)
        if wim:
            if wim["slices"]:
                return "Cannot delete wim {} - In use".format(uuid), 400
            mongoUtils.delete("wim_obj", uuid)
            mongoUtils.delete("wim", uuid)
            return "Deleted WIM {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such wim: {}".format(uuid), 404

    def put(self, uuid):
        """
        Update the details of a specific wim.
        used by: `katana wim update -f [yaml file] [uuid]`
        """
        # TODO: Validate what data should not change
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("wim", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            mongoUtils.update("wim", uuid, data)
            return f"Modified {uuid}", 200
        else:
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            return "Created " + str(mongoUtils.add('wim', data)), 201
