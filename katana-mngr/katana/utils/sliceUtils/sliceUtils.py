import copy
import json
import logging
import logging.handlers
import pickle
import time
import uuid
import os
import requests

from katana.shared_utils.mongoUtils import mongoUtils
from katana.shared_utils.kafkaUtils.kafkaUtils import create_producer

# Logging Parameters
logger = logging.getLogger(__name__)
file_handler = logging.handlers.RotatingFileHandler("katana.log", maxBytes=10000, backupCount=5)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


NEST_KEYS_OBJ = (
    "sst",
    "shared",
    "network_DL_throughput",
    "ue_DL_throughput",
    "network_UL_throughput",
    "ue_UL_throughput",
    "group_communication_support",
    "mtu",
    "number_of_terminals",
    "positional_support",
    "device_velocity",
    "terminal_density",
)

NEST_KEYS_LIST = (
    "coverage",
    "ns_list",
    "radio_spectrum",
    "probe_list",
    "connections",
    "functions",
    "qos",
)


def ns_details(
    ns_list, edge_loc, vim_dict, total_ns_list, shared_function=0, shared_slice_list_key=None,
):
    """
    Get details for the NS that are part of the slice
    A) Find the nsd details for each NS
    B) Replace placement value with location
    C) Get the VIM for each NS
    """
    pop_list = []
    for ns in ns_list:
        try:
            if ns["placement_loc"] and not ns["placement"]:
                # Placement to Core already done - go to next NS
                continue
            else:
                # Placement to Edge - Is already done - Need to make another ns
                new_ns = copy.deepcopy(ns)
        except KeyError:
            # No placement at all
            new_ns = ns
        # 00) Check if the function is shared and if the ns is already instantiated
        new_ns["shared_function"] = shared_function
        new_ns["shared_slice_key"] = shared_slice_list_key
        # Search the nsd collection in Mongo for the nsd
        nsd = mongoUtils.find("nsd", {"nsd-id": new_ns["nsd-id"]})
        if not nsd:
            # Bootstrap the NFVOs to check for NSDs that are not in mongo
            # If again is not found, check if NS is optional.
            # If it is just remove it, else error
            nfvo_obj_list = list(mongoUtils.find_all("nfvo_obj"))
            for infvo in nfvo_obj_list:
                nfvo = pickle.loads(infvo["obj"])
                nfvo.bootstrapNfvo()
            nsd = mongoUtils.find("nsd", {"nsd-id": new_ns["nsd-id"]})
            if not nsd and ns.get("optional", False):
                # The NS is optional - continue to next
                pop_list.append(ns)
                continue
            else:
                # Error handling: The ns is not optional and the nsd is not
                # on the NFVO - stop and return
                error_message = f"NSD {new_ns['nsd-id']} not found on any NFVO registered to SM"
                logger.error(error_message)
                return error_message, []
        new_ns["nfvo-id"] = nsd["nfvo_id"]
        new_ns["nsd-info"] = nsd
        # B) ****** Replace placement value with location info ******
        if type(new_ns["placement"]) is str:
            new_ns["placement_loc"] = {"location": new_ns["placement"]}
        else:
            new_ns["placement_loc"] = (
                lambda x: {"location": "Core"} if not x else {"location": edge_loc}
            )(new_ns["placement"])

        # C) ****** Get the VIM info ******
        if shared_function != 2:
            new_ns["vims"] = []
            loc = new_ns["placement_loc"]["location"]
            get_vim = list(mongoUtils.find_all("vim", {"location": loc}))
            if not get_vim:
                if not new_ns.get("optional", False):
                    # Error handling: There is no VIM at that location
                    error_message = f"VIM not found in location {loc}"
                    logger.error(error_message)
                    return error_message, []
                else:
                    # The NS is optional - continue to next
                    pop_list.append(ns)
                    continue
            # TODO: Check the available resources and select vim
            # Temporary use the first element
            selected_vim = get_vim[0]["id"]
            new_ns["vims"].append(selected_vim)
            try:
                vim_dict[selected_vim]["ns_list"].append(new_ns["ns-name"])
                if new_ns["nfvo-id"] not in vim_dict[selected_vim]["nfvo_list"]:
                    vim_dict[selected_vim]["nfvo_list"].append(new_ns["nfvo-id"])
            except KeyError:
                vim_dict[selected_vim] = {
                    "ns_list": [new_ns["ns-name"]],
                    "nfvo_list": [new_ns["nfvo-id"]],
                    "shared": shared_slice_list_key,
                }
            resources = vim_dict[selected_vim].get(
                "resources", {"memory-mb": 0, "vcpu-count": 0, "storage-gb": 0, "instances": 0}
            )
            for key in resources:
                resources[key] += nsd["flavor"][key]
            vim_dict[selected_vim]["resources"] = resources
            new_ns["placement_loc"]["vim"] = selected_vim
        # 0) Create an uuid for the ns
        new_ns["ns-id"] = str(uuid.uuid4())
        total_ns_list.append(new_ns)
        del new_ns
    # Remove the ns that are optional and nsd was not found
    ns_list = [ns for ns in ns_list if ns not in pop_list]
    return 0, pop_list


def add_slice(nest_req):
    """
    Creates the network slice
    """

    # Recreate the NEST with None options where missiong
    nest = {
        "_id": nest_req["_id"],
        "status": "Init",
        "created_at": time.time(),  # unix epoch
        "deployment_time": {
            "Placement_Time": None,
            "Provisioning_Time": None,
            "WAN_Deployment_Time": None,
            "NS_Deployment_Time": None,
            "Radio_Configuration_Time": None,
            "Slice_Deployment_Time": None,
        },
    }
    mongoUtils.add("slice", nest)
    for nest_key in NEST_KEYS_OBJ:
        nest[nest_key] = nest_req.get(nest_key, None)
    for nest_key in NEST_KEYS_LIST:
        nest[nest_key] = nest_req.get(nest_key, [])

    # Check if slice monitoring has been enabled
    monitoring = os.getenv("KATANA_MONITORING", None)
    wim_monitoring = {}
    mon_producer = None
    if monitoring:
        # Create the Kafka producer
        mon_producer = create_producer()
        nest["slice_monitoring"] = {}

    # **** STEP-1: Placement ****
    nest["status"] = "Placement"
    if monitoring:
        mon_producer.send(
            "nfv_mon",
            value={
                "action": "katana_mon",
                "slice_info": {"slice_id": nest["_id"], "status": "placement"},
            },
        )

    nest["conf_comp"] = {"nf": [], "ems": []}
    mongoUtils.update("slice", nest["_id"], nest)
    logger.info(f"{nest['_id']} Status: Placement")
    placement_start_time = time.time()

    # Initiate the lists
    vim_dict = {}
    total_ns_list = []
    ems_messages = {}

    # Get Details for the Network Services
    # i) The extra NS of the slice
    for location in nest["coverage"]:
        err, _ = ns_details(nest["ns_list"], location, vim_dict, total_ns_list)
        if err:
            nest["status"] = f"Failed - {err}"
            nest["ns_inst_info"] = {}
            nest["total_ns_list"] = []
            mongoUtils.update("slice", nest["_id"], nest)
            return
    del nest["ns_list"]
    nest["ns_list"] = copy.deepcopy(total_ns_list)
    # ii) The NS part of the core slice
    inst_functions = {}
    for connection in nest["connections"]:
        for key in connection:
            # Check if the function has been instantiated from another connection
            if connection[key]["_id"] in inst_functions:
                connection[key] = inst_functions[connection[key]["_id"]]
                continue
            # Check if the function is shared with another slice
            # shared_check values: 0: No shared, 1: First shared, 2: Shared
            shared_check = 0
            shared_slice_list_key = None
            try:
                shared_slice_list_key = nest["shared"][key][connection[key]["_id"]]
                shared_slice_list = connection[key]["shared"]["sharing_list"][shared_slice_list_key]
                if len(shared_slice_list) > 1:
                    shared_check = 2
                else:
                    shared_check = 1
            except KeyError:
                pass
            try:
                err, pop_list = ns_details(
                    connection[key]["ns_list"],
                    connection[key]["location"],
                    vim_dict,
                    total_ns_list,
                    shared_check,
                    shared_slice_list_key,
                )
                if pop_list:
                    connection[key]["ns_list"] = [
                        x for x in connection[key]["ns_list"] if x not in pop_list
                    ]
                if err:
                    nest["status"] = f"Failed - {err}"
                    nest["ns_inst_info"] = {}
                    nest["total_ns_list"] = []
                    mongoUtils.update("slice", nest["_id"], nest)
                    return
                inst_functions[connection[key]["_id"]] = connection[key]
            except KeyError:
                continue

    nest["vim_list"] = vim_dict
    nest["total_ns_list"] = total_ns_list
    nest["deployment_time"]["Placement_Time"] = format(time.time() - placement_start_time, ".4f")

    # **** STEP-2: Resource Provisioning ****
    nest["status"] = "Provisioning"
    if monitoring:
        mon_producer.send(
            "nfv_mon",
            value={
                "action": "katana_mon",
                "slice_info": {"slice_id": nest["_id"], "status": "provisioning"},
            },
        )
    mongoUtils.update("slice", nest["_id"], nest)
    logger.info(f"{nest['_id']} Status: Provisioning")
    prov_start_time = time.time()

    # *** STEP-2a: Cloud ***
    # *** STEP-2a-i: Create the new tenant/project on the VIM ***
    for num, (vim, vim_info) in enumerate(vim_dict.items()):
        target_vim = mongoUtils.find("vim", {"id": vim})
        target_vim_obj = pickle.loads(mongoUtils.find("vim_obj", {"id": vim})["obj"])
        # Define project parameters
        if vim_info["shared"]:
            name = "vim_{0}_katana_{1}_shared".format(num, vim_info["shared"])
        else:
            name = "vim_{0}_katana_{1}".format(num, nest["_id"])
        tenant_project_name = name
        tenant_project_description = name
        tenant_project_user = name
        tenant_project_password = "password"
        # If the vim is Openstack type, set quotas
        quotas = (
            vim_info["resources"]
            if target_vim["type"] == "openstack" or target_vim["type"] == "Openstack"
            else None
        )
        ids = target_vim_obj.create_slice_prerequisites(
            tenant_project_name,
            tenant_project_description,
            tenant_project_user,
            tenant_project_password,
            nest["_id"],
            quotas=quotas,
        )
        # Register the tenant to the mongo db
        target_vim["tenants"][nest["_id"]] = tenant_project_name
        mongoUtils.update("vim", target_vim["_id"], target_vim)

        # STEP-2a-ii: Αdd the new VIM tenant to NFVO
        if target_vim["type"] == "openstack":
            # Update the config parameter for the tenant
            config_param = dict(security_groups=ids["secGroupName"])
        elif target_vim["type"] == "opennebula":
            config_param = target_vim["config"]
        else:
            config_param = {}

        for nfvo_id in vim_info["nfvo_list"]:
            target_nfvo = mongoUtils.find("nfvo", {"id": nfvo_id})
            target_nfvo_obj = pickle.loads(mongoUtils.find("nfvo_obj", {"id": nfvo_id})["obj"])
            vim_id = target_nfvo_obj.addVim(
                tenant_project_name,
                target_vim["password"],
                target_vim["type"],
                target_vim["auth_url"],
                target_vim["username"],
                config_param,
            )
            vim_info["nfvo_vim_account"] = vim_info.get("nfvo_vim_account", {})
            vim_info["nfvo_vim_account"][nfvo_id] = vim_id
            # Register the tenant to the mongo db
            target_nfvo["tenants"][nest["_id"]] = target_nfvo["tenants"].get(nest["_id"], [])
            target_nfvo["tenants"][nest["_id"]].append(vim_id)
            mongoUtils.update("nfvo", target_nfvo["_id"], target_nfvo)

    mongoUtils.update("slice", nest["_id"], nest)
    # *** STEP-2b: WAN ***
    if mongoUtils.count("wim") <= 0:
        logger.warning("There is no registered WIM")
    else:
        wan_start_time = time.time()
        # Crate the data for the WIM
        wim_data = {"_id": nest["_id"], "core_connections": [], "extra_ns": [], "slice_sla": {}}
        # i) Create the slice_sla data for the WIM
        wim_data["slice_sla"] = {
            "network_DL_throughput": nest["network_DL_throughput"],
            "network_UL_throughput": nest["network_UL_throughput"],
            "mtu": nest["mtu"],
        }
        # ii) Add the connections
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
                        if ns["placement_loc"] not in key_data["ns"]:
                            key_data["ns"].append(ns["placement_loc"])
                try:
                    pnf_l = connection[key]["pnf_list"]
                except KeyError:
                    pass
                else:
                    key_data["pnf"] = pnf_l
                if key_data:
                    data[key] = key_data
            if data:
                wim_data["core_connections"].append(data)
        # iii) Add the extra Network Services
        for ns in nest["ns_list"]:
            if ns["placement_loc"] not in wim_data["extra_ns"]:
                wim_data["extra_ns"].append(ns["placement_loc"])
        # iV) Add the probes
        wim_data["probes"] = nest["probe_list"]
        # Select WIM - Assume that there is only one registered
        wim_list = list(mongoUtils.index("wim"))
        target_wim = wim_list[0]
        target_wim_id = target_wim["id"]
        target_wim_obj = pickle.loads(mongoUtils.find("wim_obj", {"id": target_wim_id})["obj"])
        target_wim_obj.create_slice(wim_data)
        nest["wim_data"] = wim_data
        target_wim["slices"][nest["_id"]] = nest["_id"]
        mongoUtils.update("slice", nest["_id"], nest)
        mongoUtils.update("wim", target_wim["_id"], target_wim)
        # Add monitoring from WIM in nest
        try:
            wim_monitoring = target_wim["monitoring-url"]
            nest["slice_monitoring"]["WIM"] = wim_monitoring
        except KeyError:
            pass
        nest["deployment_time"]["WAN_Deployment_Time"] = format(time.time() - wan_start_time, ".4f")
    nest["deployment_time"]["Provisioning_Time"] = format(time.time() - prov_start_time, ".4f")

    # **** STEP-3: Slice Activation Phase****
    nest["status"] = "Activation"
    if monitoring:
        mon_producer.send(
            "nfv_mon",
            value={
                "action": "katana_mon",
                "slice_info": {"slice_id": nest["_id"], "status": "activation"},
            },
        )
    mongoUtils.update("slice", nest["_id"], nest)
    logger.info(f"{nest['_id']} Status: Activation")
    # *** STEP-3a: Cloud ***
    # Instantiate NS
    # Store info about instantiated NSs
    ns_inst_info = {}
    nest["deployment_time"]["NS_Deployment_Time"] = {}
    for ns in total_ns_list:
        ns["start_time"] = time.time()
        if ns["shared_function"] == 2:
            # The ns is already instantiated and there is no need to instantiate again
            # Find the sharing list
            shared_list = mongoUtils.get("sharing_lists", ns["shared_slice_key"])
            ns_inst_info[ns["ns-id"]] = shared_list["ns_list"][ns["nsd-id"]]
            logger.debug(f"NS {ns['nsd-id']} is shared!!")
            logger.debug(shared_list["ns_list"][ns["nsd-id"]])
            nest["conf_comp"]["nf"].append(ns["nsd-id"])
            continue
        ns_inst_info[ns["ns-id"]] = {}
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        selected_vim = ns["placement_loc"]["vim"]
        nfvo_vim_account = vim_dict[selected_vim]["nfvo_vim_account"][ns["nfvo-id"]]
        nfvo_inst_ns = target_nfvo_obj.instantiateNs(ns["ns-name"], ns["nsd-id"], nfvo_vim_account)
        ns_inst_info[ns["ns-id"]][ns["placement_loc"]["location"]] = {
            "nfvo_inst_ns": nfvo_inst_ns,
            "nfvo-id": ns["nfvo-id"],
            "ns-name": ns["ns-name"],
            "slice_id": nest["_id"],
            "vim": selected_vim,
        }
        # Check if this the first slice of a sharing list
        if ns["shared_function"] == 1:
            shared_list = mongoUtils.get("sharing_lists", ns["shared_slice_key"])
            ns_inst_info[ns["ns-id"]]["shared"] = True
            shared_list["ns_list"][ns["nsd-id"]] = ns_inst_info[ns["ns-id"]]
            mongoUtils.update("sharing_lists", ns["shared_slice_key"], shared_list)
            logger.debug("Added NS to the shared list")
        nest["conf_comp"]["nf"].append(ns["nsd-id"])
        time.sleep(4)
        time.sleep(2)

    # Get the nsr for each service and wait for the activation
    for ns in total_ns_list:
        target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
        target_nfvo_obj = pickle.loads(mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"])
        site = ns["placement_loc"]
        nfvo_inst_ns_id = ns_inst_info[ns["ns-id"]][site["location"]]["nfvo_inst_ns"]
        insr = target_nfvo_obj.getNsr(nfvo_inst_ns_id)
        while insr["operational-status"] != "running" or insr["config-status"] != "configured":
            if insr["operational-status"] == "failed":
                error_message = (
                    f"Network Service {ns['nsd-id']} failed to start on NFVO {ns['nfvo-id']}."
                )
                logger.error(error_message)
                nest["ns_inst_info"] = ns_inst_info
                nest["status"] = f"Failed - {error_message}"
                mongoUtils.update("slice", nest["_id"], nest)
                return
            time.sleep(10)
            insr = target_nfvo_obj.getNsr(nfvo_inst_ns_id)
        nest["deployment_time"]["NS_Deployment_Time"][ns["ns-name"]] = format(
            time.time() - ns["start_time"], ".4f"
        )
        # Get the IPs of the instantiated NS
        vnf_list = []
        vnfr_id_list = target_nfvo_obj.getVnfrId(insr)
        for ivnfr_id in vnfr_id_list:
            vnfr = target_nfvo_obj.getVnfr(ivnfr_id)
            vnf_list.append(target_nfvo_obj.getIPs(vnfr))
        ns_inst_info[ns["ns-id"]][site["location"]]["vnfr"] = vnf_list

    nest["ns_inst_info"] = ns_inst_info
    mongoUtils.update("slice", nest["_id"], nest)

    # If monitoring parameter is set, send the ns_list to nfv_mon module
    if monitoring and mon_producer:
        mon_producer.send(topic="nfv_mon", value={"action": "create", "ns_list": ns_inst_info})
        nest["slice_monitoring"]["nfv_ns_status_monitoring"] = True

    # *** STEP-3b: Radio Slice Configuration ***
    if mongoUtils.count("ems") <= 0:
        logger.warning("There is no registered EMS")
    else:
        # Add the management IPs for the NS sent ems in ems_messages:
        ems_radio_data = {
            "ue_DL_throughput": nest["ue_DL_throughput"],
            "ue_UL_throughput": nest["ue_UL_throughput"],
            "group_communication_support": nest["group_communication_support"],
            "number_of_terminals": nest["number_of_terminals"],
            "positional_support": nest["positional_support"],
            "radio_spectrum": nest["radio_spectrum"],
            "device_velocity": nest["device_velocity"],
            "terminal_density": nest["terminal_density"],
        }
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
                            try:
                                ns_info = ns_inst_info[ns["ns-id"]][connection[key]["location"]]
                            except KeyError:
                                ns_info = ns_inst_info[ns["ns-id"]]["Core"]
                            ns_data = {
                                "name": ns["ns-name"],
                                "location": ns["placement_loc"]["location"],
                                "vnf_list": ns_info["vnfr"],
                            }
                            key_data["ns"].append(ns_data)
                try:
                    key_data["pnf"] = connection[key]["pnf_list"]
                except KeyError:
                    pass
                if key_data:
                    data[key] = key_data
            if data:
                data["slice_sla"] = ems_radio_data
                data["slice_id"] = nest["_id"]
                for ems_id in ems_id_list:
                    messages = ems_messages.get(ems_id, [])
                    messages.append(data)
                    ems_messages[ems_id] = messages

        for ems_id, ems_message in ems_messages.items():
            # Find the EMS
            target_ems = mongoUtils.find("ems", {"id": ems_id})
            if not target_ems:
                # Error handling: There is no such EMS
                logger.error("EMS {} not found - No configuration".format(ems_id))
                continue
            target_ems_obj = pickle.loads(mongoUtils.find("ems_obj", {"id": ems_id})["obj"])
            # Send the message
            for imessage in ems_message:
                target_ems_obj.conf_radio(imessage)
            nest["conf_comp"]["ems"].append(ems_id)
        nest["ems_data"] = ems_messages
        nest["deployment_time"]["Radio_Configuration_Time"] = format(
            time.time() - radio_start_time, ".4f"
        )

    # *** STEP-4: Finalize ***
    # Create Grafana Dashboard for monitoring
    # Create the NS status panel
    if monitoring:
        # Open the Grafana Dashboard template
        monitoring_slice_id = "slice_" + nest["_id"].replace("-", "_")
        with open("/katana-grafana/templates/new_dashboard.json", mode="r") as dashboard_file:
            new_dashboard = json.load(dashboard_file)
            new_dashboard["dashboard"]["title"] = monitoring_slice_id
            new_dashboard["dashboard"]["uid"] = nest["_id"]
        # Add the dashboard panels
        # Add the NS Status panels
        expr = "ns_status" + '{slice_id="' + nest["_id"] + '"}'
        targets = [
            {"expr": expr, "legendFormat": "", "interval": "", "format": "table", "instant": True}
        ]
        infra_targets = {}
        for ns in ns_inst_info.values():
            for key, value in ns.items():
                # Check if the VIM supports infrastructure monitoring
                selected_vim = mongoUtils.find("vim", {"id": value["vim"]})
                try:
                    vim_monitoring = selected_vim["type"]
                    vim_monitoring_list = infra_targets.get(vim_monitoring, [])
                    for ivnf in value["vnfr"]:
                        vim_monitoring_list += ivnf["vm_list"]
                    infra_targets[vim_monitoring] = vim_monitoring_list
                except KeyError:
                    pass
        # Create the VM Monitoring panels
        PANELS = [
            "vm_state",
            "vm_cpu_cpu_time",
            "vm_cpu_overall_cpu_usage",
            "vm_memory_actual",
            "vm_memory_available",
            "vm_memory_usage",
            "vm_disk_read_bytes",
            "vm_disk_write_bytes",
            "vm_disk_errors",
        ]
        with open("/katana-grafana/templates/new_vm_monitoring_panel.json", mode="r") as panel_file:
            vm_panel_template = json.load(panel_file)
            for i, panel in enumerate(PANELS):
                vm_panel = copy.deepcopy(vm_panel_template)
                vm_panel["title"] = panel
                vm_panel["gridPos"] = {"h": 8, "w": 12, "x": 13, "y": i * 9}
                vm_panel["id"] = 10 + i
                vm_targets = []
                for vim_type, vm_list in infra_targets.items():
                    for vm in vm_list:
                        expr = (
                            vim_type
                            + "_"
                            + panel
                            + '{project=~".*'
                            + nest["_id"]
                            + '",vm_name="'
                            + vm
                            + '"}'
                        )
                        vm_targets.append({"expr": expr, "interval": "", "legendFormat": ""})
                vm_panel["targets"] = vm_targets
                new_dashboard["dashboard"]["panels"].append(vm_panel)
        # Read and fill the NS Status panel template
        with open("/katana-grafana/templates/new_ns_status_panel.json", mode="r") as panel_file:
            ns_panel = json.load(panel_file)
            ns_panel["targets"] = targets
            new_dashboard["dashboard"]["panels"].append(ns_panel)
        # Add the WIM Monitoring panel
        if wim_monitoring:
            # Read and fill the panel template
            with open("/katana-grafana/templates/new_wim_panel.json", mode="r") as panel_file:
                wim_panel = json.load(panel_file)
                wim_panel["targets"].append(
                    {
                        "expr": f"rate({monitoring_slice_id}_flows[1m])",
                        "interval": "",
                        "legendFormat": "",
                        "refId": "A",
                    }
                )
                new_dashboard["dashboard"]["panels"].append(wim_panel)
        mon_producer.send(
            "nfv_mon",
            value={
                "action": "katana_mon",
                "slice_info": {"slice_id": nest["_id"], "status": "running"},
            },
        )

        # Use the Grafana API in order to create the new dashboard for the new slice
        grafana_url = "http://katana-grafana:3000/api/dashboards/db"
        headers = {"accept": "application/json", "content-type": "application/json"}
        grafana_user = os.getenv("GF_SECURITY_ADMIN_USER", "admin")
        grafana_passwd = os.getenv("GF_SECURITY_ADMIN_PASSWORD", "admin")
        r = requests.post(
            url=grafana_url,
            headers=headers,
            auth=(grafana_user, grafana_passwd),
            data=json.dumps(new_dashboard),
        )
        logger.info(f"Created new Grafana dashboard for slice {nest['_id']}")
    logger.info(f"{nest['_id']} Status: Running")
    nest["status"] = "Running"
    nest["deployment_time"]["Slice_Deployment_Time"] = format(
        time.time() - nest["created_at"], ".4f"
    )
    mongoUtils.update("slice", nest["_id"], nest)


def delete_slice(slice_id, force=False):
    """
    Deletes the given network slice
    """

    # Update the slice status in mongo db
    slice_json = mongoUtils.get("slice", slice_id)
    slice_json["status"] = "Terminating"
    mongoUtils.update("slice", slice_json["_id"], slice_json)
    logger.info(f"{slice_json['_id']} Status: Terminating")

    # Check if slice monitoring has been enabled
    monitoring = os.getenv("KATANA_MONITORING", None)
    slice_monitoring = slice_json.get("slice_monitoring", None)
    mon_producer = None

    if monitoring:
        # Create the Kafka producer
        mon_producer = create_producer()
        mon_producer.send(
            "nfv_mon",
            value={
                "action": "katana_mon",
                "slice_info": {"slice_id": slice_id, "status": "terminating"},
            },
        )

    # *** Step-1: Radio Slice Configuration ***
    if slice_json["conf_comp"]["ems"]:
        ems_messages = slice_json.get("ems_data", None)
        if ems_messages:
            for ems_id, ems_message in ems_messages.items():
                # Find the EMS
                target_ems = mongoUtils.find("ems", {"id": ems_id})
                if not target_ems or ems_id not in slice_json["conf_comp"]["ems"]:
                    # Error handling: There is no such EMS
                    logger.error("EMS {} not found - No configuration".format(ems_id))
                    continue
                target_ems_obj = pickle.loads(mongoUtils.find("ems_obj", {"id": ems_id})["obj"])
                target_ems_obj.del_slice(ems_message)
    else:
        logger.info("There was not EMS configuration")

    # *** Step-2: WAN Slice ***
    wim_data = slice_json.get("wim_data", None)
    if wim_data:
        # Select WIM - Assume that there is only one registered
        wim_list = list(mongoUtils.index("wim"))
        if wim_list:
            target_wim = wim_list[0]
            target_wim_id = target_wim["id"]
            target_wim_obj = pickle.loads(mongoUtils.find("wim_obj", {"id": target_wim_id})["obj"])
            target_wim_obj.del_slice(slice_id)
            try:
                del target_wim["slices"][slice_json["_id"]]
            except KeyError:
                logger.warning(f"Slice {slice_id} not in WIM {target_wim_id}")
            else:
                mongoUtils.update("wim", target_wim["_id"], target_wim)
        else:
            err = "Cannot find WIM - WAN Slice will not be deleted"
            logger.warning(err)
            slice_json["status"] = "Error"
            if monitoring:
                mon_producer.send(
                    "nfv_mon",
                    value={
                        "action": "katana_mon",
                        "slice_info": {"slice_id": slice_id, "status": "error"},
                    },
                )
            slice_json["error"] = slice_json.get("error", "") + err
            mongoUtils.update("slice", slice_json["_id"], slice_json)
    else:
        logger.info("There was no WIM configuration")

    # *** Step-3: Cloud ***
    vim_error_list = []
    try:
        total_ns_list = slice_json["total_ns_list"]
        ns_inst_info = slice_json["ns_inst_info"]
        for ns in total_ns_list:
            if ns["nsd-id"] not in slice_json["conf_comp"]["nf"]:
                logger.error(f"{ns['nsd-id']} was not instantiated successfully")
                continue
            # Get the NFVO
            nfvo_id = ns["nfvo-id"]
            target_nfvo = mongoUtils.find("nfvo", {"id": ns["nfvo-id"]})
            if not target_nfvo:
                logger.warning(
                    "NFVO with id {} was not found - NSs won't terminate".format(nfvo_id)
                )
                vim_error_list += ns["vims"]
                continue
            target_nfvo_obj = pickle.loads(
                mongoUtils.find("nfvo_obj", {"id": ns["nfvo-id"]})["obj"]
            )
            # Stop the NS
            nfvo_inst_ns = ns_inst_info[ns["ns-id"]][ns["placement_loc"]["location"]][
                "nfvo_inst_ns"
            ]
            target_nfvo_obj.deleteNs(nfvo_inst_ns)
            while True:
                if target_nfvo_obj.checkNsLife(nfvo_inst_ns):
                    break
                time.sleep(5)
    except KeyError as e:
        err = f"Error, not all NSs started or terminated correctly {e}"
        logger.warning(err)
        slice_json["status"] = "Error"
        if monitoring:
            mon_producer.send(
                "nfv_mon",
                value={
                    "action": "katana_mon",
                    "slice_info": {"slice_id": slice_id, "status": "error"},
                },
            )
        slice_json["error"] = slice_json.get("error", "") + err
        mongoUtils.update("slice", slice_json["_id"], slice_json)

    vim_dict = slice_json.get("vim_list", {})
    for vim, vim_info in vim_dict.items():
        try:
            # Delete the new tenants from the NFVO
            for nfvo, vim_account in vim_info["nfvo_vim_account"].items():
                # Get the NFVO
                target_nfvo = mongoUtils.find("nfvo", {"id": nfvo})
                target_nfvo_obj = pickle.loads(mongoUtils.find("nfvo_obj", {"id": nfvo})["obj"])
                # Delete the VIM and update nfvo db
                target_nfvo_obj.deleteVim(vim_account)
                target_nfvo["tenants"][slice_json["_id"]].remove(vim_account)
                if len(target_nfvo["tenants"][slice_json["_id"]]) == 0:
                    try:
                        del target_nfvo["tenants"][slice_json["_id"]]
                    except KeyError:
                        logger.warning(f"Slice {slice_id} not in NFO {nfvo}")
                    else:
                        mongoUtils.update("nfvo", target_nfvo["_id"], target_nfvo)
            # Delete the tenants from every vim
            if vim not in vim_error_list:
                # Get the VIM
                target_vim = mongoUtils.find("vim", {"id": vim})
                if not target_vim:
                    logger.warning("VIM id {} was not found - Tenant won't be deleted".format(vim))
                    continue
                target_vim_obj = pickle.loads(mongoUtils.find("vim_obj", {"id": vim})["obj"])
                target_vim_obj.delete_proj_user(target_vim["tenants"][slice_json["_id"]])
                try:
                    del target_vim["tenants"][slice_json["_id"]]
                except KeyError:
                    logger.warning(f"Slice {slice_id} not in VIM {vim}")
                else:
                    mongoUtils.update("vim", target_vim["_id"], target_vim)
        except KeyError as e:
            err = f"Error, not all tenants created or removed correctly {e}"
            logger.warning(err)
            slice_json["status"] = "Error"
            if monitoring:
                mon_producer.send(
                    "nfv_mon",
                    value={
                        "action": "katana_mon",
                        "slice_info": {"slice_id": slice_id, "status": "error"},
                    },
                )
            slice_json["error"] = slice_json.get("error", "") + err
            mongoUtils.update("slice", slice_json["_id"], slice_json)

    if "error" not in slice_json:
        mongoUtils.delete("slice", slice_json["_id"])
        if monitoring:
            mon_producer.send(
                "nfv_mon",
                value={
                    "action": "katana_mon",
                    "slice_info": {"slice_id": slice_id, "status": "deleted"},
                },
            )
    elif "error" in slice_json and force:
        mongoUtils.delete("slice", slice_json["_id"])
        if monitoring:
            mon_producer.send(
                "nfv_mon",
                value={
                    "action": "katana_mon",
                    "slice_info": {"slice_id": slice_id, "status": "deleted"},
                },
            )

    # Remove Slice from the tenants list on functions
    for func_id in slice_json["functions"]:
        ifunc = mongoUtils.get("func", func_id)
        try:
            ifunc["tenants"].remove(slice_json["_id"])
        except (KeyError, ValueError):
            logger.warning(f"Slice {slice_id} not in function {func_id}")
        else:
            mongoUtils.update("func", func_id, ifunc)

    # Remove Slice dashboard
    if monitoring and slice_monitoring:
        # Use the Grafana API in order to delete the new dashboard for the new slice
        grafana_url = f"http://katana-grafana:3000/api/dashboards/uid/{slice_id}"
        headers = {"accept": "application/json", "content-type": "application/json"}
        grafana_user = os.getenv("GF_SECURITY_ADMIN_USER", "admin")
        grafana_passwd = os.getenv("GF_SECURITY_ADMIN_PASSWORD", "admin")
        r = requests.delete(url=grafana_url, headers=headers, auth=(grafana_user, grafana_passwd),)
        logger.info(f"Deleted Grafana dashboard for slice {slice_id}")
        # Stop the threads monitoring NS status of the slice
        ns_inst_info = slice_json["ns_inst_info"]
        mon_producer.send(topic="nfv_mon", value={"action": "delete", "ns_list": ns_inst_info})
