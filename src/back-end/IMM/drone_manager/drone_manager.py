from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
#from IMM.drone_manager.route import Route
from IMM.drone_manager.link import Link
from IMM.drone_manager.mission import Mission
from IMM.drone_manager.dm_config import WAIT_TIME, MIN_CHARGE_LEVEL, FULL_CHARGE_LEVEL
import time
import threading
import queue


LOGGER_NAME = "drone_manager"
_logger = create_logger(LOGGER_NAME)
_drone_logger = create_logger(LOGGER_NAME + "_drones", custom_file_name="drone_log.log")

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
        self.drone_route_dict = {} # dictionary of drone -> route
        self.mode = "AUTO"

        self.link = None

        self.drone_data_lock = threading.Lock()
        self.update_received_event = threading.Event()
        self.event_queue = queue.Queue()
        self.status_thread = None
        

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

        self.status_thread = threading.Thread(target=self.status_printer, daemon=True)
        self.status_thread.start()

        # get drones from CRM, wait until non-zero number of drones
        while True:
            self.drones = self.get_drones()
            if self.drones:
                _logger.info("received drones from RDS")
                break
            time.sleep(WAIT_TIME)

        # wait until routes have been received, which happens after area is set by user
        while not self.drone_route_dict:
            time.sleep(WAIT_TIME)
        
        _logger.info("received routes from pathfinding")


        while self.running:
            self.resource_management()
            self.assign_missions()

            for drone in self.drones:
                _drone_logger.debug(drone)
            time.sleep(WAIT_TIME)


    def set_routes(self, drone_route_dict):
        """
        Set the routes that shall be used to execute AUTO mode. The Drone Manager will assign drones
        to fly these routes continuously. Currently assumes we always have 
        enough drones to fly these routes.

        This function is called by the IMM when the area is set and route planning has been completed.
        """
        if not isinstance(drone_route_dict, dict) or not drone_route_dict:
            return False

        # Reset drone routes and status
        for drone in self.drones:
            with self.drone_data_lock:
                drone.route = None
                if drone.status == "flying":
                    drone.status = "waiting"

        routes = [drone_route_dict[drone] for drone in drone_route_dict]
        _logger.info(f"Drone manager received routes: {routes}")
        return True
        

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
        if self.update_received_event.is_set():
            update = self.event_queue.get()
            self.update_received_event.clear()
            if update['update'] == 'lost_drone':
                drone = self.get_matching_drone(update['drone'])
                if drone:
                    self.drones.remove(drone)
                # idk maybe gotta do some resource management here
            elif update['update'] == 'gained_drone':
                if self.link.connect_to_drone():
                    self.drones.append(Drone(id=update['drone']))
                # idk maybe gotta do some resource management here


        for d in self.drones:
            with self.drone_data_lock:
                if d.status != "charging" and self.link.get_drone_battery(d) < MIN_CHARGE_LEVEL:
                    if d.route:
                        d.route.drone = None
                    d.route = None
                    self.link.return_to_home(d)
        
        for d in self.drone_route_dict:
            # is there a drone that flies this route?
            # if drone.id == drone_id:
            #  drone.route = route
            # route.drone = route
            r = self.drone_route_dict[d]
            if not r.drone:
                with self.drone_data_lock:
                    battery_lvl = self.link.get_drone_battery(d)
                    drone_status = d.status
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
        for d in self.drone_route_dict:
            route = self.drone_route_dict[d]
            success = True
            with self.drone_data_lock:
                # TODO: see if route.drone can be replaced with d,
                # and if drone.route can be replaced with drone_route_dict[d]
                if route.drone and route.drone.status in ["landed", "waiting", "idle"]:
                    mission = self.create_mission(route.drone)
                    route.drone.current_mission = mission
                    success = self.link.fly(mission, route.drone)
        return success
        #TODO: Handle routes which could not get a mission


    def get_matching_drone(self, drone_id):
        for d in self.drones:
            if d.id == drone_id:
                return d
        return None
    

    def status_printer(self):
        ''''Receives update msgs from link and updates the drone managers resources to reflect the changes'''
        alive = True
        while alive:
            try:
                msg = self.link.msg_queue.get()
                _logger.info(f'got status update: {msg}')
                if msg is None:
                    continue
                
                data = msg['data']

                if msg['topic'] == 'drone_status':
                    _logger.info(f'Received drone_status update with the data being: {data}')
                    if data['drone_status'] == 'waiting':
                        with self.drone_data_lock:
                            drone = self.get_matching_drone(data['drone'])
                            if drone:
                                drone.status = data['drone_status']
                        _logger.info('mission done')
                    elif data['drone_status'] == 'idle':
                        with self.drone_data_lock:
                            drone = self.get_matching_drone(data['drone'])
                            if drone:
                                drone.status = data['drone_status']
                        _logger.info('idling')
                    elif data['drone_status'] == 'charging':
                        with self.drone_data_lock:
                            drone = self.get_matching_drone(data['drone'])
                            if drone:
                                drone.status = data['drone_status']
                        _logger.info('charging battery')
                    elif data['drone_status'] == 'flying':
                        with self.drone_data_lock:
                            drone = self.get_matching_drone(data['drone'])
                            if drone:
                                drone.status = data['drone_status']
                        _logger.info('flying mission')
                    elif data['drone_status'] == 'returning':
                        with self.drone_data_lock:
                            drone = self.get_matching_drone(data['drone'])
                            if drone:
                                drone.status = data['drone_status']
                        _logger.info('returning to home')

                elif msg['topic'] == 'drone_position':
                    with self.drone_data_lock:
                        drone = self.get_matching_drone(data['drone'])
                        if drone:
                            drone.lat = data['lat']
                            drone.lon = data['lon']
                            drone.alt = data['alt']

                elif msg['topic'] == 'lost_drone':
                    _logger.info(f'topic is lost_drone, trying to get data')
                    _logger.info(f'Received drone status update with the data being: {data}')
                    self.event_queue.put({'drone':data['drone'], 'update':'lost_drone'})
                    self.update_received_event.set()

                elif msg['topic'] == 'gained_drone':
                    _logger.info(f'topic is new_drone, trying to get data')
                    _logger.info(f'Received drone status update with the data being: {data}')
                    self.event_queue.put({'drone':data['drone'], 'update':'gained_drone'})
                    self.update_received_event.set()

                while self.update_received_event.is_set():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                alive = False
            except Exception as e:
                _logger.warning(f'exception occurred in status printer {e}')
                pass
                    
    
    def set_mode(self, mode):
        """ 
        Sets the current mode.
        
        keyword arguments:
          mode - "AUTO" or "MAN"
        """
        self.mode = mode
