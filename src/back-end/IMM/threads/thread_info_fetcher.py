"""This file contains the thread that is used for regularly sending requests to
RDS. This thread automatically requests information and saves it to the database.
The thread should be started trough the thread_handler.py.
"""

import time
from threading import Thread

from config_file import context, zmq
from IMM.database.database import session_scope, Drone, PrioImage, func
from config_file import RDS_req_socket_url, UPDATE_INTERVAL
from utility.session_functions import get_session_id
from utility.helper_functions import check_keys_exists, create_logger

LOGGER_NAME = "thread_info_fetcher"
_logger = create_logger(LOGGER_NAME)

def save_info_to_db(drone_info, current_time):
    """Creates a drone instance if not exists and adds/updates values accordingly.

    Keyword arguments:
    drone_info -- A json containing info about drones.
    current_time -- An integer representing time in unixtime.
    """

    session_id = get_session_id()
    with session_scope() as session:
        for key, value in drone_info.items():
            if key not in ["fcn", "arg"]:
                drone = session.query(Drone).filter_by(id=value["drone-id"], session_id=session_id).first()
                if drone is None:
                    drone = Drone(id=value["drone-id"], session_id=session_id, last_updated=current_time,
                                  time2bingo=value["time2bingo"])

                drone.last_updated = current_time
                drone.time2bingo = value["time2bingo"]
                session.add(drone)


class InfoFetcherThread(Thread):
    """Regularly fetches information about drones from the RDS and updates the
    database.
    """
    def __init__(self):
        """Initates the thread"""
        super().__init__()
        _logger.info("Connecting to RDS...")
        self.RDS_info_socket = context.socket(zmq.REQ)
        self.RDS_info_socket.connect(RDS_req_socket_url)
        _logger.info("Connection to RDS established.")
        self.running = True
        self.last_updated = 0

    def run(self):
        while self.running:
            current_time = int(time.time())
            self.__get_info(current_time)
            self.__get_eta()
            self.last_updated = current_time
            time.sleep(UPDATE_INTERVAL)


    def __get_info(self, current_time):
        """Requests information about drones from the RDS and updates the
        database accordingly.
        Should not be called outside this thread.

        Keyword arguments:
        current_time -- An integer representing time in unixtime.
        """

        request = {
            "fcn": "get_info",
            "arg": "drone-info"
        }
        drone_info = self.__send_request(request)
        save_info_to_db(drone_info, current_time)

    def __get_eta(self):
        """Gets the current ETA from the RDS.
        Should not be called outside this thread.
        """

        request = {
            "fcn": "queue_ETA",
            "arg": ""
        }
        response = self.__send_request(request)

        with session_scope() as session:
            time_requested = session.query(func.min(PrioImage.time_requested)).first()[0]
            if time_requested is not None and check_keys_exists(response, ["arg2"]):
                next_eta_image = session.query(PrioImage).filter_by(time_requested=time_requested).first()
                if next_eta_image is not None:
                    next_eta_image.eta = int(response["arg2"])
                    session.add(next_eta_image)

    def __send_request(self, request):
        """Sends a request to the RDS connection.

        Keyword arguments:
        request -- The request JSON.

        Returns the RDS response.
        """
        _logger.debug(f"Sending request to RDS: {request}")
        self.RDS_info_socket.send_json(request)
        response = self.RDS_info_socket.recv_json()
        _logger.debug(f"Received response from RDS: {response}")
        return response

    def stop(self):
        """Stops the thread. Used for debugging.
        Should always be called trough thread_handler.py.
        """

        self.running = False
