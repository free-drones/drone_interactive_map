from rise_drones.src.app import app_single_drone_attempt
import dss
import dss.auxiliaries
import dss.client
import time
import threading

class Link():
    '''This class is used to connect to drones and send missions to them'''
    def __init__(self):
        self.drone_dict = {}

        self.ip = dss.auxiliary.zmq.get_ip() #auto ip for now
        self.crm = '10.44.170.10:17700' #crm ip and port

    def connect_to_drone(self):
        '''Creates a new drone object and adds it to the drone dictionary'''
        drone_name = "drone"+ str(len(self.drone_dict))
        new_drone = app_single_drone_attempt.Drone(self.ip, drone_name, self.crm)
        if new_drone.drone_connected:
            self.drone_dict[drone_name] = new_drone
            return True
        else:
            new_drone.kill()
            return False
    
    def get_list_of_drones(self):
        '''Returns a list of all drones'''
        return self.drone_dict.keys()
    
    def kill(self):
        '''Kills all drones and clears the drone dictionary'''
        for drone in self.drone_dict.values():
            drone.kill()
        self.drone_dict = {}

    def fly(self, mission, drone_name):
        '''Takes a mission and a drone name and sends the mission to the drone'''
        self.drone_dict[drone_name].fly_mission(mission)
    
    def fly_random_mission(self, drone_name):
        '''Takes a drone name and sends a random mission to the drone'''
        self.drone_dict[drone_name].fly_random_mission()

    def get_mission_status(self, drone_name):
        '''Returns the status of the mission'''
        return self.drone_dict[drone_name].mission_status
    
    def return_to_home(self, drone_name):
        '''Returns the drone to its launch location'''
        self.drone_dict[drone_name].return_to_home()
    
    def get_drone_state(self, drone_name):
        '''Returns the current state of the drone in the form of a dictionary {Lat: Decimal degrees , Lon: Decimal degrees , Alt: AMSL , Heading: degrees relative true north}'''
        return self.drone_dict[drone_name].get_drone_location()
    
    def get_drone_waypoint(self, drone_name):
        '''Returns the current waypoint of the drone'''
        return self.drone_dict[drone_name].get_current_waypoint()