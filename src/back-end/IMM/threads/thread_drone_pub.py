"""This file contains the thread that is used for regularly collecting drone info data from the Drone Manager,
that is then sent to the frontend via the GUIPubThread.
The thread should be started trough the thread_handler.py.
"""

import time
from config_file import DRONE_INFO_INTERVAL
from threading import Thread
from utility.helper_functions import create_logger

LOGGER_NAME = "thread_drone_pub"
_logger = create_logger(LOGGER_NAME)

class DronePubThread(Thread):
    """
    Regularly uses information from the Drone Manager to package information that is sent to the 
    frontend (gets sent using GUI pub thread)
    """
    def __init__(self, thread_handler):
        """Initiates the thread

        Keyword arguments:
        thread_handler -- The class ThreadHandler, can be found in
                          thread_handler.py
        """
        super().__init__()
        self.thread_handler = thread_handler
        self.running = True

    def run(self):
        """ Regularly sends drone info to frontend via the gui pub thread """
        while self.running:
            drones = self.__get_drones_info()
            args = {"drones" : drones}
            request = {"fcn": "new_drones", "arg": args}
            self.thread_handler.get_gui_pub_thread().add_request(request)

            time.sleep(DRONE_INFO_INTERVAL)

    def __get_drones_info(self):
        """ 
        Return a dictionary containing information for all drones, on the following form:
        {
            'drone1' : drone_data,
            'drone2' : drone_data,
            ...
        }
        where drone_data is the data for each drone returned by the function __get_drone_info()

        
        """
        drones_data = {}
        with self.thread_handler.get_drone_manager_thread().drone_data_lock:
                drones = self.thread_handler.get_drone_manager_thread().drones
                if not drones:
                    _logger.info(f"Could not retrieve drones from drone manager")
                    return drones_data
                
                for drone in drones:
                    _logger.debug(drone)
                    if self.__has_valid_drone_data(drone):
                        drone_data = self.__get_drone_info(drone)
                        drones_data[drone_data['drone_id']] = drone_data
                    else:
                        _logger.info(f"Drone {drone.id} has invalid data and could not be included in drone info")

        return drones_data
    
    def __has_valid_drone_data(self, drone):
        """ Return true if the given drone has non-None data """
        return drone.id is not None and drone.lat and drone.lon and drone.mode in ["AUTO", "MAN", "PHOTO"]

    def __get_drone_info(self, drone):
        """ 
        Return a dictionary containing information for one drone on the following form:
        {
            'drone_id' : 'drone1',
            'location' : {
                'lat' : 59.123,
                'long' : 18.123
            },
            'mode' : 'AUTO'
        }
        """
        drone_data = {}
        drone_data["drone_id"] = drone.id
        drone_data["location"] = {}
        drone_data["location"]["lat"] = drone.lat
        drone_data["location"]["long"] = drone.lon
        drone_data["mode"] = drone.mode
        return drone_data

    def stop(self):
        """Stops the thread. Used for debugging.
        Should always be called trough thread_handler.py.
        """

        self.running = False
