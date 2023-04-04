from IMM.drone_manager.node import Node


class Drone():
    
    def __init__(self, id, mode="AUTO"):
        self.id = id
        self.mode = mode
        self.route = None
        self.next_point = None
        self.current_mission = None
    
    def get_status(self, input = -1): #TODO Make it dss status
        return input
    
    def execute_mission(self):
        pass
        # communicate through self.link to send(?) mission to CRM and execute it

    def get_next_point(self):
        # If we do not have a photo request mission
        if not self.next_point:
            self.next_point = self.route.get_next_node()
        
        is_node = isinstance(self.next_point, Node)
        self.route.update_route(reuse_node=is_node)
        
        
        return self.next_point
