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


NEST_KEYS_OBJ = ("sst", "sd", "shared", "network_DL_throughput",
                 "ue_DL_throughput", "network_UL_throughput",
                 "ue_UL_throughput", "group_communication_support", "mtu",
                 "number_of_terminals", "positional_support",
                 "device_velocity", "terminal_density")

NEST_KEYS_LIST = ("coverage", "ns_list", "radio_spectrum", "probe_list")


def do_work(nest_req):
    """
    Creates the network slice
    """

    # Recreate the NEST with None options where missiong
    nest = {"_id": nest_req["_id"], "created_at": nest_req["created_at"],
            "deployment_time": {}}
    for nest_key in NEST_KEYS_OBJ:
        nest[nest_key] = nest_req.get(nest_key, None)
    for nest_key in NEST_KEYS_LIST:
        nest[nest_key] = nest_req.get(nest_key, [])

    # **** STEP-1: Placement ****
    nest['status'] = 'Placement'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Placement")
    placement_start_time = time.time()

    # Find the supported sst based on the sst and the sd value (if defined)
    find_data = {"sst": nest["sst"], "sd": nest["sd"]}
    sst = mongoUtils.find("sst", find_data)

    # Make the NS and PNF list
    # Initiate the lists
    ns_list = sst.get("ns_list", []) + nest.get("ns_list", [])
    pnf_list = sst.get("pnf_list", [])
    ems_messages = {}
    for_ems_list = []
    vim_list = []
    pdu_list = []

    # Get the NSs and PNFsfrom the supported sst
    for ns in ns_list:
        if not ns["placement"]:
            ns["placement"] = [{"location": "core"}]
        else:
            ns["placement"] = []
            for location in nest["coverage"]:
                ns["placement"].append({"location": location})
        ems = ns.get("ems-id", None)
        if ems:
            ems_messages[ems] = ems_messages.get(ems, {"func_list": []})
            ems_messages[ems]["func_list"].append(
                {"type": "ns", "name": ns["ns-name"], "ip": [],
                 "ns-placement": ns["placement"]})

    for pnf in pnf_list:
        pdu = mongoUtils.find("pdu", {"id": pnf["pdu-id"]})
        pdu_list.append(pdu["id"])
        ems = pnf.get("ems-id", None)
        if ems:
            ems_messages[ems] = ems_messages.get(ems, {"func_list": []})
            ems_messages[ems]["func_list"].append(
                {"type": "pnf", "name": pnf["pnf-name"], "ip": [pdu["ip"]],
                 "pdu-location": pdu["location"]})

    # Find the details for each NS
    pop_list = []
    for ns in ns_list:
        # Search the nsd collection in Mongo for the nsd
        nsd = mongoUtils.find("nsd", {"id": ns["nsd-id"],
                              "nfvo_id": ns["nfvo-id"]})
        if not nsd:
            # Bootstrap the NFVO to check for NSDs that are not in mongo
            # If again is not found, check if NS is optional.
            # If it is just remove it, else error
            nfvo_obj_json = mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})
            if not nfvo_obj_json:
                # ERROR HANDLING: There is no OSM for that ns - stop and return
                logger.error("There is no NFVO with id {}"
                             .format(ns["nfvo-id"]))
                return
            nfvo = pickle.loads(nfvo_obj_json["obj"])
            osmUtils.bootstrapNfvo(nfvo)
            nsd = mongoUtils.find("nsd", {"id": ns["nsd-id"],
                                  "nfvo_id": ns["nfvo-id"]})
            if not nsd and ns.get("optional", False):
                pop_list.append(ns)
            else:
                # ERROR HANDLING: The ns is not optional and the nsd is not
                # on the NFVO - stop and return
                logger.error(f"NSD {ns['nsd-id']} not found on\
OSM{ns['nfvo-id']}")
                return
        nsd = mongoUtils.find("nsd", {"id": ns["nsd-id"]})
        ns["nsd-info"] = nsd
    ns_list = [ns for ns in ns_list if ns not in pop_list]

    # Select the VIMs for each NS acording to location
    for ns in ns_list:
        ns["vims"] = []
        for site in ns["placement"]:
            get_vim = list(mongoUtils.find_all('vim', {"location": site["location"]}))
            if not get_vim:
                # ERROR HANDLING: There is no VIM at that location
                logger.error("VIM not found")
                return
            # TODO: Check the available resources and select vim
            # Temporary use the first element
            selected_vim = get_vim[0]["id"]
            ns["vims"].append(selected_vim)
            site["vim"] = selected_vim
            if selected_vim not in vim_list:
                vim_list.append(selected_vim)

    # Create the information for the EMS, WIM MON
    end_points = {"vims": vim_list, "pdus": pdu_list,
                  "probes": nest["probe_list"]}
    wim_data = {"network_DL_throughput": nest["network_DL_throughput"],
                "network_UL_throughput": nest["network_UL_throughput"],
                "mtu": nest["mtu"], "end_points": end_points}
    ems_data = {"ue_DL_throughput": nest["ue_DL_throughput"],
                "ue_UL_throughput": nest["ue_UL_throughput"],
                "group_communication_support":
                nest["group_communication_support"],
                "number_of_terminals": nest["number_of_terminals"],
                "positional_support": nest["positional_support"],
                "radio_spectrum": nest["radio_spectrum"],
                "device_velocity": nest["device_velocity"],
                "terminal_density": nest["terminal_density"]}
    for ems in ems_messages.values():
        ems.update(ems_data)

    nest["network functions"] = {"ns_list": ns_list, "pnf_list": pnf_list}
    nest['deployment_time']['Placement_Time'] = format(
        time.time() - placement_start_time, '.4f')

    # **** STEP-2: Provisioning ****
    nest['status'] = 'Provisioning'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Provisioning")
    prov_start_time = time.time()

    # *** STEP-2a: Cloud ***
    # *** STEP-2a-i: Create the new tenant/project on the VIM ***
    for num, vim in enumerate(vim_list):
        target_vim = mongoUtils.find("vim", {"id": vim})
        target_vim_obj = pickle.loads(
            mongoUtils.find("vim_obj", {"id": vim})["obj"])
        # Define project parameters
        tenant_project_name = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_description = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_user = 'vim_{0}_katana_{1}'.format(
            num, nest['_id'])
        tenant_project_password = 'password'
        ids = target_vim_obj.create_slice_prerequisites(
            tenant_project_name,
            tenant_project_description,
            tenant_project_user,
            tenant_project_password,
            nest['_id']
        )
        # Register the tenant to the mongo db
        target_vim["tenants"] = target_vim.get("tenants", [])
        target_vim["tenants"].append({nest["_id"]: tenant_project_name})

        # STEP-2a-ii: Αdd the new VIM tenant to NFVO
        if target_vim["type"] == "openstack":
            # Update the config parameter for the tenant
            config_param = dict(security_groups=ids["secGroupName"])
        elif target_vim["type"] == "opennebula":
            config_param = selected_vim['config']

        for ns in ns_list:
            if vim in ns["vims"]:
                target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
                target_nfvo_obj = pickle.loads(
                    mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
                vim_id = target_nfvo_obj.addVim(
                    tenant_project_name, target_vim['password'],
                    target_vim['type'], target_vim['auth_url'],
                    target_vim['username'],
                    config_param)
                # Register the tenant to the mongo db
                target_nfvo["tenants"] = target_nfvo.get("tenants", [])
                target_nfvo["tenants"].append({nest["_id"]: vim_id})
                for site in ns["placement"]:
                    if site["vim"] == vim:
                        site["nfvo_vim"] = vim_id

    # *** STEP-2b: WAN ***
    if (mongoUtils.count('wim') <= 0):
        logger.warning('There is no registered WIM')
    else:
        wan_start_time = time.time()
        # Select WIM - Assume that there is only one registered
        wim_list = list(mongoUtils.index('wim'))
        target_wim = wim_list[0]
        target_wim_id = target_wim["id"]
        target_wim_obj = pickle.loads(
            mongoUtils.find("wim_obj", {"id": target_wim_id})["obj"])
        target_wim_obj.create_slice(wim_data)
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
    for ns in ns_list:
        ns_start_time = time.time()
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(
            mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        for site in ns["placement"]:
            nfvo_inst_ns = target_nfvo_obj.instantiateNs(
                ns["ns-name"],
                ns["nsd-id"],
                site["nfvo_vim"]
            )
            site["nfvo_inst_ns"] = nfvo_inst_ns

    # Get the nsr for each service and wait for the activation
    for ns in ns_list:
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(
            mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        for site in ns["placement"]:
            insr = target_nfvo_obj.getNsr(site["nfvo_inst_ns"])
            while (insr["operational-status"] != "running" or
                   insr["config-status"] != "configured"):
                time.sleep(10)
                insr = target_nfvo_obj.getNsr(site["nfvo_inst_ns"])
            nest['deployment_time']['NS_Deployment_Time'][ns['ns-name']] =\
                format(time.time() - ns_start_time, '.4f')
            logger.debug("{} IS RUNNING".format(site))
    # **************** HERE *******************************************************
    return

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
