#!/usr/bin/env python3

"""
Read the collected NFV metrics and expose them to Prometheus
"""

import logging
import threading
import requests
import json

from katana.utils.kafkaUtils.kafkaUtils import create_consumer, create_topic
from katana.utils.threadingUtis.threadingUtils import MonThread
from prometheus_client import start_http_server, Gauge

# Create the logger
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def mon_start(ns_list, ns_thread_dict, ns_status):
    """
    Starts the monitoring of new network services
    """
    logger.info("Starting Network Function Status monitoring")
    for ns_id, ns in ns_list.items():
        for key, value in ns.items():
            location = key.replace("-", "_")
            ns_name = value["ns-name"].replace("-", "_")
            metric_name = "ns_" + ns_name + "_" + location
            dict_entry = ns_thread_dict.get(metric_name, {})
            ns_status.labels(value["slice_id"], metric_name).set(1)
            new_thread = MonThread(value, ns_status, metric_name)
            new_thread.start()
            dict_entry[ns_id] = {"thread": new_thread, "metric": ns_status}
            ns_thread_dict[metric_name] = dict_entry


def mon_stop(ns_list, ns_thread_dict):
    """
    Stops the monitoring os new network services
    """
    logger.info("Stoping Network Function Status monitoring")
    for ns_id, ns in ns_list.items():
        for key, value in ns.items():
            location = key.replace("-", "_")
            ns_name = value["ns-name"].replace("-", "_")
            metric_name = "ns_" + ns_name + "_" + location
            mon_thread = ns_thread_dict[metric_name][ns_id]["thread"]
            mon_thread.stop()


def katana_mon(metric, slice_info):
    """
    Updates the slice monitoring status
    """
    if slice_info["status"] == "running":
        metric.labels(slice_info["slice_id"]).set(0)
    elif slice_info["status"] == "placement":
        metric.labels(slice_info["slice_id"]).set(1)
    elif slice_info["status"] == "provisioning":
        metric.labels(slice_info["slice_id"]).set(2)
    elif slice_info["status"] == "activation":
        metric.labels(slice_info["slice_id"]).set(3)
    elif slice_info["status"] == "terminating":
        metric.labels(slice_info["slice_id"]).set(10)
    elif slice_info["status"] == "error":
        metric.labels(slice_info["slice_id"]).set(11)
    elif slice_info["status"] == "deleted":
        metric.labels(slice_info["slice_id"]).set(12)


def start_exporter():
    """
    Starts the NFV Monitoring. Creates the Kafka consumer
    """

    # Create the Katana Home Monitoring metric
    katana_home = Gauge("katana_status", "Katana Slice Status", ["slice_id"])

    # Create the thread dictionary and the prometheus ns status metric
    ns_thread_dict = {}
    ns_status = Gauge("ns_status", "Network Service Status", ["slice_id", "ns_name"])

    # Create the Kafka topic
    create_topic("nfv_mon")

    # Create the Kafka consumer
    consumer = create_consumer("nfv_mon")

    for message in consumer:
        if message.value["action"] == "create":
            ns_list = message.value["ns_list"]
            mon_start(ns_list, ns_thread_dict, ns_status)
        elif message.value["action"] == "delete":
            ns_list = message.value["ns_list"]
            mon_stop(ns_list, ns_thread_dict)
        elif message.value["action"] == "katana_mon":
            katana_mon(katana_home, message.value["slice_info"])


if __name__ == "__main__":
    start_http_server(8002)
    start_exporter()
