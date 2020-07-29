#!/usr/bin/env python3

"""
Read the collected NFV metrics and expose them to Prometheus
"""

import logging
import requests
import json
import os

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


def katana_mon(metric, n_slices, slice_info):
    """
    Updates the slice monitoring status
    """
    if slice_info["status"] == "running":
        metric.labels(slice_info["slice_id"]).set(0)
        n_slices.inc()
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
        n_slices.dec()


def start_exporter():
    """
    Starts the NFV Monitoring. Creates the Kafka consumer
    """

    # Add the Grafana new Home Dashboard
    with open("katana/dashboards/katana.json", mode="r") as home_dash_file:
        home_dash = json.load(home_dash_file)
        # Use the Grafana API in order to create the new home dashboard
        grafana_url = "http://katana-grafana:3000/api/dashboards/db"
        headers = {"accept": "application/json", "content-type": "application/json"}
        grafana_user = os.getenv("GF_SECURITY_ADMIN_USER", "admin")
        grafana_passwd = os.getenv("GF_SECURITY_ADMIN_PASSWORD", "admin")
        r = requests.post(
            url=grafana_url,
            headers=headers,
            auth=(grafana_user, grafana_passwd),
            data=json.dumps(home_dash),
        )

    # Set the default dashboard to the new katana home dashboard
    grafana_url = "http://katana-grafana:3000/api/org/preferences"
    preferences = {"theme": "", "homeDashboardId": 1, "timezone": "cet"}
    r = requests.put(
        url=grafana_url,
        headers=headers,
        auth=(grafana_user, grafana_passwd),
        data=json.dumps(preferences),
    )

    # Create the Katana Home Monitoring metric
    katana_home = Gauge("katana_status", "Katana Slice Status", ["slice_id"])
    total_slices = Gauge("total_slices", "Number of running slices")

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
            katana_mon(katana_home, total_slices, message.value["slice_info"])


if __name__ == "__main__":
    start_http_server(8002)
    start_exporter()
