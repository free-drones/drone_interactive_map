from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.link import Link
from IMM.drone_manager.link_dummy import Link as LinkDummy
from IMM.drone_manager.mission import Mission
from IMM.drone_manager.dm_config import WAIT_TIME, MIN_CHARGE_LEVEL, FULL_CHARGE_LEVEL
import time


LOGGER_NAME = "drone_manager"
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
        self.drones = []
        self.routes = []

        self.link = None

    def connect(self):
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
                auto_drones = self.get_auto_drones() # adding for manual
                for d in auto_drones:
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
        
#---------------------------------MANUAL START--------------------------------------------

        if self.mode == "manual":
            route = self.get_manual_route()
            manual_drone = self.get_manual_drone()
            if not manual_drone:
                closest_drone = self.get_closest_auto_drone(self.get_manual_route())
                if closest_drone:
                    closest_drone.mode = "manual"
                    closest_drone.route = self.get_manual_route()
                    closest_drone.current_mission = self.create_mission(closest_drone.route)
            else:
                pos = self.link.get_drone_position(d)
                distance_to_goal = self.distance(self.get_coordinates_from_route(route), (pos[0],pos[1]))
                if distance_to_goal > ACCEPTABLE_DISTANCE: # This needs to be figured out, PLACEHOLDER
                    clostest_auto_drone, auto_drone_distance = self.get_closest_auto_drone(self.get_coordinates_from_route(route))
                    if auto_drone_distance < distance_to_goal:
                        manual_drone.mode = "auto"
                        manual_drone.route = None
                        manual_drone.current_mission = None
                        clostest_auto_drone.mode = "manual"
                        clostest_auto_drone.route = self.get_manual_route()
                        clostest_auto_drone.current_mission = self.create_mission(clostest_auto_drone.route)

    def get_coordinates_from_route(self, route):
        coordinates = (lat, lon) # This needs to be figured out, PLACEHOLDER
        return coordinates

    def get_manual_drone(self):
        for d in self.drones:
            if d.mode == "manual":
                return d
            else:
                return None
            
    def get_manual_route(self, drone):# This needs to be figured out, PLACEHOLDER
        return None
    
    def get_closest_auto_drone(self, coordinates):
        """ Returns the closest drone to the given coordinates"""
        drones = self.get_auto_drones()
        if drones:
            positions = {}
            for d in drones:
                pos = self.link.get_drone_position(d)
                positions[d]= (pos['lat'], pos['lon'])
            closest_drone, min_distance = min(((drone, self.distance(coordinates, positions[drone])) for drone in positions), key=lambda item: item[1])
            return closest_drone, min_distance
    
    def distance(self, coordinates1, coordinates2):
        """ Returns the distance between two coordinates"""
        lat1, lon1 = coordinates1
        lat2, lon2 = coordinates2

        # Convert latitude and longitude from degrees to radians
        rad_lat1, rad_lon1, rad_lat2, rad_lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Calculate the distance on a sphere using the Haversine formula
        lat_diff = rad_lat2 - rad_lat1
        lon_diff = rad_lon2 - rad_lon1
        x = math.sin(lat_diff/2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(lon_diff/2)**2
        sphere_dist = 2 * math.asin(math.sqrt(x))

        # Radius of Earth in kilometers
        R = 6371

        # Calculate the distance on the earth's surface
        distance = R * sphere_dist
        return distance
          
    def get_auto_drones(self):
        return [d for d in self.drones if d.mode == "auto"]
    
#---------------------------------MANUAL END --------------------------------------------

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
