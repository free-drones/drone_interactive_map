class Link():
    def __init__(self):
        self.link = None
    
    def fly(self, mission, drone):
        # convert mission from Mission to json representation
        mission_dict = mission.as_mission_dict()
        return None
    
    def get_mission_status(self, drone):
        return None #status
    
    def get_drone_status(self, drone):
        return {"battery":95} #
    
    def get_drone_waypoint(self, drone):
        return None #waypoint
    
    def return_to_home(self, drone):
        return None
    
    def fly_random_mission(self, drone):
        pass

    def get_list_of_drones(self):
        return [] # [drone_name]    
    
    def connect(self):
        #Establish connection with 
        
        status=1
        return status