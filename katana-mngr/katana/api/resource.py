# -*- coding: utf-8 -*-
from flask_classful import FlaskView
import logging
from bson.json_util import dumps

from katana.api.mongoUtils import mongoUtils

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


class ResourcesView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns the available resources on platform,
        used by: `katana resource ls`
        """
        # Get VIMs
        vims = []
        for vim in mongoUtils.index("vim"):
            # TODO: Get resources from monitoring module
            max_resources = None
            avail_resources = None
            vims.append({"name": vim["name"], "id": vim["id"],
                         "location": vim["location"], "type": vim["type"],
                         "tenants": vim["tenants"],
                         "max_resources": max_resources,
                         "avail_resources": avail_resources})
        # Get PDUs
        pdus = []
        for pdu in mongoUtils.index("pdu"):
            pdus.append({"name": pdu["name"], "id": pdu["id"],
                         "location": pdu["location"],
                         "tenants": pdu["tenants"]})

        resources = {"VIMs": vims,
                     "PDUs": pdus}
        return dumps(resources), 200

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
