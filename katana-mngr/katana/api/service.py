# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView
import uuid
from bson.json_util import dumps
import time

from katana.api.mongoUtils import mongoUtils


class ServiceView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of service and their details,
        used by: `katana service ls`
        """
        service_data = mongoUtils.index("service")
        return_data = []
        for iservice in service_data:
            return_data.append(dict(_id=iservice['_id'],
                               created_at=iservice['created_at'],
                               type=iservice['type']))
        return dumps(return_data)

    def get(self, uuid):
        """
        Returns the details of specific service,
        used by: `katana service inspect [uuid]`
        """
        return dumps((mongoUtils.get("service", uuid)))

    def post(self):
        """
        Add a new service. The request must provide the service details.
        used by: `katana service add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        data = request.json
        for service in data:
            new_uuid = str(uuid.uuid4())
            service['_id'] = new_uuid
            service['created_at'] = time.time()  # unix epoch
        return str(mongoUtils.add_many('service', data))
