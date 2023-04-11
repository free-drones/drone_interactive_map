class Link():
    # TODO: handle connection errors appropriately, both on initial connection and if it drops after a while
    def __init__(self):
        self.link = None
    
    def fly(self, mission, drone):
        # convert mission from Mission to json representation
        mission_dict = mission.as_mission_dict()
        drone_name = drone.id
        return None
    
    def get_drone_status(self, drone):
        return None
    
    def get_drone_position(self, drone):
        return None
    
    def get_drone_battery(self, drone):
        return 100
    
    def get_drone_waypoint(self, drone):
        return None
    
    def return_to_home(self, drone):
        return None
    
    def fly_random_mission(self, drone):
        pass

    def get_list_of_drones(self):
        return []
    