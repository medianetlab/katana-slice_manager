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
        return dumps(return_data)


    # @route('/all/') #/nfvo/all
    def all(self):
        """
        Same with index(self) above, but returns all nfvo details
        """
        return dumps(mongoUtils.index("nfvo"))


    def get(self, uuid):
        """
        Returns the details of specific nfvo,
        used by: `katana nfvo inspect [uuid]`
        """
        return dumps((mongoUtils.get("nfvo", uuid)))

    def post(self):
        """
        Add a new nfvo. The request must provide the nfvo details.
        used by: `katana nfvo add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch

        if request.json['type'] == "OSM":
            # Create the NFVO object
            osm_username = request.json['nfvousername']
            osm_password = request.json['nfvopassword']
            osm_ip = request.json['nfvoip']
            osm_project_name = request.json['tenantname']
            osm = osmUtils.Osm(osm_ip, osm_username,
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
                request.json['nfvo'] = Binary(thebytes)
                osmUtils.bootstrapNfvo(osm)
                return mongoUtils.add("nfvo", request.json)
        else:
            response = dumps({'error': 'This type nfvo is not supported'})
            return response, 400

    def delete(self, uuid):
        """
        Delete a specific nfvo.
        used by: `katana nfvo rm [uuid]`
        """
        result = mongoUtils.delete("nfvo", uuid)
        if result == 1:
            return uuid
        elif result == 0:
            # if uuid is not found, return error
            return "Error: No such nfvo: {}".format(uuid)

    def put(self, uuid):
        """
        Update the details of a specific nfvo.
        used by: `katana nfvo update -f [yaml file] [uuid]`
        """
        request.json['_id'] = uuid
        
        """
        Make binary data acceptable by Mongo
          - REST api sends: 'nfvo': {'$binary':'gANja2F0YW5h....a base64 string...', '$type': '00'} which is rejected when passed to Mongo
        By decoding the base64 string and then using Binary() it works
          - Inside Mongo  : "nfvo" : BinData(0,"gANja2F0YW5h....a base64 string...")
        """
        request.json['nfvo'] = Binary(base64.b64decode(request.json['nfvo']['$binary']))
        result = mongoUtils.update("nfvo", uuid, request.json)

        if result == 1:
            return uuid
        elif result == 0:
            # if no object was modified, return error
            return "Error: No such nfvo: {}".format(uuid)
