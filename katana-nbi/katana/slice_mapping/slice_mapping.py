import logging
from logging import handlers
import uuid

from katana.shared_utils.mongoUtils import mongoUtils

# Logging Parameters
logger = logging.getLogger(__name__)
file_handler = handlers.RotatingFileHandler("katana.log", maxBytes=10000, backupCount=5)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

NEST_FIELDS = ("base_slice_descriptor", "service_descriptor", "test_descriptor")

SLICE_DES_OBJ = (
    "base_slice_des_id",
    "base_slice_des_ref",
    "delay_tolerance",
    "network_DL_throughput",
    "ue_DL_throughput",
    "network_UL_throughput",
    "ue_UL_throughput",
    "deterministic_communication",
    "group_communication_support",
    "isolation_level",
    "mtu",
    "mission_critical_support",
    "mmtel_support",
    "nb_iot",
    "number_of_connections",
    "number_of_terminals",
    "positional_support",
    "simultaneous_nsi",
    "nonIP_traffic",
    "device_velocity",
    "terminal_density",
)
SLICE_DES_LIST = ("coverage", "radio_spectrum", "qos")

SERVICE_DES_OBJ = ()
SERVICE_DES_LIST = ("ns_list",)

TEST_DES_OBJ = ("performance_monitoring", "performance_prediction")
TEST_DES_LIST = ("probe_list",)


# Calculate the Required generation
def calc_find_data(gen, location, func):
    if gen == 5:
        return {"location": location, "gen": 5, "func": func}
    else:
        return {"location": location, "gen": 5, "func": func}


def nest_mapping(req):
    """
    Function that maps nest to the underlying network functions
    """
    # Store the gst in DB
    mongoUtils.add("gst", req)

    nest = {"_id": req["_id"]}

    # Recreate the nest req
    for field in NEST_FIELDS:
        req[field] = req.get(field, None)

    # ****** STEP 1: Slice Descriptor ******
    if not req["base_slice_descriptor"]:
        logger.error("No Base Slice Descriptor given - Exit")
        return "NEST Error: No Base Slice Descriptor given", 400
    req_slice_des = req["base_slice_descriptor"]
    # *** Recreate the NEST ***
    for req_key in SLICE_DES_OBJ:
        req_slice_des[req_key] = req_slice_des.get(req_key, None)
    for req_key in SLICE_DES_LIST:
        req_slice_des[req_key] = req_slice_des.get(req_key, [])

    # *** Check if there are references for slice ***
    if req_slice_des["base_slice_des_ref"]:
        ref_slice = mongoUtils.find(
            "base_slice_des_ref", {"base_slice_des_id": req_slice_des["base_slice_des_ref"]}
        )
        if ref_slice:
            for key, value in req_slice_des.items():
                try:
                    if value is None:
                        req_slice_des[key] = ref_slice[key]
                except KeyError:
                    continue
        else:
            logger.error(
                "slice_descriptor {} not found".format(req_slice_des["base_slice_des_ref"])
            )
            return "Error: referenced slice_descriptor not found", 400

    # *************************** Start the mapping ***************************
    # Currently supports:
    # 1) If delay_tolerance --> EMBB else --> URLLC
    #    If EMBB --> EPC Placement=@Core. If URLLC --> EPC Placement=@Edge
    # 2) If network throughput > 100 Mbps --> Type=5G
    # *************************************************************************
    functions_list = []

    if req_slice_des["network_DL_throughput"]["guaranteed"] > 100000:
        gen = 5
    else:
        gen = 4

    # *** Calculate the type of the slice (sst) ***
    if req_slice_des["delay_tolerance"]:
        # EMBB
        nest["sst"] = 1
        epc = mongoUtils.find("func", calc_find_data(gen, "Core", 0))
        if not epc:
            return "Error: Not available Core Network Functions", 400
        connections = []
        not_supp_loc = []
        for location in req_slice_des["coverage"]:
            enb = mongoUtils.find("func", calc_find_data(gen, location, 1))
            if not enb:
                not_supp_loc.append(location)
            else:
                connections.append({"core": epc, "radio": enb})
                enb["tenants"].append(nest["_id"])
                mongoUtils.update("func", enb["_id"], enb)
                functions_list.append(enb["_id"])
        if not epc or not connections:
            return "Error: Not available Network Functions", 400
        epc["tenants"].append(nest["_id"])
        mongoUtils.update("func", epc["_id"], epc)
        functions_list.append(epc["_id"])
        for location in not_supp_loc:
            logger.warning(f"Location {location} not supported")
            req_slice_des["coverage"].remove(location)
    else:
        # URLLC
        nest["sst"] = 2
        connections = []
        not_supp_loc = []
        for location in req_slice_des["coverage"]:
            epc = mongoUtils.find("func", calc_find_data(gen, location, 0))
            enb = mongoUtils.find("func", calc_find_data(gen, location, 1))
            if not epc or not enb:
                not_supp_loc.append(location)
            else:
                connections.append({"core": epc, "radio": enb})
                epc["tenants"].append(nest["_id"])
                enb["tenants"].append(nest["_id"])
                mongoUtils.update("func", enb["_id"], enb)
                mongoUtils.update("func", epc["_id"], epc)
                functions_list.extend([epc["_id"], enb["_id"]])
        if not connections:
            return "Error: Not available Network Functions", 400
        for location in not_supp_loc:
            logger.warning(f"Location {location} not supported")
            req_slice_des["coverage"].remove(location)

    nest["connections"] = connections
    nest["functions"] = functions_list

    # Values to be copied to NEST
    KEYS_TO_BE_COPIED = (
        "network_DL_throughput",
        "ue_DL_throughput",
        "network_UL_throughput",
        "ue_UL_throughput",
        "group_communication_support",
        "mtu",
        "number_of_terminals",
        "positional_support",
        "radio_spectrum",
        "device_velocity",
        "terminal_density",
        "coverage",
    )
    for key in KEYS_TO_BE_COPIED:
        nest[key] = req_slice_des[key]

    # Create the shared value
    nest["shared"] = {
        "isolation": req_slice_des["isolation_level"],
        "simultaneous_nsi": req_slice_des["simultaneous_nsi"],
    }

    # ****** STEP 2: Service Descriptor ******
    if req["service_descriptor"]:
        req_service_des = req["service_descriptor"]
        # *** Recreate the NEST ***
        for req_key in SERVICE_DES_OBJ:
            req_service_des[req_key] = req_service_des.get(req_key, None)
        for req_key in SERVICE_DES_LIST:
            req_service_des[req_key] = req_service_des.get(req_key, [])
        # Create the NS field on Nest
        nest["ns_list"] = req_service_des["ns_list"]

        # # Replace Placement with location in each NS
        # for ns in nest["ns_list"]:
        #     ns["placement"] = (
        #         lambda x: {"location": ["Core"]} if not x else
        #         {"location": req_slice_des["coverage"]})(ns["placement"])

    # ****** STEP 3: Service Descriptor ******
    if req["test_descriptor"]:
        req_test_des = req["test_descriptor"]
        # *** Recreate the NEST ***
        for req_key in TEST_DES_OBJ:
            req_test_des[req_key] = req_test_des.get(req_key, None)
        for req_key in TEST_DES_LIST:
            req_test_des[req_key] = req_test_des.get(req_key, [])
        # Create the Probe field on Nest
        nest["probe_list"] = req_test_des["probe_list"]

    if not mongoUtils.find(
        "base_slice_des_ref",
        {"base_slice_des_id": req["base_slice_descriptor"]["base_slice_des_id"]},
    ):
        new_uuid = str(uuid.uuid4())
        req["base_slice_descriptor"]["_id"] = new_uuid
        mongoUtils.add("base_slice_des_ref", req["base_slice_descriptor"])
    return nest, 0
