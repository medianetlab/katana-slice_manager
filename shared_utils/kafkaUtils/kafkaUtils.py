from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient, admin, errors
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

# NOTE: It is required to have global parameters for kafka objects
consumer, producer, topic = None, None, None


def create_consumer():
    global consumer

    # Create the kafka consumer
    tries = 3
    exit = False
    while not exit:
        try:
            consumer = KafkaConsumer(
                'slice',
                bootstrap_servers=['kafka:19092'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=10000,
                group_id='katana-mngr-group',
                value_deserializer=lambda m: json.loads(m.decode('ascii')))
        except errors.NoBrokersAvailable as KafkaError:
            if tries > 0:
                tries -= 1
                logger.warning("Kafka not ready yet. Tries remaining: {0}".
                               format(tries))
                time.sleep(5)
            else:
                logger.error(KafkaError)
        else:
            logger.info("New consumer")
            exit = True
            tries = 3
    return consumer


def create_producer():
    global producer

    # Create the kafka producer
    tries = 3
    exit = False
    while not exit:
        try:
            producer = KafkaProducer(
                bootstrap_servers=["kafka:19092"],
                value_serializer=lambda m: json.dumps(m).encode('ascii'))
        except errors.NoBrokersAvailable as KafkaError:
            if tries > 0:
                tries -= 1
                logger.warning("Kafka not ready yet. Tries remaining: {0}".
                               format(tries))
                time.sleep(5)
            else:
                logger.error(KafkaError)
        else:
            logger.info("New producer")
            exit = True
            tries = 3
    return producer


def create_topic():
    global topic

    # Create the kafka topic
    tries = 3
    exit = False
    while not exit:
        try:
            try:
                topic = admin.NewTopic(name="slice", num_partitions=1,
                                       replication_factor=1)
                broker = KafkaAdminClient(bootstrap_servers="kafka:19092")
                broker.create_topics([topic])
            except errors.TopicAlreadyExistsError:
                logger.warning("Topic exists already")
            else:
                logger.info("New topic")
        except errors.NoBrokersAvailable as KafkaError:
            if tries > 0:
                tries -= 1
                logger.warning("Kafka not ready yet. Tries remaining: {0}".
                               format(tries))
                time.sleep(5)
            else:
                logger.error(KafkaError)
        else:
            exit = True
            tries = 3
