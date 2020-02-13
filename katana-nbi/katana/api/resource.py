# -*- coding: utf-8 -*-
from flask_classful import FlaskView
import logging
from bson.json_util import dumps

from katana.shared_utils.mongoUtils import mongoUtils

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


def get_vims(filter_data=None):
    '''
    Return the list of available VIMs
    '''
    vims = []
    for vim in mongoUtils.find_all("vim", data=filter_data):
        # TODO: Get resources from monitoring module
        max_resources = None
        avail_resources = None
        vims.append({"name": vim["name"], "id": vim["id"],
                     "location": vim["location"], "type": vim["type"],
                     "tenants": vim["tenants"],
                     "max_resources": max_resources,
                     "avail_resources": avail_resources})
    return vims


def get_func(filter_data={}):
    '''
    Return the list of available Network Functions
    '''
    filter_data["type"] = 1
    data = mongoUtils.find_all("func", data=filter_data)
    functions = []
    for iserv in data:
        functions.append(dict(
            DB_ID=iserv['_id'],
            gen=(lambda x: "4G" if x == 4 else "5G")(iserv["gen"]),
            functionality=(
                lambda x: "Core" if x == 0 else "Radio")(iserv["func"]),
            pnf_list=iserv["pnf_list"],
            function_id=iserv['id'], location=iserv["location"],
            tenants=iserv["tenants"],
            shared=iserv["shared"],
            created_at=iserv['created_at']))
    return functions


class ResourcesView(FlaskView):
    route_prefix = '/api/'

    def index(self):
        """
        Returns the available resources on platform,
        used by: `katana resource ls`
        """
        # Get VIMs
        vims = get_vims()
        # Get Functions
        functions = get_func()
        resources = {"VIMs": vims, "Functions": functions}
        return dumps(resources), 200

    def get(self, uuid):
        """
        Returns the available resources on platform,
        used by: `katana resource location <location>`
        """
        # Get VIMs
        filter_data = {"location": uuid}
        vims = get_vims(filter_data)
        # Get Functions
        functions = get_func(filter_data)
        resources = {"VIMs": vims, "Functions": functions}
        return dumps(resources), 200
