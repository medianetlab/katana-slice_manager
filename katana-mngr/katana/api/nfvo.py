# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
from katana.api.osmUtils import osmUtils
from katana.api.tango5gUtils import tango5gUtils
from requests import ConnectionError, ConnectTimeout
import uuid
from katana.api.mongoUtils import mongoUtils
from bson.json_util import dumps
import time


class NFVOView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of nfvo and their details,
        used by: `katana nfvo ls`
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

        # TODO implement authorizing nfvo connection
        if request.json['type'] == "OSM":
            username = request.json['nfvousername']
            password = request.json['nfvopassword']
            ip = request.json['nfvoip']
            project_name = request.json['tenantname']
            try:
                token = osmUtils.get_token(
                    ip=ip,
                    project_id=project_name,
                    username=username,
                    password=password)
            except ConnectTimeout as e:
                print("It is time for ... Time out")
                response = dumps({'error': 'Unable to connect to NFVO'})
                return (response, 400)
            except ConnectionError as e:
                print("Unable to connect")
                response = dumps({'error': 'Unable to connect to NFVO'})
                return (response, 400)
            else:
                request.json['token_id'] = token
                return mongoUtils.add("nfvo", request.json)
        elif request.json['type'] == "5GTango":
            try:
                url = request.json['nfvoip']
                tango5gUtils.register_sp(url)
            except ConnectionError as e:
                print("There was a connection error")
                response = dumps({'error': 'Unable to connect to NFVO'})
                return (response, 400)
            else:
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
        result = mongoUtils.update("nfvo", uuid, request.json)

        if result == 1:
            return uuid
        elif result == 0:
            # if no object was modified, return error
            return "Error: No such nfvo: {}".format(uuid)
