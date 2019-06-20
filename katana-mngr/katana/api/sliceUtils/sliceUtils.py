from katana.api.mongoUtils import mongoUtils
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


def do_work(request_json):
    """
    Creates the network slice
    """

    # TODO !!!
    # proper error handling and return

    # **** STEP-1: Placement ****
    request_json['status'] = 'Placement'
    mongoUtils.update("slice", request_json['_id'], request_json)
    logger.info("Status: Placement")
    placement_start_time = time.time()

    data = {"location": "core"}
    get_vim = mongoUtils.find('vim', data=data)
    default_vim = get_vim
    vim_list = []
    placement_list = {}
    new_ns_list = request_json['nsi']['nsd-ref']
    slice_type = request_json['nsi']['type']
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
                logger.warning("Network Service {0} isn't registered.\
                Will be placed at the default core NFVI".format(
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
                vim_list.append({"vim_id": selected_vim["_id"],
                                 "type": selected_vim["type"]})
    else:
        logger.warning('There are no registered slice services. All \
Network services will be placed on the default core NFVI and no network graph \
will be created')
        for new_ns in new_ns_list:
            placement_list[new_ns["name"]] =\
                {"vim": default_vim["_id"]}
        vim_list.append({"vim_id": default_vim["_id"],
                         "type": default_vim["type"]})

    request_json["vim_list"] = vim_list
    request_json["placement"] = placement_list
    # TODO:Create the network graph
    request_json['deployment_time']['Placement_Time'] = format(
        time.time() - placement_start_time, '.4f')

    # **** STEP-2: Provisioning ****
    request_json['status'] = 'Provisioning'
    mongoUtils.update("slice", request_json['_id'], request_json)
    logger.info("Status: Provisioning")
    prov_start_time = time.time()

    # *** STEP-2a: Cloud ***
    # Select NFVO - Assume that there is only one registered
    nfvo_list = list(mongoUtils.index('nfvo'))
    nfvo = pickle.loads(nfvo_list[0]['nfvo'])

    # Create a new tenant/project on every VIM used in the placement
    nfvo_vim_id_dict = {}
    for num, ivim in enumerate(vim_list):
        # STEP-2a-i: openstack prerequisites
        # Define project parameters
        tenant_project_name = 'vim_{0}_katana_{1}'.format(
            num, request_json['_id'])
        tenant_project_description = 'vim_{0}_katana_{1}'.format(
            num, request_json['_id'])
        tenant_project_user = 'vim_{0}_katana_{1}'.format(
            num, request_json['_id'])
        tenant_project_password = 'password'

        # Create the project on the NFVi
        selected_vim = mongoUtils.get("vim", ivim["vim_id"])
        ivim_obj = pickle.loads(selected_vim["vim"])
        ids = ivim_obj.create_slice_prerequisites(
            tenant_project_name,
            tenant_project_description,
            tenant_project_user,
            tenant_project_password,
            request_json['_id']
        )
        # Add the new tenant to the database
        ivim['tenant'] = ids

        if ivim["type"] == "openstack":
            # Update the config parameter for the tenant
            ivim['config'] = {'security_groups': ids["secGroupName"]}
        elif ivim["type"] == "opennebula":
            ivim['config'] = selected_vim['config']

        # STEP-2a-ii: add VIM to NFVO
        nfvo_vim_id_dict[ivim["vim_id"]] = nfvo.addVim(
            tenant_project_name, selected_vim["password"],
            selected_vim['type'], selected_vim['auth_url'],
            selected_vim["username"], ivim['config'])
    request_json["nfvo_vim_id"] = nfvo_vim_id_dict

    # *** STEP-2b: WAN ***
    if (mongoUtils.count('wim') <= 0):
        logger.warning('There is no registered WIM')
    else:
        wan_start_time = time.time()
        # Select WIM - Assume that there is only one registered
        wim_list = list(mongoUtils.index('wim'))
        wim = pickle.loads(wim_list[0]['wim'])

        # Create the WAN Slice Descriptor
        wsd = {}
        wsd['services-segment'] = []
        try:
            services = request_json["nsi"]["wim-ref"]["services-segment"]
        except Exception:
            logger.warning("There are no services on the slice descriptor")
        else:
            for service in services:
                wsd["services-segment"].append(service)
        wsd['topology'] = request_json['nsi']['wim-ref']['topology']
        wsd['bidirectional'] = request_json['nsi']['wim-ref']['bidirectional']
        wsd['link_params'] = request_json['nsi']['wim-ref']['link_params']
        # TODO Add the intermediate VIMs
        # Create the WAN Slice
        wim.create_slice(wsd)
        request_json['deployment_time']['WAN_Deployment_Time'] =\
            format(time.time() - wan_start_time, '.4f')
    request_json['deployment_time']['Provisioning_Time'] =\
        format(time.time() - prov_start_time, '.4f')

    # **** STEP-3: Activation ****
    request_json['status'] = 'Activation'
    mongoUtils.update("slice", request_json['_id'], request_json)
    logger.info("Status: Activation")
    # *** STEP-3a: Cloud ***
    # Instantiate NS
    request_json['deployment_time']['NS_Deployment_Time'] = {}
    ns_id_dict = {}
    for num, ins in enumerate(new_ns_list):
        ns_start_time = time.time()
        slice_vim_id = nfvo_vim_id_dict[placement_list[ins["name"]]["vim"]]
        ns_id_dict[ins["name"]] = nfvo.instantiate_ns(
            ins["name"],
            ins["id"],
            slice_vim_id
        )
    request_json["running_ns"] = ns_id_dict
    # Get the nsr for each service and wait for the activation
    nsr_dict = {}
    for num, ins in enumerate(new_ns_list):
        nsr_dict[ins["name"]] = nfvo.get_nsr(ns_id_dict[ins["name"]])
        while nsr_dict[ins["name"]]['operational-status'] != 'running':
            time.sleep(10)
            nsr_dict[ins["name"]] = nfvo.get_nsr(ns_id_dict[ins["name"]])
        request_json['deployment_time']['NS_Deployment_Time'][ins['name']] =\
            format(time.time() - ns_start_time, '.4f')
    mongoUtils.update("slice", request_json['_id'], request_json)

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
        logger.warning('There is no registered EMS')
    else:
        # Select NFVO - Assume that there is only one registered
        ems_list = list(mongoUtils.index('ems'))
        ems = pickle.loads(ems_list[0]['ems'])
        radio_start_time = time.time()
        emsd = {
            "sst": request_json["nsi"]["type"],
            "location": request_json["nsi"]["radio-ref"]["location"],
            "ipsdn": ip_list[0][1],
            "ipservices": ip_list[0][0]
        }
        ems.conf_radio(emsd)
        request_json['deployment_time']['Radio_Configuration_Time']\
            = format(time.time() - radio_start_time, '.4f')

    logger.info("Status: Running")
    request_json['status'] = 'Running'
    request_json['deployment_time']['Slice_Deployment_Time'] =\
        format(time.time() - request_json['created_at'], '.4f')
    mongoUtils.update("slice", request_json['_id'], request_json)


def delete_slice(slice_json):
    """
    Deletes the given network slice
    """

    # Select NFVO - Assume that there is only one registered
    nfvo_list = list(mongoUtils.index('nfvo'))
    nfvo = pickle.loads(nfvo_list[0]['nfvo'])

    # Stop all the Network Services
    for ins_name, ins_id in slice_json["running_ns"].items():
        nfvo.deleteNs(ins_id)

    time.sleep(15)

    for ivim in slice_json["vim_list"]:
        # Remove vims from the nfvo
        nfvo_vim_id = slice_json["nfvo_vim_id"][ivim['vim_id']]
        nfvo.deleteVim(nfvo_vim_id)
        # Delete VIM Project, user and Security group
        logger.debug("Delete vim tenant")
        selected_vim = mongoUtils.get("vim", ivim["vim_id"])
        ivim_obj = pickle.loads(selected_vim["vim"])
        ivim_obj.delete_proj_user(ivim["tenant"])
