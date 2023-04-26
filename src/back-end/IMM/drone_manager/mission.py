from IMM.drone_manager.dm_config import DRONE_SPEED

class Mission:
    """
    Class representing a mission that drones execute. A mission consists of a route.
    """

    def __init__(self, route):
        self.route = route

    def as_mission_dict(self):
        """
        Returns the mission in dictionary format compatible with RDS, where each
        waypoint ('id0' etc) is a dictionary with latitude, longitude and more. Example:
        {
            "id0": {
                "lat": 58.4035,
                "lon": 15.5745,
                "alt": 120,
                "alt_type": "amsl",
                "heading": "course",
                "speed": 5.0
            },
            "id1": {
                "lat": 58.4035,
                "lon": 15.5845,
                "alt": 120,
                "alt_type": "amsl",
                "heading": "course",
                "speed": 5.0
            }
        }
        """
        mission = {}
        for i, node in enumerate(self.route.nodes):
            mission[f"id{i}"] = self._node_to_waypoint_dict(node)
        return mission
    
    def _node_to_waypoint_dict(self, node):
        """
        Returns a Node as a waypoint in dictionary format compatible with RDS. See Mission.as_mission_dict()
        """
        return {
            "lat": node.lat,
            "lon": node.lon,
            "alt": node.alt,
            "alt_type": "amsl",
            "heading": "course",
            "speed": DRONE_SPEED
        }