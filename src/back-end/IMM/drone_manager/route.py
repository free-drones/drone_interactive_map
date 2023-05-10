import math
from IMM.drone_manager.node import Node

class Route:
    """
    Class representing a route that drones fly along. A route consists of nodes. 
    Each route gets assigned a drone which will fly to each of the nodes in order.
    """
    
    def __init__(self, nodes, as_dicts = False):
        if as_dicts:
            self.nodes = [Node(lat=node['lat'], lon=node['lon']) for node in nodes]
        else:
            self.nodes = nodes
        
        self.drone = None
    
        
    def __repr__(self):
        output = "\n"
        for node in self.nodes:
            output += f"{node}\n"
        return output
