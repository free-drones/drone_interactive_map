
class Drone():
    
    def __init__(self, id, link, mode="AUTO"):
        self.id = id
        self.link = link
        self.mode = mode
        self.route = None
        self.next_point = None
        self.current_mission = None
    
    def get_status(input = -1):
        return input
    
    def execute_mission(self):
        # communicate through self.link to send(?) mission to CRM and execute it