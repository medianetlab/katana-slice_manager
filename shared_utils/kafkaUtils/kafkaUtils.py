from kafka import KafkaProducer, KafkaAdminClient, admin, errors
import time
import logging
import json

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

producer, topic = None, None


def create_producer():
    global producer, topic

    if not producer or not topic:
        # Create the kafka producer
        tries = 3
        exit = False
        while not exit:
            try:
                logger.debug("New producer")
                producer = KafkaProducer(
                    bootstrap_servers=["kafka:19092"],
                    value_serializer=lambda m: json.dumps(m).encode('ascii'))
            except errors.NoBrokersAvailable as KafkaError:
                if tries > 0:
                    tries -= 1
                    time.sleep(5)
                else:
                    logger.error(KafkaError)
            else:
                exit = True
                tries = 3

        # Create the Kafka topic
        try:
            topic = admin.NewTopic(name="slice", num_partitions=1,
                                   replication_factor=1)
            broker = KafkaAdminClient(bootstrap_servers="kafka:19092")
            broker.create_topics([topic])
        except errors.TopicAlreadyExistsError:
            logger.warning("Topic exists already")

    return producer, topic
