from flask import request
from flask_classful import FlaskView, route
from katana.api.mongoUtils import mongoUtils
from katana.api.sliceUtils import sliceUtils

import uuid
from bson.json_util import dumps
from threading import Thread
import time
import logging
import urllib3

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


class SliceView(FlaskView):
    """
    Returns a list of slices and their details,
    used by: `katana slice ls`
    """
    urllib3.disable_warnings()
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of slices and their details,
        used by: `katana slice ls`
        """
        slice_data = mongoUtils.index("slice")
        return_data = []
        for islice in slice_data:
            return_data.append(dict(_id=islice['_id'],
                                    created_at=islice['created_at'],
                                    status=islice['status']))
        return dumps(return_data)

    def get(self, uuid):
        """
        Returns the details of specific slice,
        used by: `katana slice inspect [uuid]`
        """
        return dumps((mongoUtils.get("slice", uuid)))

    @route('/<uuid>/time')
    def show_time(self, uuid):
        """
        Returns deployment time of a slice
        """
        islice = mongoUtils.get("slice", uuid)
        return dumps(islice["deployment_time"])

    def post(self):
        """
        Add a new slice. The request must provide the slice details.
        used by: `katana slice add -f [yaml file]`
        """
        new_uuid = str(uuid.uuid4())
        request.json['_id'] = new_uuid
        request.json['status'] = 'init'
        request.json['created_at'] = time.time()  # unix epoch
        request.json['deployment_time'] = dict(
            Slice_Deployment_Time='N/A',
            Placement_Time='N/A',
            Provisioning_Time='N/A',
            NS_Deployment_Time='N/A',
            WAN_Deployment_Time='N/A',
            Radio_Configuration_Time='N/A')
        mongoUtils.add("slice", request.json)
        # background work
        # temp hack from:
        # https://stackoverflow.com/questions/48994440/execute-a-function-after-flask-returns-response
        # might be replaced with Celery...

        thread = Thread(target=sliceUtils.do_work, kwargs={'nest':
                                                           request.json})
        thread.start()

        return new_uuid

    def delete(self, uuid):
        """
        Delete a specific slice.
        used by: `katana slice rm [uuid]`
        """

        # check if slice uuid exists
        delete_json = mongoUtils.get("slice", uuid)

        if not delete_json:
            return "Error: No such slice: {}".format(uuid)
        else:
            delete_thread = Thread(target=sliceUtils.delete_slice,
                                   kwargs={'slice_json': delete_json})
            delete_thread.start()
            return "Deleting {0}".format(uuid)

    # def put(self, uuid):
    #     """
    #     Update the details of a specific slice.
    #     used by: `katana slice update -f [yaml file] [uuid]`
    #     """
    #     request.json['_id'] = uuid
    #     result = mongoUtils.update("slice", uuid, request.json)

    #     if result == 1:
    #         return uuid
    #     elif result == 0:
    #         # if no object was modified, return error
    #         return "Error: No such slice: {}".format(uuid)
