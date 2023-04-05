from IMM.drone_manager.route import Route
from IMM.drone_manager.node import Node

class Mission():
    def __init__(self, route):
        self.route = route

    def as_mission_dict(self):
        mission = []
        for node in self.route.nodes:
            mission.append(self.node_to_waypoint_dict(node))
        return mission
    
    def node_to_waypoint_dict(self, node):
        return {
            "lat": node.lat,
            "lon": node.lon,
            "alt": node.alt,
            "alt_type": "amsl",
            "heading": "course",
        }