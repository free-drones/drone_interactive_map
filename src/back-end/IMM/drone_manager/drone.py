from IMM.drone_manager.node import Node


class Drone():
    
    def __init__(self, id, mode="AUTO", status="idle"):
        self.id = id # Drone "name/id" to identify drones in Link class
        self.mode = mode
        self.route = None
        self.current_mission = None

        # The following properties need to be thread-safe and therefore need to be protected by a lock when accessed or changed
        self.status = status
        self.lat = None
        self.lon = None
        self.alt = None
    
    def __repr__(self):
        return f"Drone(id={self.id}, mode={self.mode}, status={self.status}, pos=({self.lat}, {self.lon}), alt={self.alt}, has route={bool(self.route)})"