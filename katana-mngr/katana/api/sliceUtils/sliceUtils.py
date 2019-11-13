from katana.api.mongoUtils import mongoUtils
from katana.api.osmUtils import osmUtils
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


NEST_KEYS = ("sst", "sd", "coverage", "nsd_list", "shared",
             "network_DL_throughput", "ue_DL_throughput",
             "network_UL_throughput", "ue_UL_throughput",
             "group_communication_support", "mtu", "number_of_terminals",
             "positional_support", "radio_spectrum", "device_velocity",
             "terminal_density", "probe_list")


def do_work(nest):
    """
    Creates the network slice
    """

    # **** STEP-1: Placement ****
    nest['status'] = 'Placement'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Placement")
    placement_start_time = time.time()

    # Recreate the NEST with None options where missiong
    new_nest = {}
    for nest_key in NEST_KEYS:
        new_nest[nest_key] = nest.get(nest_key, None)

    # Find the supported sst based on the sst and the sd value (if defined)
    find_data = {"sst": new_nest["sst"], "sd": new_nest["sd"]}
    sst = mongoUtils.find("sst", find_data)

    # Make the NS and PNF list
    ns_list = sst.get("ns_list", [])
    pnf_list = sst.get("pnf_list", [])
    for ns in ns_list:
        if ns["placement"] == 1:
            

    return
    # Select NFVO - Assume that there is only one registered
    nfvo_list = list(mongoUtils.index('nfvo'))
    nfvo = pickle.loads(nfvo_list[0]['nfvo'])

    data = {"location": "core"}
    get_vim = mongoUtils.find('vim', data=data)
    default_vim = get_vim
    vim_list = []
    placement_list = {}
    radio_nsd_list = []
    new_ns_list = nest['nsi']['nsd-ref']
    slice_name = nest['nsi']['name']
    data = {"name": slice_name}
    registered_service = mongoUtils.find('service', data=data)
    if registered_service is not None:
        registered_ns_list = registered_service['ns']
        for new_ns in new_ns_list:
            # Find the NS in the NFVO NSs
            data = {"id": new_ns["id"]}
            nsd = mongoUtils.find("nsd", data)
            if not nsd:
                osmUtils.bootstrapNfvo(nfvo)
                nsd = mongoUtils.find("nsd", data)
                if not nsd:
                    logger.error(f"NSd {new_ns['id']} was not found in the\
NFVO. Deleting slice")
                    delete_slice(nest)
                    return "Error: NSD was not found int the NFVO"
            try:
                logger.debug(new_ns["radio"])
                if new_ns["radio"]:
                    radio_nsd_list.append(new_ns["name"])
            except KeyError:
                logger.debug("No radio for this NS")
            placement_list[new_ns["name"]] = {"requirements": nsd["flavor"],
                                              "vim_net": nsd["vim_networks"]}
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
                placement_list[new_ns["name"]]["vim"] = selected_vim["_id"]
            else:
                vim_location =\
                    registered_ns_list[registered_ns_index]['location']
                data = {"location": vim_location}
                get_vim = mongoUtils.find('vim', data=data)
                selected_vim = get_vim
                placement_list[new_ns["name"]]["vim"] = selected_vim["_id"]
            if selected_vim["_id"] not in vim_list:
                vim_list.append(selected_vim["_id"])
    else:
        logger.warning('There are no registered slice services. All \
Network services will be placed on the default core NFVI and no network graph \
will be created')
        for new_ns in new_ns_list:
            # Find the NS in the NFVO NSs
            data = {"id": new_ns["id"]}
            nsd = mongoUtils.find("nsd", data)
            if not nsd:
                osmUtils.bootstrapNfvo(nfvo)
                nsd = mongoUtils.find("nsd", data)
                if not nsd:
                    logger.error(f"NSd {new_ns['id']} was not found in the\
                        NFVO. Deleting slice")
                    delete_slice(nest)
                    return "Error: NSD was not found int the NFVO"
            try:
                if new_ns["radio"]:
                    radio_nsd_list.append(new_ns["name"])
            except KeyError:
                pass
            placement_list[new_ns["name"]] = {"requirements": nsd["flavor"],
                                              "vim_net": nsd["vim_networks"]}
            placement_list[new_ns["name"]]["vim"] = default_vim["_id"]
        vim_list.append(default_vim["_id"])

    nest["vim_list"] = vim_list
    nest["placement"] = placement_list
    # TODO:Create the network graph
    nest['deployment_time']['Placement_Time'] = format(
        time.time() - placement_start_time, '.4f')

    # **** STEP-2: Provisioning ****
    nest['status'] = 'Provisioning'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Provisioning")
    prov_start_time = time.time()

    # *** STEP-2a: Cloud ***
    # Create a new tenant/project on every VIM used in the placement
    nfvo_vim_id_dict = {}
    for num, ivim in enumerate(vim_list):
        # STEP-2a-i: openstack prerequisites
        # Define project parameters
        tenant_project_name = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_description = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_user = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_password = 'password'

        # Create the project on the NFVi
        selected_vim = mongoUtils.get("vim", ivim)

        ivim_obj = pickle.loads(selected_vim["vim"])
        ids = ivim_obj.create_slice_prerequisites(
            tenant_project_name,
            tenant_project_description,
            tenant_project_user,
            tenant_project_password,
            nest['_id']
        )
        # Register the tenant to the mongo db
        selected_vim["tenants"][nest["_id"]] = ids
        mongoUtils.update("vim", ivim, selected_vim)

        if selected_vim["type"] == "openstack":
            # Update the config parameter for the tenant
            config_param = dict(security_groups=ids["secGroupName"])
        elif selected_vim["type"] == "opennebula":
            config_param = selected_vim['config']

        # STEP-2a-ii: add VIM to NFVO
        nfvo_vim_id_dict[ivim] = nfvo.addVim(
            tenant_project_name, selected_vim['password'],
            selected_vim['type'], selected_vim['auth_url'],
            selected_vim['username'],
            config_param)
    nest["nfvo_vim_id"] = nfvo_vim_id_dict

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
            services = nest["nsi"]["wim-ref"]["services-segment"]
        except Exception:
            logger.warning("There are no services on the slice descriptor")
        else:
            for service in services:
                wsd["services-segment"].append(service)
        wsd['topology'] = nest['nsi']['wim-ref']['topology']
        wsd['bidirectional'] = nest['nsi']['wim-ref']['bidirectional']
        wsd['link_params'] = nest['nsi']['wim-ref']['link_params']
        # TODO Add the intermediate VIMs
        # Create the WAN Slice
        wim.create_slice(wsd)
        nest['deployment_time']['WAN_Deployment_Time'] =\
            format(time.time() - wan_start_time, '.4f')
    nest['deployment_time']['Provisioning_Time'] =\
        format(time.time() - prov_start_time, '.4f')

    # **** STEP-3: Activation ****
    nest['status'] = 'Activation'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Activation")
    # *** STEP-3a: Cloud ***
    # Instantiate NS
    nest['deployment_time']['NS_Deployment_Time'] = {}
    ns_id_dict = {}
    for num, ins in enumerate(new_ns_list):
        ns_start_time = time.time()
        slice_vim_id = nfvo_vim_id_dict[placement_list[ins["name"]]["vim"]]
        ns_id_dict[ins["name"]] = nfvo.instantiateNs(
            ins["name"],
            ins["id"],
            slice_vim_id
        )
    nest["running_ns"] = ns_id_dict
    # Get the nsr for each service and wait for the activation
    nsr_dict = {}
    for num, ins in enumerate(new_ns_list):
        nsr_dict[ins["name"]] = nfvo.getNsr(ns_id_dict[ins["name"]])
        while nsr_dict[ins["name"]]['operational-status'] != 'running':
            time.sleep(10)
            nsr_dict[ins["name"]] = nfvo.getNsr(ns_id_dict[ins["name"]])
        nest['deployment_time']['NS_Deployment_Time'][ins['name']] =\
            format(time.time() - ns_start_time, '.4f')

    # Get the IPs for any radio delployed service
    for ns_name, nsr in nsr_dict.items():
        vnfr_id_list = nfvo.getVnfrId(nsr)
        nsr = {}
        for ivnfr_id in vnfr_id_list:
            vnfr = nfvo.getVnfr(ivnfr_id)
            vnf_name = vnfr["vnfd-ref"]
            nsr[vnf_name] = nfvo.getIPs(vnfr)
        placement_list[ns_name]["vnfr"] = nsr
    mongoUtils.update("slice", nest['_id'], nest)
    logger.debug(f"****** placement_list ******")
    for mynsd, nsd_value in placement_list.items():
        logger.debug(f"{mynsd} --> {nsd_value}")

    # *** STEP-3b: Radio ***
    radio_component_list = []
    for radio_ns in radio_nsd_list:
        radio_component_list.append(placement_list[radio_ns]["vnfr"])
    if (mongoUtils.count('ems') <= 0):
        logger.warning('There is no registered EMS')
    else:
        # Select NFVO - Assume that there is only one registered
        ems_list = list(mongoUtils.index('ems'))
        ems = pickle.loads(ems_list[0]['ems'])
        radio_start_time = time.time()
        emsd = {
            "sst": nest["nsi"]["type"],
            "location": nest["nsi"]["radio-ref"]["location"],
            "nsr_list": radio_component_list
        }
        logger.debug("**** EMS *****")
        logger.debug(emsd)
        ems.conf_radio(emsd)
        nest['deployment_time']['Radio_Configuration_Time']\
            = format(time.time() - radio_start_time, '.4f')

    logger.info("Status: Running")
    nest['status'] = 'Running'
    nest['deployment_time']['Slice_Deployment_Time'] =\
        format(time.time() - nest['created_at'], '.4f')
    mongoUtils.update("slice", nest['_id'], nest)


def delete_slice(slice_json):
    """
    Deletes the given network slice
    """

    # Update the slice status in mongo db
    slice_json["status"] = "Terminating"
    mongoUtils.update("slice", slice_json['_id'], slice_json)
    logger.info("Status: Terminating")

    # Select NFVO - Assume that there is only one registered
    nfvo_list = list(mongoUtils.index('nfvo'))
    nfvo = pickle.loads(nfvo_list[0]['nfvo'])

    # Stop all the Network Services
    try:
        for ins_name, ins_id in slice_json["running_ns"].items():
            nfvo.deleteNs(ins_id)

        time.sleep(15)

        for ivim in slice_json["vim_list"]:
            # Remove vims from the nfvo
            nfvo_vim_id = slice_json["nfvo_vim_id"][ivim]
            nfvo.deleteVim(nfvo_vim_id)
            # Delete VIM Project, user and Security group
            selected_vim = mongoUtils.get("vim", ivim)
            ivim_obj = pickle.loads(selected_vim["vim"])
            slice_id = slice_json["_id"]
            ivim_obj.delete_proj_user(selected_vim["tenants"]
                                      [slice_json["_id"]])
            # Remove the tenant from the registered vim
            selected_vim["tenants"].pop(slice_json["_id"])
            mongoUtils.update("vim", ivim, selected_vim)
    except KeyError:
        logger.info("No running services")

    result = mongoUtils.delete("slice", slice_json["_id"])
    if result == 1:
        return slice_json["_id"]
    elif result == 0:
        return 'Error: Slice with slice_json["_id"]: {} could not be deleted'.\
            format(slice_json["_id"])
