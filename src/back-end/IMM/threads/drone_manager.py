from threading import Thread, Event
from utility.helper_functions import create_logger

import time

LOGGER_NAME = "thread_drone_manager"
_logger = create_logger(LOGGER_NAME)

class DroneManager(Thread):
    def __init__(self):
        """
        Initiates the thread.

        keyword arguments:
            -
        """

        super().__init__()
        self.running = True
        # _logger.debug("something")
        self.drones = []
        self.routes = []

    def run(self):
        """ ... """
        while self.running:
            self.get_crm_drones()
            if self.routes:
                pass
            
            # for i in range(drones/routes):
                # mission = create_mission(self.drones[i], self.routes[i]) 
                # execute_mission(drones[i])
        
            # Send out missions
            else:
                pass
                # self.routes = imm.route_planning.get_routes()
            

    def set_start_routes(self, route_list):
        self.routes = route_list

    def get_crm_drones():
        return 3
        pass
        #Retunera mängd drönare

    def stop(self):
        self.running = False