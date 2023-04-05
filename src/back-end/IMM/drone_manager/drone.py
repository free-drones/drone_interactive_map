from IMM.drone_manager.node import Node


class Drone():
    
    def __init__(self, id, mode="AUTO"):
        self.id = id # Drone "name/id" to identify drones in Link class
        self.mode = mode
        self.route = None

        self.current_mission = None
        self.secondary_route = None # Used for photo routes, "side missions" if you will
        

    def get_next_point(self):
        if self.secondary_route:
            return self.secondary_route.get_next_node()
        return self.route.get_next_node()


    

        # if not self.next_point:
        #     self.next_point = self.route.get_next_node()
        
        # is_node = isinstance(self.next_point, Node)
        # self.route.update_route(reuse_node=is_node)
        
        # return self.next_point
