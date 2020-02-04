from katana.shared_utils.mongoUtils import mongoUtils
import logging
import uuid


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

GST_FIELDS = ("base_slice_descriptor", "service_descriptor", "test_descriptor")

SLICE_DES_OBJ = ("base_slice_des_id", "base_slice_des_ref", "delay_tolerance",
                 "network_DL_throughput", "ue_DL_throughput",
                 "network_UL_throughput", "ue_UL_throughput",
                 "deterministic_communication", "group_communication_support",
                 "isolation_level", "mtu", "mission_critical_support",
                 "mmtel_support", "nb_iot", "number_of_connections",
                 "number_of_terminals", "positional_support",
                 "simultaneous_nsi", "nonIP_traffic",
                 "device_velocity", "terminal_density")
SLICE_DES_LIST = ("coverage", "radio_spectrum", "qos")

SERVICE_DES_OBJ = ()
SERVICE_DES_LIST = ("ns_list",)

TEST_DES_OBJ = ("performance_monitoring", "performance_prediction")
TEST_DES_LIST = ("probe_list",)


def gst_to_nest(gst):
    """
    Function that translates the gst to nest
    """
    nest = {"_id": gst["_id"]}
    for field in GST_FIELDS:
        gst[field] = gst.get(field, None)

    # ****** STEP 1: Slice Descriptor ******
    if not gst["base_slice_descriptor"]:
        logger.error("No Base Slice Descriptor given - Exit")
        return "GST Error: No Base Slice Descriptor given", 400
    gst_slice_des = gst["base_slice_descriptor"]
    # *** Recreate the GST ***
    for gst_key in SLICE_DES_OBJ:
        gst_slice_des[gst_key] = gst_slice_des.get(gst_key, None)
    for gst_key in SLICE_DES_LIST:
        gst_slice_des[gst_key] = gst_slice_des.get(gst_key, [])

    # *** Check if there are references for slice ***
    if gst_slice_des["base_slice_des_ref"]:
        ref_slice = mongoUtils.find("base_slice_des_ref", {"base_slice_des_id":
                                    gst_slice_des["base_slice_des_ref"]})
        if ref_slice:
            for key, value in gst_slice_des.items():
                try:
                    if value is None:
                        gst_slice_des[key] = ref_slice[key]
                except KeyError:
                    continue
        else:
            logger.error("slice_descriptor {} not found".
                         format(gst_slice_des["base_slice_des_ref"]))
            return "Error: referenced slice_descriptor not found", 400

    # *** Calculate the type of the slice (sst) ***
    # Based on the Supported Slices inputs will determine sst and sd values
    if gst_slice_des["delay_tolerance"]:
        if gst_slice_des["nb_iot"]:
            # MIoT
            sst = 3
        else:
            # eMBB
            sst = 1
    else:
        if gst_slice_des["nb_iot"]:
            # TBD
            sst = 1
        else:
            # uRLLC
            if len(gst_slice_des["coverage"]) > 0:
                sst = 2
            else:
                logger.warning("No edge location - embb placement")
                sst = 1

    # Get the supported slices list
    while True:
        sst_list = list(mongoUtils.find_all("sst", {"sst": sst}))
        # If there are not supported sst 2 or 3, search supported sst 1 (embb)
        if not sst_list:
            if sst > 1:
                logger.warning(
                    "There are not supported sst {} types - Searching for eMBB"
                    .format(sst))
                sst = 1
            else:
                logger.error("There are no supported eMBB slices")
                return "Error: There are no supported slices", 400
        else:
            break

    # Check if there are more than one supported sst with same type
    if len(sst_list) > 1:
        # Check the sst supported locations against coverage
        max_match = 0
        max_pos = 0
        for i, _slice in enumerate(sst_list):
            tot = 0
            for location in gst_slice_des["coverage"]:
                if location in _slice["supported_locations"]:
                    tot += 1
            if tot > max_match:
                max_match = tot
                max_pos = i

        selected_slice = sst_list[max_pos]
    else:
        selected_slice = sst_list[0]
    nest["sst_id"] = selected_slice["_id"]

    # *** Check which locations are not covered by the supported sst ***
    remove_locations = []
    for location in gst_slice_des["coverage"]:
        if location not in selected_slice["supported_locations"]:
            remove_locations.append(location)
            logger.warning("Location {} is not supported for that type of sst".
                           format(location))
    nest["coverage"] = [location for location in gst_slice_des["coverage"] if
                        location not in remove_locations]

    # Values to be copied to NEST
    KEYS_TO_BE_COPIED = ("network_DL_throughput", "ue_DL_throughput",
                         "network_UL_throughput", "ue_UL_throughput",
                         "group_communication_support", "mtu",
                         "number_of_terminals", "positional_support",
                         "radio_spectrum", "device_velocity",
                         "terminal_density")
    for key in KEYS_TO_BE_COPIED:
        nest[key] = gst_slice_des[key]

    # Create the shared value
    nest["shared"] = {"isolation": gst_slice_des["isolation_level"],
                      "simultaneous_nsi": gst_slice_des["simultaneous_nsi"]}

    # ****** STEP 2: Service Descriptor ******
    if gst["service_descriptor"]:
        gst_service_des = gst["service_descriptor"]
        # *** Recreate the GST ***
        for gst_key in SERVICE_DES_OBJ:
            gst_service_des[gst_key] = gst_service_des.get(gst_key, None)
        for gst_key in SERVICE_DES_LIST:
            gst_service_des[gst_key] = gst_service_des.get(gst_key, [])
        # Create the NS field on Nest
        nest["ns_list"] = gst_service_des["ns_list"]

    # ****** STEP 3: Service Descriptor ******
    if gst["test_descriptor"]:
        gst_test_des = gst["test_descriptor"]
        # *** Recreate the GST ***
        for gst_key in TEST_DES_OBJ:
            gst_test_des[gst_key] = gst_test_des.get(gst_key, None)
        for gst_key in TEST_DES_LIST:
            gst_test_des[gst_key] = gst_test_des.get(gst_key, [])
        # Create the Probe field on Nest
        nest["probe_list"] = gst_test_des["probe_list"]

    mongoUtils.add("gst", gst)
    if not mongoUtils.find(
            "base_slice_des_ref",
            {"base_slice_des_id": gst["base_slice_descriptor"]
                ["base_slice_des_id"]}):
        new_uuid = str(uuid.uuid4())
        gst["base_slice_descriptor"]["_id"] = new_uuid
        mongoUtils.add("base_slice_des_ref", gst["base_slice_descriptor"])
    return nest, 0
