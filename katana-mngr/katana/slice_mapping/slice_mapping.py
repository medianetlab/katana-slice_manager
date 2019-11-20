from katana.api.mongoUtils import mongoUtils
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


GST_KEYS_OBJ = ("slice_des", "delay_tolerance", "network_DL_throughput",
                "ue_DL_throughput", "network_UL_throughput",
                "ue_UL_throughput", "deterministic_communication",
                "group_communication_support", "isolation_level",
                "mtu", "mission_critical_support", "mmtel_support",
                "nb_iot", "number_of_connections", "number_of_terminals",
                "positional_support", "simultaneous_nsi", "nonIP_traffic",
                "device_velocity", "terminal_density", "ns_des_id",
                "test_des_id", "performance_monitoring",
                "performance_prediction")
GST_KEYS_LIST = ("coverage", "radio_spectrum", "qos", "ns_list",
                 "probe_list")


def gst_to_nest(gst):
    """
    Function that translates the gst to nest
    """
    # *** Check if there are references for  slice, ns_des, test_des***

    # *** Recreate the GST ***
    for gst_key in GST_KEYS_OBJ:
        gst[gst_key] = gst.get(gst_key, None)
    for gst_key in GST_KEYS_LIST:
        gst[gst_key] = gst.get(gst_key, [])

    # *** Calculate the type of the slice (sst) ***
    # Based on the Supported Slices inputs will determine sst and sd values
    if gst["delay_tolerance"]:
        if gst["nb_iot"]:
            # MIoT
            sst = 3
        else:
            # eMBB
            sst = 1
    else:
        if gst["nb_iot"]:
            # TBD
            pass
        else:
            # uRLLC
            sst = 2

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
                # TODO: Error Handling
                return
        else:
            break

    # Check if there are more than one supported sst with same type
    if len(sst_list) > 1:
        # Check the sst supported locations against coverage
        max_match = 0
        for i, _slice in enumerate(sst_list):
            tot = 0
            for location in gst["coverage"]:
                if location in _slice["supported_locations"]:
                    tot += 1
            if tot > max_match:
                max_match = tot
                max_pos = i
