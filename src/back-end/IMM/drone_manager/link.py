class Link():
    def __init__(self):
        self.link = None
    
    def fly(self, mission, drone_name):
        return None
    
    def get_mission_state(self, drone_name):
        return None #status
    
    def get_drone_position(self, drone_name):
        #In docs called state
        return None #position
    
    def get_drone_waypoint(self, drone_name):
        return None #waypoint
    
    def return_to_home(self, drone_name):
        return None
    
    def fly_random_mission(self, drone_name):
        pass

    def get_list_of_drones(self):
        return [] # [drone_name]    
    
    def connect(self):
        #Establish connection with 
        
        status=1
        return status