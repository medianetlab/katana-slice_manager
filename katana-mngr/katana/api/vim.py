# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
from katana.api.openstackUtils import utils as openstackUtils
from katana.api.wimUtils import wimUtils
import uuid
from katana.api.mongoUtils import mongoUtils
from bson.json_util import dumps
import time
import logging


class VimView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of vims and their details,
        used by: `katana vim ls`
        """
        return dumps(mongoUtils.index("vim"))

    def get(self, uuid):
        """
        Returns the details of specific vim,
        used by: `katana vim inspect [uuid]`
        """
        return dumps((mongoUtils.get("vim", uuid)))

    def post(self):
        """
        Add a new vim. The request must provide the vim details.
        used by: `katana vim add -f [yaml file]`
        """
        print(request.json, flush=True)
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch

        # TODO implement authorizing VIM connection
        if request.json['type'] == "openstack":
            username = request.json['username']
            password = request.json['password']
            auth_url = request.json['auth_url']
            project_name = request.json['admin_project_name']
            try:
                openstackUtils.openstack_authorize(
                    auth_url=auth_url,
                    project_name=project_name,
                    username=username,
                    password=password)
            except AttributeError as e:
                response = dumps({'error': 'Openstack authorization failed.'})
                return response, 400
            else:
                if (mongoUtils.count("wim") > 0):
                    wimUtils.register_vim(request.json)
                else:
                    logging.warning('There is no registered WIM\n')
                return mongoUtils.add("vim", request.json)
        else:
            response = dumps({'error': 'This type VIM is not supported'})
            return response, 400

    def delete(self, uuid):
        """
        Delete a specific vim.
        used by: `katana vim rm [uuid]`
        """
        result = mongoUtils.delete("vim", uuid)
        if result == 1:
            return uuid
        elif result == 0:
            # if uuid is not found, return error
            return "Error: No such vim: {}".format(uuid)

    def put(self, uuid):
        """
        Update the details of a specific vim.
        used by: `katana vim update -f [yaml file] [uuid]`
        """
        request.json['_id'] = uuid
        result = mongoUtils.update("vim", uuid, request.json)

        if result == 1:
            return uuid
        elif result == 0:
            # if no object was modified, return error
            return "Error: No such vim: {}".format(uuid)
