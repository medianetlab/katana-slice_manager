from flask import request
from flask_classful import FlaskView
from katana.utils.mongoUtils import mongoUtils
from bson.json_util import dumps
import logging
import time
import uuid


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


class PduView(FlaskView):
    route_prefix = '/api/'
    req_fields = ["id"]

    def index(self):
        """
        Returns a list of pdu and their details,
        used by: `katana pdu ls`
        """
        pdu_data = mongoUtils.index("pdu")
        return_data = []
        for ipdu in pdu_data:
            return_data.append(dict(_id=ipdu['_id'],
                               pdu_id=ipdu['id'],
                               created_at=ipdu['created_at'],
                               location=ipdu['location']))
        return dumps(return_data)

    def get(self, uuid):
        """
        Returns the details of specific pdu,
        used by: `katana pdu inspect [uuid]`
        """
        data = (mongoUtils.get("pdu", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404

    def post(self):
        """
        Add a new pdu. The request must provide the pdu details.
        used by: `katana pdu add -f [yaml file]`
        """
        try:
            pdu_id = request.json["id"]
        except KeyError:
            return f"Error: Required fields: {self.req_fields}", 400
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['created_at'] = time.time()  # unix epoch
        request.json["tenants"] = []
        return mongoUtils.add('pdu', request.json), 201

    def delete(self, uuid):
        """
        Delete a specific pdu.
        used by: `katana pdu rm [uuid]`
        """
        del_pdu = mongoUtils.delete("pdu", uuid)
        if del_pdu:
            if del_pdu["tenants"]:
                return "Cannot delete pdu {} - In use".format(uuid), 400
            return "Deleted PDU {}".format(uuid), 200
        else:
            # if uuid is not found, return error
            return "Error: No such pdu: {}".format(uuid), 404

    def put(self, uuid):
        """
        Update the details of a specific pdu.
        used by: `katana pdu update [uuid] -f [yaml file]`
        """
        data = request.json
        data['_id'] = uuid
        old_data = mongoUtils.get("pdu", uuid)

        if old_data:
            data["created_at"] = old_data["created_at"]
            data["tenants"] = old_data["tenants"]
            try:
                for entry in self.req_fields:
                    if data[entry] != old_data[entry]:
                        return "Cannot update field: " + entry, 400
            except KeyError:
                return f"Error: Required fields: {self.req_fields}", 400
            else:
                mongoUtils.update("pdu", uuid, data)
            return f"Modified {uuid}", 200
        else:
            try:
                pdu_id = request.json["id"]
            except KeyError:
                return f"Error: Required fields: {self.req_fields}", 400
            new_uuid = uuid
            data = request.json
            data['_id'] = new_uuid
            data['created_at'] = time.time()  # unix epoch
            data["tenants"] = []
            return "Created " + str(mongoUtils.add('pdu', data)), 201
