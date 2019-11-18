# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
from katana.api.openstackUtils import utils as openstackUtils
from katana.api.opennebulaUtils import utils as opennebulaUtils
from katana.api.mongoUtils import mongoUtils
import uuid
from bson.json_util import dumps
from bson.binary import Binary
import pickle
import time
import logging

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


class VimView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of vims and their details,
        used by: `katana vim ls`
        """
        vim_data = mongoUtils.index("vim")
        return_data = []
        for ivim in vim_data:
            return_data.append(dict(_id=ivim['_id'],
                               created_at=ivim['created_at'],
                               type=ivim['type']))
        return dumps(return_data), 200

    # @route('/all/') #/vim/all
    def all(self):
        """
        Same with index(self) above, but returns all vim details
        """
        return dumps(mongoUtils.index("vim")), 200

    def get(self, uuid):
        """
        Returns the details of specific vim,
        used by: `katana vim inspect [uuid]`
        """
        data = (mongoUtils.get("vim", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def post(self):
        """
        Add a new vim. The request must provide the vim details.
        used by: `katana vim add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch

        # TODO implement authorizing VIM connection
        username = request.json['username']
        password = request.json['password']
        auth_url = request.json['auth_url']
        project_name = request.json['admin_project_name']
        if request.json['type'] == "openstack":
            try:
                new_vim = openstackUtils.Openstack(uuid=new_uuid,
                                                   auth_url=auth_url,
                                                   project_name=project_name,
                                                   username=username,
                                                   password=password)
                if new_vim.auth_error:
                    raise(AttributeError)
            except AttributeError as e:
                response = dumps({'error': 'Openstack auth failed.'+e})
                return response, 400
            else:
                thebytes = pickle.dumps(new_vim)
                obj_json = {"_id": new_uuid, "id": request.json["id"],
                            "obj": Binary(thebytes)}
                mongoUtils.add("vim_obj", obj_json)
                return mongoUtils.add("vim", request.json)
        elif request.json['type'] == "opennebula":
            try:
                new_vim = opennebulaUtils.Opennebula(uuid=new_uuid,
                                                     auth_url=auth_url,
                                                     project_name=project_name,
                                                     username=username,
                                                     password=password)
            except AttributeError as e:
                response = dumps({'Error': 'OpenNebula auth failed.'+e})
                return response, 400
            else:
                thebytes = pickle.dumps(new_vim)
                obj_json = {"_id": new_uuid, "id": request.json["id"],
                            "obj": Binary(thebytes)}
                mongoUtils.add("vim_obj", obj_json)
                return mongoUtils.add("vim", request.json)
        else:
            response = dumps({'error': 'This type VIM is not supported'})
            return response, 400

    def delete(self, uuid):
        """
        Delete a specific vim.
        used by: `katana vim rm [uuid]`
        """
        # TODO: Check if there is anything running by this ems before delete
        mongoUtils.delete("vim_obj", uuid)
        result = mongoUtils.delete("vim", uuid)
        if result:
            return "Deleted VIM {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such vim: {}".format(uuid), 404

    def put(self, uuid):
        """
        Update the details of a specific vim.
        used by: `katana vim update -f [yaml file] [uuid]`
        """
        # TODO: Validate what data should not change
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("vim", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            mongoUtils.update("vim", uuid, data)
            return f"Modified {uuid}", 200
        else:
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            return "Created " + str(mongoUtils.add('vim', data)), 201
