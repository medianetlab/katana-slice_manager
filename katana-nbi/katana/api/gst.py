# -*- coding: utf-8 -*-
from flask_classful import FlaskView
import logging
from bson.json_util import dumps

from katana.utils.mongoUtils import mongoUtils

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


class GstView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns a list of GST and their details,
        used by: `katana gst ls`
        """
        gst_data = mongoUtils.index("gst")
        return_data = []
        for gst in gst_data:
            return_data.append(dict(_id=gst['_id']))
        return dumps(return_data), 200

    def get(self, uuid):
        """
        Returns the details of specific GST,
        used by: `katana gst inspect [uuid]`
        """
        data = (mongoUtils.get("gst", uuid))
        if data:
            return dumps(data), 200
        else:
            return "Not Found", 404
