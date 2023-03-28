from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.route import Route

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
        self.drones = []
        self.routes = []
        self.manual_route = Route()
        self.photo_queue = []

    def run(self):
        """ where the thread runs """

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
    
    def create_mission(self, drone):
        drone.current_mission = Mission(drone.next_point)
        return Mission(drone.next_point)


    def resource_management(self):
        pass
        #If photo req:
            #Assign drone to complete it

        #if self.mode == "MAN":
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
                    d.current_mission = self.create_mission(d)
                    d.execute_mission()
            #Handle MAN mode drones
            if d.mode == "MAN":
                pass
                #Update route after current map position
            if d.mode == "PHOTO":
                
                d.next_point = self.view_to_nodes(photo_view)
                d.current_mission = self.create_mission(d)

    
    def set_mode(self, mode):
        self.mode = mode

    # Receives a manual-mode view from the main IMM thread and modifies the
    # manual route according to the view.
    # arguments:
    # view –
    # {
    #     "up_left" : coord,
    #     "up_right" : coord,
    #     "down_left" : coord,
    #     "down_right" : coord,
    #     "center" : coord,
    # }
    # where coord is a dictionary on the form of:
    # { "lat": double, "long", double }
    def receive_manual_view(self, view):
        if self.mode == "MAN":
            nodes = self.view_to_nodes(view)
            self.manual_route.add_nodes(nodes)
            
            # update route for the manual drone(s)
    
    def receive_photo_request(self, view):
        nodes = self.view_to_nodes(view)
        self.photo_queue.append(nodes)
        #self.manual_route.add_nodes(nodes)
        pass
    
    # currently just takes center point regardless of zoom level
    def view_to_nodes(coords):
        return [coords["center"]]
a

# temp
class Link():
    def __init__(self, link):
        self.link = link

class Mission():
    def __init__(self, points):
        self.points = points

