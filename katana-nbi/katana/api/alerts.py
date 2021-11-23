import logging
from logging import handlers
from flask import request
from flask_classful import FlaskView

from katana.shared_utils.mongoUtils import mongoUtils
from katana.shared_utils.kafkaUtils.kafkaUtils import create_producer

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


class AlertView(FlaskView):
    route_prefix = "/api/"

    def post(self):
        """
        Get a new alert
        """
        alert_message = request.json
        # Check the alert type
        for ialert in alert_message["alerts"]:
            if ialert["labels"]["alertname"] == "NSFailing":
                ns_id = ialert["labels"]["ns_name"].split("__")[1].replace("_", "-")
                location = ialert["labels"]["ns_name"].split("__")[2]
                slice_id = ialert["labels"]["slice_id"]
                logger.warning(
                    f"Failing Network Service {ns_id} in {location} for slice {slice_id}"
                )
                # Update the NEST
                nest = mongoUtils.get("slice", slice_id)
                nest["ns_inst_info"][ns_id][location]["status"] = "Error"
                # Add the error to the runtime errors
                ns_errors = nest["runtime_errors"].get("ns", [])
                ns_errors.append(ns_id)
                nest["runtime_errors"]["ns"] = ns_errors
                nest["status"] = "Runtime Error"
                mongoUtils.update("slice", slice_id, nest)
                # Update monitoring status
                if nest["slice_monitoring"]:
                    mon_producer = create_producer()
                    mon_producer.send(
                        "nfv_mon",
                        value={
                            "action": "katana_mon",
                            "slice_info": {"slice_id": nest["_id"], "status": "runtime_error"},
                        },
                    )
                # TODO: Notify APEX
        return "Alert received", 200
