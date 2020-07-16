#!/usr/bin/env python3

"""
Read the collected NFV metrics and expose them to Prometheus
"""

import logging

from katana.utils.kafkaUtils.kafkaUtils import create_consumer, create_topic
from prometheus_client import start_http_server, Gauge

# Create the logger
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def mon_start(ns_list):
    """
    Starts the monitoring of new network services
    """
    # for ns in ns_list:
    #     ns_name = ns["name"].replace("-", "_")
    #     ns_status = Gauge(ns_name, "Status of the NS")
    logger.debug(ns_list)


def mon_stop(ns_list):
    """
    Stops the monitoring os new network services
    """
    logger.debug(ns_list)


def start_exporter():
    """
    Starts the NFV Monitoring. Creates the Kafka consumer
    """

    # Create the thread dictionary
    ns_thread_dict = {}

    # Create the Kafka topic
    create_topic("nfv_mon")

    # Create the Kafka consumer
    consumer = create_consumer("nfv_mon")

    for message in consumer:
        ns_list = message.value["ns_list"]
        if message.value["action"] == "create":
            mon_start(ns_list)
        else:
            mon_stop(ns_list)


if __name__ == "__main__":
    start_http_server(8002)
    start_exporter()
