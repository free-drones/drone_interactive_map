from threading import Thread
from utility.helper_functions import create_logger
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.route import Route
from IMM.drone_manager.link import Link
from IMM.drone_manager.node import Node

import time

PHOTO_NODE_WEIGHT = 3 #The higher the weight, the higher the priority on taking the photo => Drone will get there faster
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
        self.photo_queue = []  # queued photo requests, may be handled later
        self.photo_routes = []
        self.link = Link()
        self.link.connect()

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

    # return list of drone objects
    def get_crm_drones(self):
        drones = [Drone(id=dname) for dname in self.link.get_list_of_drones()]
        return drones

    def stop(self):
        self.running = False

    def get_drone_count(self):
        return len(self.drones)
    
    def create_mission(self, drone):
        drone.current_mission = Mission(drone.next_point)
        return Mission(drone.next_point)


    # Given photo requests, manual mode status, charge status for each drone, area change request, re-assign drones/routes
    def resource_management(self):
        pass

        #for r in routes
            #
        #if self.mode == "MAN":
            #Reassign routes/drones
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
                
                #d.next_point = self.view_to_nodes(photo_view)
                #d.current_mission = self.create_mission(d)
                
                
                pass

    
    def set_mode(self, mode):
        self.mode = mode

    # Receives a manual-mode view from the main IMM thread and modifies the
    # manual route according to the view.
    # arguments:
    # view –
    # { "up_left" : coord, "up_right" : coord, "down_left" : coord, "down_right" : coord, "center" : coord }
    # where coord is a dictionary on the form of:
    # { "lat": double, "long", double }
    def receive_manual_view(self, view):
        if self.mode == "MAN":
            self.manual_route = self.view_to_route(view)
    
    # Adds a photo request to queue to be handled later
    def receive_photo_request(self, view):
        self.photo_queue.append(view)
        # TODO: Add priority on photo request based on which client sent it (user prio)
        pass

    # Returns a route covering a photo request
    def route_from_photo_request(self, view):
        return self.view_to_route(view, weight=PHOTO_NODE_WEIGHT)
    
    # currently just takes center point regardless of zoom level
    def view_to_route(coords, weight=1):
        node = [Node(lat=coords["center"]["lat"], lon=coords["center"]["lon"], weight=weight)]
        return Route(nodes=[node])
    
    def update_routes(self): # TODO: maybe rename/move? Not sure what this actually should be called?
        if self.photo_queue:
            # We have photo request to handle
            
            next_photo_req = self.photo_queue.pop(0)
            photo_req_route = self.route_from_photo_request(next_photo_req)

            if next_photo_req["weight"] == 3: #3 is important picture, get it asap!

                closest_drone = min(self.drones, key=lambda d: self.link.get_drone_position(d.id))
                closest_drone.route.prepend(photo_req_route) # Note: add at index 1, not 0. 0 is the node we are currently moving to
                                                             # Subnote: is this really how it should be? Maybe we should cancel any mission and just go to photo place?!
                
            elif next_photo_req["weight"] == 2: #2 is important but not super prio, append it somewhere!
                pass
            elif next_photo_req["weight"] == 1: #1 is not important, be efficient and use closest route!
                
                photo_route_reference_node = photo_req_route.get_next_node() # picks one node as reference when determining closest route
                closest_route = min(self.routes, key=lambda r: r.distance_to(photo_route_reference_node))
                new_route = Route(closest_route)
                new_route.append(photo_req_route)
                photo_route = pathfinding(new_route)
            
                self.photo_routes.append(photo_route)

            pass


# Note:
# Pathfinding should handle cases where routes contain both nodes and routes. Should flatten any such routes and do pathfinding on *one* set of weighted nodes.

class Mission():
    def __init__(self, points):
        self.points = points

