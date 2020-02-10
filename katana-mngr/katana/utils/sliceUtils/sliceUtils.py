from katana.shared_utils.mongoUtils import mongoUtils
import pickle
import time
import logging
import logging.handlers

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


NEST_KEYS_OBJ = ("sst", "shared", "network_DL_throughput",
                 "ue_DL_throughput", "network_UL_throughput",
                 "ue_UL_throughput", "group_communication_support", "mtu",
                 "number_of_terminals", "positional_support",
                 "device_velocity", "terminal_density")

NEST_KEYS_LIST = ("coverage", "ns_list", "radio_spectrum", "probe_list",
                  "connections", "functions")


def ns_details(ns_list, edge_loc, vim_dict, total_ns_list):
    """
    Get details for the NS that are part of the slice
    A) Find the nsd details for each NS
    B) Replace placement value with location
    C) Get the VIM for each NS
    """
    pop_list = []
    for ns in ns_list:
        # A) ****** Get the NSD ******
        # Search the nsd collection in Mongo for the nsd
        nsd = mongoUtils.find("nsd", {"nsd-id": ns["nsd-id"],
                              "nfvo_id": ns["nfvo-id"]})
        if not nsd:
            # Bootstrap the NFVO to check for NSDs that are not in mongo
            # If again is not found, check if NS is optional.
            # If it is just remove it, else error
            nfvo_obj_json = mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})
            if not nfvo_obj_json:
                # ERROR HANDLING: There is no OSM for that ns -
                # Stop and return
                logger.error(
                    "There is no NFVO with id {}".format(ns["nfvo-id"]))
                return [], [], [], 1
            nfvo = pickle.loads(nfvo_obj_json["obj"])
            bootstrapNfvo(nfvo)
            nsd = mongoUtils.find("nsd", {"nsd-id": ns["nsd-id"],
                                  "nfvo_id": ns["nfvo-id"]})
            if not nsd and ns.get("optional", False):
                pop_list.append(ns)
                continue
            else:
                # ERROR HANDLING: The ns is not optional and the nsd is not
                # on the NFVO - stop and return
                logger.error(
                    f"NSD {ns['nsd-id']} not found on OSM {ns['nfvo-id']}")
                return [], [], [], 1
        ns["nsd-info"] = nsd
        # B) ****** Replace placement value with location info ******
        ns["placement"] = (lambda x: {"location": "Core"} if not x
                           else {"location": edge_loc})(ns["placement"])

        # C) ****** Get the VIM info ******
        ns["vims"] = []
        loc = ns["placement"]["location"]
        get_vim = list(mongoUtils.find_all('vim', {"location": loc}))
        if not get_vim:
            # ERROR HANDLING: There is no VIM at that location
            logger.error(f"VIM not found in location {loc}")
            return [], [], [], 1
        # TODO: Check the available resources and select vim
        # Temporary use the first element
        selected_vim = get_vim[0]["id"]
        ns["vims"].append(selected_vim)
        try:
            vim_dict[selected_vim]["ns_list"].append(ns["ns-name"])
            if ns["nfvo-id"] not in vim_dict[selected_vim]["nfvo_list"]:
                vim_dict[selected_vim]["nfvo_list"].append(ns["nfvo-id"])
        except KeyError:
            vim_dict[selected_vim] = {"ns_list": [ns["ns-name"]],
                                      "nfvo_list": [ns["nfvo-id"]]}
        ns["placement"]["vim"] = selected_vim
        if ns not in total_ns_list:
            total_ns_list.append(ns)
    # Remove the ns that are optional and nsd was not found
    ns_list = [ns for ns in ns_list if ns not in pop_list]
    return total_ns_list, vim_dict, ns_list, 0


def add_slice(nest_req):
    """
    Creates the network slice
    """

    nest_req['status'] = 'init'
    nest_req['created_at'] = time.time()  # unix epoch
    nest_req['deployment_time'] = dict(
        Slice_Deployment_Time='N/A',
        Placement_Time='N/A',
        Provisioning_Time='N/A',
        NS_Deployment_Time='N/A',
        WAN_Deployment_Time='N/A',
        Radio_Configuration_Time='N/A')
    mongoUtils.add("slice", nest_req)

    # Recreate the NEST with None options where missiong
    nest = {"_id": nest_req["_id"], "created_at": nest_req["created_at"],
            "deployment_time": {"Placement_Time": None,
                                "Provisioning_Time": None,
                                "WAN_Deployment_Time": None,
                                "NS_Deployment_Time": None,
                                "Radio_Configuration_Time": None,
                                "Slice_Deployment_Time": None}}
    for nest_key in NEST_KEYS_OBJ:
        nest[nest_key] = nest_req.get(nest_key, None)
    for nest_key in NEST_KEYS_LIST:
        nest[nest_key] = nest_req.get(nest_key, [])

    # **** STEP-1: Placement ****
    nest['status'] = 'Placement'
    nest["configured_components"] = []
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Placement")
    placement_start_time = time.time()

    # Initiate the lists
    pdu_list = []
    vim_dict = {}
    total_ns_list = []
    ems_messages = {}

    # **** Step1-a: Get Details for the Network Services ****
    # i) The extra NS of the slice
    for location in nest["coverage"]:
        total_ns_list, vim_dict, temp_list, err = ns_details(
            nest["ns_list"], location, vim_dict, total_ns_list)
        if err:
            delete_slice(nest)
            return
    nest["ns_list"] = []
    for ns in total_ns_list:
        nest["ns_list"].append(ns)

    # ii) The NS part of the core slice
    for connection in nest["connections"]:
        for key in connection:
            try:
                total_ns_list, vim_dict, connection[key]["ns_list"],\
                    err = ns_details(
                        connection[key]["ns_list"],
                        connection[key]["location"],
                        vim_dict, total_ns_list)
                if err:
                    delete_slice(nest)
                    return
            except KeyError:
                continue
            else:
                del temp_list

    # **** Step1-b: Create the data for WIM ****
    wim_data = {"core_connections": [], "extra_NS": []}
    # Add the connections
    for connection in nest["connections"]:
        data = {}
        for key in connection:
            key_data = {}
            try:
                ns_l = connection[key]["ns_list"]
            except KeyError:
                pass
            else:
                key_data["ns"] = []
                for ns in ns_l:
                    if ns["placement"] not in key_data["ns"]:
                        key_data["ns"].append(ns["placement"])
            try:
                pnf_l = connection[key]["pnf_list"]
            except KeyError:
                pass
            else:
                key_data["pnf"] = pnf_l
            pnf = connection[key].get("pnf_list", [])
            if key_data:
                data[key] = key_data
        if data:
            wim_data["core_connections"].append(data)

    # Add the extra Network Services
    for ns in nest["ns_list"]:
        if ns["placement"] not in wim_data["extra_NS"]:
            wim_data["extra_NS"].append(ns["placement"])

    nest["configured_components"].append("nf")
    nest["vim_list"] = vim_dict
    nest['deployment_time']['Placement_Time'] = format(
        time.time() - placement_start_time, '.4f')

    # **** STEP-2: Resource Provisioning ****
    nest['status'] = 'Provisioning'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Provisioning")
    prov_start_time = time.time()

    # *** STEP-2a: Cloud ***
    # *** STEP-2a-i: Create the new tenant/project on the VIM ***
    for num, (vim, vim_info) in enumerate(vim_dict.items()):
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
        target_vim["tenants"][nest["_id"]] = tenant_project_name
        mongoUtils.update("vim", target_vim["_id"], target_vim)

        # STEP-2a-ii: Αdd the new VIM tenant to NFVO
        if target_vim["type"] == "openstack":
            # Update the config parameter for the tenant
            config_param = dict(security_groups=ids["secGroupName"])
        elif target_vim["type"] == "opennebula":
            config_param = selected_vim['config']

        for nfvo_id in vim_info["nfvo_list"]:
            target_nfvo = mongoUtils.find("nfvo", {"id": nfvo_id})
            target_nfvo_obj = pickle.loads(
                mongoUtils.find("nfvo_obj", {"id": nfvo_id})["obj"])
            vim_id = target_nfvo_obj.addVim(
                tenant_project_name, target_vim['password'],
                target_vim['type'], target_vim['auth_url'],
                target_vim['username'],
                config_param)
            vim_info["nfvo_vim_account"] = vim_info.get("nfvo_vim_account", {})
            vim_info["nfvo_vim_account"][nfvo_id] = vim_id
            # Register the tenant to the mongo db
            target_nfvo["tenants"][nest["_id"]] =\
                target_nfvo["tenants"].get(nest["_id"], [])
            target_nfvo["tenants"][nest["_id"]].append(vim_id)
            mongoUtils.update("nfvo", target_nfvo["_id"], target_nfvo)

    mongoUtils.update("slice", nest['_id'], nest)
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
        nest["wim_data"] = wim_data
        target_wim["slices"][nest["_id"]] = nest["_id"]
        mongoUtils.update("wim", target_wim["_id"], target_wim)
        nest['deployment_time']['WAN_Deployment_Time'] =\
            format(time.time() - wan_start_time, '.4f')
        nest["configured_components"].append("wim")
    nest['deployment_time']['Provisioning_Time'] =\
        format(time.time() - prov_start_time, '.4f')

    # **** STEP-3: Slice Activation Phase****
    nest['status'] = 'Activation'
    mongoUtils.update("slice", nest['_id'], nest)
    logger.info("Status: Activation")
    # *** STEP-3a: Cloud ***
    # Instantiate NS
    # Store info about instantiated NSs
    ns_inst_info = {}
    nest['deployment_time']['NS_Deployment_Time'] = {}
    for ns in total_ns_list:
        ns_start_time = time.time()
        ns_inst_info[ns["nsd-id"]] = {}
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(
            mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        selected_vim = ns["placement"]["vim"]
        nfvo_vim_account = \
            vim_dict[selected_vim]["nfvo_vim_account"][ns["nfvo-id"]]
        nfvo_inst_ns = target_nfvo_obj.instantiateNs(
            ns["ns-name"],
            ns["nsd-id"],
            nfvo_vim_account
        )
        ns_inst_info[ns["nsd-id"]][ns["placement"]["location"]] = {
            "nfvo_inst_ns": nfvo_inst_ns}
        time.sleep(4)
        time.sleep(2)

    # Get the nsr for each service and wait for the activation
    for ns in total_ns_list:
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(
            mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        site = ns["placement"]
        nfvo_inst_ns_id = \
            ns_inst_info[ns["nsd-id"]][site["location"]]["nfvo_inst_ns"]
        insr = target_nfvo_obj.getNsr(nfvo_inst_ns_id)
        while (insr["operational-status"] != "running" or
               insr["config-status"] != "configured"):
            time.sleep(10)
            insr = target_nfvo_obj.getNsr(nfvo_inst_ns_id)
        nest['deployment_time']['NS_Deployment_Time'][ns['ns-name']] =\
            format(time.time() - ns_start_time, '.4f')
        # Get the IPs of the instantiated NS
        vnf_list = []
        vnfr_id_list = target_nfvo_obj.getVnfrId(insr)
        for ivnfr_id in vnfr_id_list:
            vnfr = target_nfvo_obj.getVnfr(ivnfr_id)
            vnf_list.append(target_nfvo_obj.getIPs(vnfr))
        ns_inst_info[ns["nsd-id"]][site["location"]]["vnfr"] = vnf_list

    nest["ns_inst_info"] = ns_inst_info
    nest["total_ns_list"] = total_ns_list
    mongoUtils.update("slice", nest['_id'], nest)

    # *** STEP-3b: Radio Slice Configuration ***
    if (mongoUtils.count('ems') <= 0):
        logger.warning('There is no registered EMS')
    else:
        # Add the management IPs for the NS sent ems in ems_messages:
        ems_radio_data = {"ue_DL_throughput": nest["ue_DL_throughput"],
                          "ue_UL_throughput": nest["ue_UL_throughput"],
                          "group_communication_support":
                          nest["group_communication_support"],
                          "number_of_terminals": nest["number_of_terminals"],
                          "positional_support": nest["positional_support"],
                          "radio_spectrum": nest["radio_spectrum"],
                          "device_velocity": nest["device_velocity"],
                          "terminal_density": nest["terminal_density"]}
        radio_start_time = time.time()
        for connection in nest["connections"]:
            data = {}
            ems_id_list = []
            for key in connection:
                key_data = {}
                try:
                    ems_id = connection[key]["ems-id"]
                except KeyError:
                    continue
                else:
                    if ems_id not in ems_id_list:
                        ems_id_list.append(ems_id)
                    try:
                        ns_l = connection[key]["ns_list"]
                    except KeyError:
                        pass
                    else:
                        key_data["ns"] = []
                        for ns in ns_l:
                            ns_info = ns_inst_info[ns["nsd-id"]]\
                                [connection[key]["location"]]
                            ns_data = \
                                {"name": ns["ns-name"],
                                 "location": ns["placement"]["location"],
                                 "vnf_list": ns_info["vnfr"]}
                            key_data["ns"].append(ns_info)
                try:
                    key_data["pnf"] = connection[key]["pnf_list"]
                except KeyError:
                    pass
                if key_data:
                    data[key] = key_data
            if data:
                data["slice_sla"] = ems_radio_data
                for ems_id in ems_id_list:
                    messages = ems_messages.get(ems_id, [])
                    messages.append(data)
                    ems_messages[ems_id] = messages

        for ems_id, ems_message in ems_messages.items():
            # Find the EMS
            target_ems = mongoUtils.find("ems", {"id": ems_id})
            if not target_ems:
                # ERROR HANDLING: There is no such EMS
                logger.error("EMS {} not found - No configuration".
                             format(ems_id))
                continue
            target_ems_obj = pickle.loads(
                mongoUtils.find("ems_obj", {"id": ems_id})["obj"])
            # Send the message
            for imessage in ems_message:
                target_ems_obj.conf_radio(imessage)
        nest["ems_data"] = ems_messages
        nest['deployment_time']['Radio_Configuration_Time']\
            = format(time.time() - radio_start_time, '.4f')
        nest["configured_components"].append("ems")

    # *** STEP-4: Finalize ***
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

    # *** Step-1: Radio Slice Configuration ***
    if "ems" in slice_json["configured_components"]:
        ems_messages = slice_json.get("ems_data", None)
        if ems_messages:
            for ems_id, ems_message in ems_messages.items():
                # Find the EMS
                target_ems = mongoUtils.find("ems", {"id": ems_id})
                if not target_ems:
                    # ERROR HANDLING: There is no such EMS
                    logger.error("EMS {} not found - No configuration".
                                 format(ems_id))
                    continue
                target_ems_obj = pickle.loads(
                    mongoUtils.find("ems_obj", {"id": ems_id})["obj"])
                target_ems_obj.del_slice(ems_message)
    else:
        logger.info("There was not EMS configuration")

    # Release PDUs
    if "pdu" in slice_json["configured_components"]:
        for ipdu in slice_json["pdu_list"]:
            pdu = mongoUtils.find("pdu", {"id": ipdu})
            pdu["tenants"].remove(slice_json["_id"])
            mongoUtils.update("pdu", pdu["_id"], pdu)
    else:
        logger.info("No PDUs on the slice")

    # *** Step-2: WAN Slice ***
    wim_data = slice_json.get("wim_data", None)
    if wim_data:
        # Select WIM - Assume that there is only one registered
        wim_list = list(mongoUtils.index('wim'))
        if wim_list:
            target_wim = wim_list[0]
            target_wim_id = target_wim["id"]
            target_wim_obj = pickle.loads(
                mongoUtils.find("wim_obj", {"id": target_wim_id})["obj"])
            target_wim_obj.del_slice(wim_data)
            del target_wim["slices"][slice_json["_id"]]
            mongoUtils.update("wim", target_wim["_id"], target_wim)
        else:
            logger.warning("Cannot find WIM - WAN Slice will not be deleted")
    else:
        logger.info("There was no WIM configuration")

    # *** Step-3: Cloud ***
    if "nf" in slice_json["configured_components"]:
        total_ns_list = slice_json["total_ns_list"]
        ns_inst_info = slice_json["ns_inst_info"]
        try:
            vim_error_list = []
            for ns in total_ns_list:
                # Get the NFVO
                nfvo_id = ns["nfvo-id"]
                target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
                if not target_nfvo:
                    logger.warning(
                        "NFVO with id {} was not found - NSs won't terminate"
                        .format(nfvo_id))
                    vim_error_list += ns["vims"]
                    continue
                target_nfvo_obj = pickle.loads(
                    mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
                # Stop the NS
                nfvo_inst_ns = ns_inst_info[ns["nsd-id"]]\
                    [ns["placement"]["location"]]["nfvo_inst_ns"]
                target_nfvo_obj.deleteNs(nfvo_inst_ns)
                while True:
                    if target_nfvo_obj.checkNsLife(nfvo_inst_ns):
                        break
                    time.sleep(5)
        except KeyError as e:
            logger.warning(
                f"Error, not all NSs started or terminated correctly {e}")

        try:
            vim_dict = slice_json["vim_list"]
            for vim, vim_info in vim_dict.items():
                # Delete the new tenants from the NFVO
                for nfvo, vim_account in vim_info["nfvo_vim_account"].items():
                    # Get the NFVO
                    target_nfvo = mongoUtils.find("nfvo", {"id": nfvo})
                    target_nfvo_obj = pickle.loads(
                        mongoUtils.find("nfvo_obj", {"id": nfvo})["obj"])
                    # Delete the VIM and update nfvo db
                    target_nfvo_obj.deleteVim(vim_account)
                    target_nfvo["tenants"][slice_json["_id"]].\
                        remove(vim_account)
                    if len(target_nfvo["tenants"][slice_json["_id"]]) == 0:
                        del target_nfvo["tenants"][slice_json["_id"]]
                    mongoUtils.update("nfvo", target_nfvo["_id"], target_nfvo)
                # Delete the tenants from every vim
                if vim not in vim_error_list:
                    # Get the VIM
                    target_vim = mongoUtils.find("vim", {"id": vim})
                    if not target_vim:
                        logger.warning(
                            "VIM id {} was not found - Tenant won't be deleted"
                            .format(vim))
                        continue
                    target_vim_obj = pickle.loads(
                        mongoUtils.find("vim_obj", {"id": vim})["obj"])
                    target_vim_obj.delete_proj_user(
                        target_vim["tenants"][slice_json["_id"]])
                    del target_vim["tenants"][slice_json["_id"]]
                    mongoUtils.update("vim", target_vim["_id"], target_vim)
        except KeyError as e:
            logger.warning(
                f"Error, not all tenants created or removed correctly {e}")
    else:
        logger.info("No NFs on the slice")

    mongoUtils.delete("slice", slice_json["_id"])

    # Remove Slice from the tenants list on functions
    for func_id in slice_json["functions"]:
        ifunc = mongoUtils.get("func", func_id)
        ifunc["tenants"].remove(slice_json["_id"])
        mongoUtils.update("func", func_id, ifunc)


def bootstrapNfvo(nfvo_obj):
    """
    Reads info from NSDs/VNFDs in the NFVO and stores them in mongodb
    """
    nfvo_obj.readVnfd()
    nfvo_obj.readNsd()
