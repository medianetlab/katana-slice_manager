import threading
import logging
import pickle

from katana.utils.mongoUtils import mongoUtils

# Create the logger
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


class MonThread(object):
    """
    Class that implements a per Network Service thread for monitoring purposes
    """

    def __init__(self, ns, ns_status):
        self.ns = ns
        self.ns_status = ns_status
        # Create the stop parameter
        self._stop = threading.Event()

    def run(self):
        """
        The function that will run to check the NS status
        """
        while not self.stopped:
            target_nfvo_obj = pickle.loads(
                mongoUtils.find("nfvo_obj", {"id": self.ns["nfvo-id"]})["obj"]
            )
            insr = target_nfvo_obj.getNsr(self.ns["nfvo_inst_ns_id"])
            if not insr or insr["operational-status"] != "running":
                self.ns_status.set(0)
            self._stop.wait(timeout=30)

    def stopped(self):
        """
        Checks if the thread has stopped
        """
        return self._stop.is_set()

    def stop(self):
        """
        Stops the thread
        """
        self._stop.set()
