from IMM.drone_manager.node import Node


class Drone():
    
    def __init__(self, id, mode="AUTO"):
        self.id = id # Drone "name/id" to identify drones in Link class
        self.mode = mode
        self.route = None
        self.current_mission = None

        # The following properties need to be thread-safe and therefore need to be protected by a lock when accessed or changed
        self.status = "idle"
        self.lat = None
        self.lon = None
        self.alt = None