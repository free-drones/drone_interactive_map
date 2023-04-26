from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.route import Route
from IMM.drone_manager.link import Link
from IMM.drone_manager.mission import Mission
from IMM.drone_manager.dm_config import WAIT_TIME, MIN_CHARGE_LEVEL, FULL_CHARGE_LEVEL
import time


LOGGER_NAME = "drone_manager"
_logger = create_logger(LOGGER_NAME)

class DroneManager(Thread):
    """
    Manages drones with RISE Drone System.

    Keeps count and manages all active drones and routes in the current session.
    Reassigns drones and creates mission for all drones as needed in AUTO mode. 
    """

    def __init__(self):
        """
        Initiates the thread.
        """

        super().__init__()
        self.running = True
        self.drones = []
        self.routes = []
        self.mode = "AUTO"

        self.link = None

    def connect(self):
        """
        Creates a connection to RDS and attempts to connect to as many drones as possible.
        Note that drones must be connected to before trying to actually retrieve them, which happens
        later.
        """
        self.link = Link()
        self.link.connect_to_all_drones()

    def run(self, connect_to_RDS = True):
        """ where the thread runs """

        if connect_to_RDS:
            self.connect()

        # get drones from RDS, wait until non-zero number of drones
        while True:
            self.drones = self.get_drones()
            if self.drones:
                _logger.info("received drones from RDS")
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
        """
        Set the routes that shall be used to execute AUTO mode. The Drone Manager will assign drones
        to fly these routes continuously. Currently assumes we always have 
        enough drones to fly these routes.

        This function is called by the IMM when the area is set and route planning has been completed.
        """
        if not isinstance(route_list, list) or not route_list:
            return False
        if isinstance(route_list[0], list):
            self.routes = [Route(route, as_dicts=True) for route in route_list]
            _logger.info(f"Drone manager received routes: {self.routes}")
            return True
        elif isinstance(route_list[0], Route):
            self.routes = route_list
            _logger.info(f"Drone manager received routes: {self.routes}")
            return True
        return False

    def get_drones(self):
        """
        Returns a list of Drone objects for all connected drones in RISE Drone System
        """
        drones = [Drone(id=dname) for dname in self.link.get_list_of_drones()]
        return drones

    def stop(self):
        """
        Stops the thread. Used by the thread_handler to stop the thread
        """
        self.running = False

    def get_drone_count(self):
        """
        Return the number of currently connected drones
        """
        return len(self.drones)
    
    def create_mission(self, drone):
        """
        Return a mission that flies according to the given drone's current route
        """
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
        """ 
        Sets the current mode.
        
        keyword arguments:
          mode - "AUTO" or "MAN"
        """
        self.mode = mode
