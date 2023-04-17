from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.link import Link as LinkDummy
from IMM.drone_manager.link_dummy import Link
from IMM.drone_manager.mission import Mission

import time


WAIT_TIME = 1
MIN_CHARGE_LEVEL = 20
FULL_CHARGE_LEVEL = 95
LOGGER_NAME = "drone_manager"
_logger = create_logger(LOGGER_NAME)

class DroneManager(Thread):
    def __init__(self, mockup_link = False):
        """
        Initiates the thread.

        keyword arguments:
            -
        """

        super().__init__()
        self.running = True
        self.drones = []
        self.routes = []

        self.link = None
        self.use_dummy_link = mockup_link

    def connect(self):
        if self.use_dummy_link:
            self.link = LinkDummy()
        self.link = Link()
        self.link.connect_to_all_drones()

    def run(self):
        """ where the thread runs """

        # get drones from CRM, wait until non-zero number of drones
        while True:
            self.drones = self.get_crm_drones()
            if self.drones:
                _logger.info("received drones from CRM")
                break
            time.sleep(WAIT_TIME)

        # wait until routes have been received, which happens after area is set by user
        while not self.routes:
            time.sleep(WAIT_TIME)
        
        _logger.info("received routes from pathfinding")

        while self.running:
            self.resource_management()
            self.assign_missions()

            time.sleep(WAIT_TIME)


    def set_routes(self, route_list):
        self.routes = route_list

    def get_crm_drones(self):
        drones = [Drone(id=dname) for dname in self.link.get_list_of_drones()]
        return drones

    def stop(self):
        self.running = False

    def get_drone_count(self):
        return len(self.drones)
    
    def create_mission(self, drone):
        return Mission(drone.route)

    def resource_management(self):
        """ Handles assigning drones based on battery and mission status to routes. Drones are sent to charge when needed. """

        for d in self.drones:
            if self.link.get_drone_status(d) != "charging" and self.link.get_drone_battery(d) < MIN_CHARGE_LEVEL:
                if d.route:
                    d.route.drone = None
                d.route = None
                self.link.return_to_home(d)
        
        for r in self.routes:
            # is there a drone that flies this route?
            if not r.drone:
                for d in self.drones:
                    battery_lvl = self.link.get_drone_battery(d)
                    drone_status = self.link.get_drone_status(d)
                    if not d.route and battery_lvl >= FULL_CHARGE_LEVEL and drone_status in ["landed", "waiting", "idle"]:
                        d.route = r
                        r.drone = d
                        break
                # If no available drone is found, there are too many routes currently and resegmentation shall occur
                if not r.drone:
                    # area segmentation with # of drones that are "available" – what does that mean? etc
                    pass
            

    def assign_missions(self):
        """ Creates missions and executes them for each drone that have a route to fly """
        for route in self.routes:
            success = True
            if self.link.get_drone_status(route.drone) in ["landed", "waiting", "idle"]:
                mission = self.create_mission(route.drone)
                route.drone.current_mission = mission
                success = self.link.fly(mission, route.drone)
        return success
        #TODO: Handle routes which could not get a mission
                
    
    def set_mode(self, mode):
        self.mode = mode
