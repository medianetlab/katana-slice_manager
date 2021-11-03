""" Katana Manager Base Application """

import logging
import logging.handlers
import uuid
import time

from katana.shared_utils.kafkaUtils import kafkaUtils
from katana.shared_utils.mongoUtils import mongoUtils
from katana.utils.sliceUtils import sliceUtils


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

# Create Kafka topic
kafkaUtils.create_topic("slice")

# Create the Kafka Consumer
consumer = kafkaUtils.create_consumer("slice")

# Create the initial core location
new_uuid = str(uuid.uuid4())
core_location_data = {
    "_id": new_uuid,
    "id": "core",
    "created_at": time.time(),
    "description": "The default Core location",
    "vims": [],
    "functions": [],
}
mongoUtils.add("location", core_location_data)

# Check for new messages
for message in consumer:
    logger.info("--- New Message ---")
    logger.info(
        "Topic: {0} | Partition: {1} | Offset: {2}".format(
            message.topic, message.partition, message.offset
        )
    )
    # Commit the latest received message
    consumer.commit()
    action = message.value["action"]
    # Add slice
    if action == "add":
        payload = message.value["message"]
        sliceUtils.add_slice(payload)
    # Delete slice
    elif action == "delete":
        payload = message.value["message"]
        force = message.value["force"]
        sliceUtils.delete_slice(slice_id=payload, force=force)
