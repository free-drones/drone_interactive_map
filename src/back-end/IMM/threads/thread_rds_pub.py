"""This file contains the thread that is used for sending request to the RDS.
This thread will not send requests automatically.
The thread should be started trough the thread_handler.py.
"""

import time
from config_file import context, zmq
from config_file import RDS_req_socket_url, RDS_pub_socket_url
from threading import Thread, Event
from utility.helper_functions import create_logger

LOGGER_NAME = "thread_rds_pub"
_logger = create_logger(LOGGER_NAME)

class RDSPubThread(Thread):
    """Regularly fetches information from the RDS and processes client requests"""
    def __init__(self, thread_handler):
        """Initiates the thread

        Keyword arguments:
        thread_handler -- The class ThreadHandler, can be found in
                          thread_handler.py
        """
        super().__init__()
        _logger.info("Connecting to RDS...")
        self.RDS_info_socket = context.socket(zmq.REQ)
        self.RDS_poi_socket = context.socket(zmq.REQ)
        self.RDS_info_socket.connect(RDS_req_socket_url)
        self.RDS_poi_socket.connect(RDS_pub_socket_url)
        _logger.info("Connection to RDS established.")
        self.thread_handler = thread_handler
        self.requests_available = Event()
        self.request_queue = []
        self.running = True

    def run(self):
        """Handles request if there are some in the request queue."""
        while self.running:
            self.requests_available.wait()
            request = self.request_queue.pop(0)

            if request["fcn"] == "add_poi":
                self.__send_on_poi_link(request)
            elif request["fcn"] != "stop":
                self.__send_on_info_link(request)

            if len(self.request_queue) == 0:
                self.requests_available.clear()


    def add_request(self, request):
        """Adds a new request for the thread to handle.
        This function should always be called when you want to send a new request.

        Keyword arguments:
        request -- A json containing the request.
        """

        self.request_queue.append(request)
        self.requests_available.set()

    def __send_on_poi_link(self, request):
        """Sends a request on the poi link to the RDS.
        Should not be called outside this thread.

        Keyword arguments:
        request -- A json containing the request.
        """
        _logger.debug(f"Sending request on poi link: {request}")
        self.RDS_poi_socket.send_json(request)
        resp = self.RDS_poi_socket.recv_json()
        _logger.debug(f"Received poi link response: {resp}")

    def __send_on_info_link(self, request):
        """Sends a request on the info link to the RDS.
        Should not be called outside this thread.

        Keyword arguments:
        request -- A json containing the request.
        """
        _logger.debug(f"Sending request on the info link: {request}")
        self.RDS_info_socket.send_json(request)
        resp = self.RDS_info_socket.recv_json()
        _logger.debug(f"Received info link reponse: {resp}")

    def quit(self):
        """Sends a QUIT request to RDS"""
        request = {"fcn":"quit", "arg": ""}
        _logger.debug(f"Sending quit request: {request}")
        self.RDS_info_socket.send_json(request)
        resp = self.RDS_info_socket.recv_json()  # What to do?
        _logger.debug(f"Received response to quit request: {resp}")

    def stop(self):
        """Stops the thread. Used for debugging.
        Should always be called trough thread_handler.py.
        """

        request = {
            "fcn": "stop"
        }
        self.RDS_poi_socket.send_json(request)
        resp_pub = self.RDS_poi_socket.recv_json()
        self.RDS_info_socket.send_json(request)
        resp_req = self.RDS_info_socket.recv_json()
        self.running = False
        self.add_request({"fcn": "stop"})
        self.requests_available.set()
