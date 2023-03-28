from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone

import time

WAIT_TIME = 1
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
        #self.active_drones = []

    def run(self):
        """ ... """

        # get drones from CRM, wait until non-zero number of drones
        while not self.drones:
            self.drones = self.get_crm_drones()
            time.sleep(WAIT_TIME)
        
        while self.running:

            #Magic function that decides active drones and assigns route to each
            
            self.resource_management()

            self.assign_missions()


    def set_start_routes(self, route_list):
        self.routes = route_list

    # probably not how it is going to work
    def get_crm_drones(self):
        drones = []
        links = []  #get dss links properly from crm
        for dss_link in links:
            drones.append(Drone(link=Link(dss_link)))
        return drones

    def stop(self):
        self.running = False

    def get_drone_count(self):
        return len(self.drones)
    
    def create_mission(self):
        # TODO
        return None

    def resource_management(self):
        pass
        #If photo req:
            #Assign drone to complete it
        #If man req:
            #Reassign routes
        #If drone.status==Need to charge:
            #Reassign drones
        #If area changed? Or application closed?
            #STOP()
        #Else:
            #Continue

    def assign_missions(self):
        for d in self.drones:
            #Handle AUTO mode drones
            if d.mode == "AUTO":
                if d.mission.status == "done":
                    d.current_mission = self.create_mission(d.route.get_next_node())
                    d.execute_mission()
            #Handle MAN mode drones
            if d.mode == "MAN":
                pass
                #Update route after current map position
            if d.mode == "PHOTO":
                pass
                d.current_mission = self.create_mission(Photo_cords)

# temp
class Link():
    def __init__(self, link):
        self.link = link