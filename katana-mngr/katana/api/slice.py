# -*- coding: utf-8 -*-
from flask import request
from flask_classful import FlaskView, route
from katana.api.openstackUtils import utils as openstackUtils
from katana.api.mongoUtils import mongoUtils
from katana.api.osmUtils import osmUtils
from katana.api.wimUtils import wimUtils
from katana.api.emsUtils import emsUtils

import json
import pickle
import uuid
from bson.json_util import dumps
from threading import Thread
import time
import logging
import urllib3


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
        self.slice_json = request.json
        # background work
        # temp hack from:
        # https://stackoverflow.com/questions/48994440/execute-a-function-after-flask-returns-response
        # might be replaced with Celery...
        def do_work(request_json):

            # TODO !!!
            # proper error handling and return

            # **** STEP-1: Placement ****
            self.slice_json['status'] = 'Placement'
            mongoUtils.update("slice", self.slice_json['_id'], self.slice_json)
            logging.info("Status: Placement")
            placement_start_time = time.time()

            data = {"location": "core"}
            get_vim = mongoUtils.find('vim', data=data)
            default_vim = get_vim
            vim_list = []
            placement_list = {}
            new_ns_list = self.slice_json['nsi']['nsd-ref']
            slice_type = self.slice_json['nsi']['type']
            data = {"type": slice_type}
            registered_service = mongoUtils.find('service', data=data)
            if registered_service is not None:
                registered_ns_list = registered_service['ns']
                for new_ns in new_ns_list:
                    # Find the NS in the registered NSs
                    registered_ns_index = next((index for (index, d) in
                                               enumerate(registered_ns_list) if
                                               d["name"] == new_ns["name"]),
                                               None)
                    if registered_ns_index is None:
                        logging.warning("Network Service {0} isn't registered.\
                        Will be placed at the default core NFVI\n".format(
                            new_ns["name"]))
                        selected_vim = default_vim
                        placement_list[new_ns["name"]] =\
                            {"vim": selected_vim["_id"]}
                    else:
                        vim_location =\
                            registered_ns_list[registered_ns_index]['location']
                        data = {"location": vim_location}
                        get_vim = mongoUtils.find('vim', data=data)
                        selected_vim = get_vim
                        placement_list[new_ns["name"]] =\
                            {"vim": selected_vim["_id"]}
                    if selected_vim not in vim_list:
                        vim_list.append(selected_vim)
            else:
                logging.warning('There are no registered slice services. All \
Network services will be placed on the default core NFVI and no network graph \
will be created\n')
                for new_ns in new_ns_list:
                    placement_list[new_ns["name"]] =\
                        {"vim": default_vim["_id"]}
                vim_list.append(default_vim)

            # TODO:Create the network graph
            self.slice_json['deployment_time']['Placement_Time'] = format(
                time.time() - placement_start_time, '.4f')

            # **** STEP-2: Provisioning ****
            self.slice_json['status'] = 'Provisioning'
            mongoUtils.update("slice", self.slice_json['_id'], self.slice_json)
            logging.info("Status: Provisioning")
            prov_start_time = time.time()

            # *** STEP-2a: Cloud ***
            # Select NFVO - Assume that there is only one registered
            nfvo_list = list(mongoUtils.index('nfvo'))
            nfvo = pickle.loads(nfvo_list[0]['nfvo'])

            # Create a new tenant/project on every VIM used in the placement
            slice_vim_id_dict = {}
            for ivim in vim_list:
                # STEP-2a-i: openstack prerequisites
                # Define project parameters
                tenant_project_name = 'katana_{0}'.format(self.slice_json['_id'])
                tenant_project_description = 'katana_{0}'.format(self.slice_json['_id'])
                tenant_project_user = 'katana_{0}'.format(self.slice_json['_id'])
                tenant_project_password = 'password'

                # Create the project on the NFVi
                ivim_obj = pickle.loads(ivim["vim"])
                ids = ivim_obj.create_slice_prerequisites(
                    tenant_project_name,
                    tenant_project_description,
                    tenant_project_user,
                    tenant_project_password,
                    self.slice_json['_id']
                )
                # Add the new tenant to the database
                ivim['tenants'].append(ids)
                mongoUtils.update("vim", ivim['_id'], ivim)

                # STEP-2a-ii: add VIM to NFVO
                slice_vim_id_dict[ivim["_id"]] = nfvo.addVim(
                    tenant_project_name, ivim["password"], ivim['type'],
                    ivim['auth_url'], ivim["username"], ids["secGroupName"])

            # *** STEP-2b: WAN ***
            if (mongoUtils.count('wim') <= 0):
                logging.warning('There is no registered WIM\n')
            else:
                wan_start_time = time.time()
                # Select WIM - Assume that there is only one registered
                wim_list = list(mongoUtils.index('wim'))
                wim = pickle.loads(wim_list[0]['wim'])

                # Create the WAN Slice Descriptor
                wsd = {}
                wsd['services-segment'] = []
                try:
                    services = self.slice_json["nsi"]["wim-ref"]["services-segment"]
                except Exception:
                    logging.warning("There are no services on the slice descriptor")
                else:
                    for service in services:
                        wsd["services-segment"].append(service)
                wsd['topology'] = self.slice_json['nsi']['wim-ref']['topology']
                wsd['bidirectional'] = self.slice_json['nsi']['wim-ref']['bidirectional']
                wsd['link_params'] = self.slice_json['nsi']['wim-ref']['link_params']
                # TODO Add the intermediate VIMs
                # Create the WAN Slice
                wim.create_slice(wsd)
                self.slice_json['deployment_time']['WAN_Deployment_Time'] =\
                    format(time.time() - wan_start_time, '.4f')
            self.slice_json['deployment_time']['Provisioning_Time'] =\
                format(time.time() - prov_start_time, '.4f')

            # **** STEP-3: Activation ****
            self.slice_json['status'] = 'Activation'
            mongoUtils.update("slice", self.slice_json['_id'], self.slice_json)
            logging.info("Status: Activation")
            # *** STEP-3a: Cloud ***
            # Instantiate NS
            self.slice_json['deployment_time']['NS_Deployment_Time'] = {}
            ns_id_dict = {}
            for num, ins in enumerate(new_ns_list):
                ns_start_time = time.time()
                slice_vim_id = slice_vim_id_dict[placement_list[ins["name"]]["vim"]]
                ns_id_dict[ins["name"]] = nfvo.instantiate_ns(
                    ins["name"],
                    ins["id"],
                    slice_vim_id
                )
            # Get the nsr for each service and wait for the activation
            nsr_dict = {}
            for num, ins in enumerate(new_ns_list):
                nsr_dict[ins["name"]] = nfvo.get_nsr(ns_id_dict[ins["name"]])
                while nsr_dict[ins["name"]]['operational-status'] != 'running':
                    time.sleep(10)
                    nsr_dict[ins["name"]] = nfvo.get_nsr(ns_id_dict[ins["name"]])
                self.slice_json['deployment_time']['NS_Deployment_Time'][ins['name']] =\
                    format(time.time() - ns_start_time, '.4f')
            mongoUtils.update("slice", self.slice_json['_id'], self.slice_json)

            # *** STEP-3b: Radio ***
            # Get the IPs for any radio delployed service
            ip_list = []
            for ns_name, nsr in nsr_dict.items():
                if ns_name == 'vepc':
                    vnfr_id_list = nfvo.get_vnfrId(nsr)
                    ip_list = []
                    for ivnfr_id in vnfr_id_list:
                        vnfr = nfvo.get_vnfr(ivnfr_id)
                        ip_list.append(nfvo.get_IPs(vnfr))

            if (mongoUtils.count('ems') <= 0):
                logging.warning('There is no registered EMS\n')
            else:
                # Select NFVO - Assume that there is only one registered
                ems_list = list(mongoUtils.index('ems'))
                ems = pickle.loads(ems_list[0]['ems'])
                radio_start_time = time.time()
                emsd = {
                    "sst": self.slice_json["nsi"]["type"],
                    "location": self.slice_json["nsi"]["radio-ref"]["location"],
                    "ipsdn": ip_list[0][1],
                    "ipservices": ip_list[0][0]
                }
                print("DEBUG: EMS = ", ems.ip, flush=True)
                ems.conf_radio(emsd)
                self.slice_json['deployment_time']['Radio_Configuration_Time']\
                    = format(time.time() - radio_start_time, '.4f')

            logging.info("Status: Running")
            self.slice_json['status'] = 'Running'
            self.slice_json['deployment_time']['Slice_Deployment_Time'] =\
                format(time.time() - self.slice_json['created_at'], '.4f')
            mongoUtils.update("slice", self.slice_json['_id'], self.slice_json)

        thread = Thread(target=do_work, kwargs={'request_json': self.slice_json})
        thread.start()

        return new_uuid

    def delete(self, uuid):
        """
        Delete a specific slice.
        used by: `katana slice rm [uuid]`
        """

        # check if slice uuid exists
        slice_json = json.loads(
            dumps(
                mongoUtils.get("slice", uuid)
            )
        )
        if not slice_json:
            return "Error: No such slice: {}".format(uuid)
        else:
            print(slice_json)
            return "ok"

            # TODO:
            # - OSM: stop NS, remove VIM
            # - openstack: remove Project/User

            # result = mongoUtils.delete("slice", uuid)
            # if result == 1:
            #     return uuid
            # elif result == 0:
            #     return "Error: Slice with uuid: {} could not be deleted".format(uuid)

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
