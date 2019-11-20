# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
from katana.api.osmUtils import osmUtils
# from katana.api.tango5gUtils import tango5gUtils
from requests import ConnectionError, ConnectTimeout
import uuid
from katana.api.mongoUtils import mongoUtils
from bson.json_util import dumps
from bson.binary import Binary
import pickle
import time
import logging
import ast
import base64

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


class NFVOView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of nfvo and their details,
        used by: `katana nfvo ls`
        """
        nfvo_data = mongoUtils.index("nfvo")
        return_data = []
        for infvo in nfvo_data:
            return_data.append(dict(_id=infvo['_id'],
                               created_at=infvo['created_at'],
                               type=infvo['type']))
        return dumps(return_data), 200

    # @route('/all/') #/nfvo/all
    def all(self):
        """
        Same with index(self) above, but returns all nfvo details
        """
        return dumps(mongoUtils.index("nfvo")), 200

    def get(self, uuid):
        """
        Returns the details of specific nfvo,
        used by: `katana nfvo inspect [uuid]`
        """
        data = (mongoUtils.get("nfvo", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def post(self):
        """
        Add a new nfvo. The request must provide the nfvo details.
        used by: `katana nfvo add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        request.json['tenants'] = {}

        if request.json['type'] == "OSM":
            # Create the NFVO object
            osm_username = request.json['nfvousername']
            osm_password = request.json['nfvopassword']
            osm_ip = request.json['nfvoip']
            osm_project_name = request.json['tenantname']
            nfvo_id = request.json["id"]
            osm = osmUtils.Osm(nfvo_id, osm_ip, osm_username,
                               osm_password, osm_project_name)
            try:
                osm.getToken()
            except ConnectTimeout as e:
                logger.exception("It is time for ... Time out")
                response = dumps({'error': 'Unable to connect to NFVO'})
                return (response, 400)
            except ConnectionError as e:
                logger.exception("Unable to connect")
                response = dumps({'error': 'Unable to connect to NFVO'})
                return (response, 400)
            else:
                # Store the osm object to the mongo db
                thebytes = pickle.dumps(osm)
                obj_json = {"_id": new_uuid, "id": request.json["id"],
                            "obj": Binary(thebytes)}
                mongoUtils.add('nfvo_obj', obj_json)
                # Get information regarding VNFDs and NSDs
                osmUtils.bootstrapNfvo(osm)
                return mongoUtils.add("nfvo", request.json), 201
        else:
            response = dumps({'error': 'This type nfvo is not supported'})
            return response, 400

    def delete(self, uuid):
        """
        Delete a specific nfvo.
        used by: `katana nfvo rm [uuid]`
        """
        # TODO: Check if there is anything running by this ems before delete
        del_nfvo = mongoUtils.find("nfvo", uuid)
        if del_nfvo:
            mongoUtils.delete("nfvo_obj", uuid)
            mongoUtils.delete_all("nsd", {"nfvo_id": del_nfvo["id"]})
            mongoUtils.delete_all("vnfd", {"nfvoid": del_nfvo["id"]})
            mongoUtils.delete("nfvo", uuid)
            return "Deleted NFVO {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such nfvo: {}".format(uuid), 404

    def put(self, uuid):
        """
        Update the details of a specific nfvo.
        used by: `katana nfvo update -f [yaml file] [uuid]`
        """
        # TODO: Validate what data should not change
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("nfvo", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            mongoUtils.update("nfvo", uuid, data)
            return f"Modified {uuid}", 200
        else:
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            return "Created " + str(mongoUtils.add('nfvo', data)), 201
