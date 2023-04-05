from rise_drones.src.app import app_single_drone_attempt
import dss
import dss.auxiliaries
import dss.client
import time
import threading
#TODO: Get more logging and error handling in place
#TODO: See to it that everything is thread safe
#TODO: check what the nack msg is for the dss
#TODO: See if we can fly multiple missions in a row
#TODO: Figure out a way to overwrite a mission
#TODO: Clean up the code
#TODO: Cover any areas where the code might break, or that we have not implemented yet
#TODO: Figure out which threads need to be daemon threads and which don't, make sure all threads are exited properly
#TODO: Why is the next drone only taking off after the first drone reaches 15m?

class Link():
    '''This class is used to connect to drones and send missions to them'''
    def __init__(self):
        self.drone_dict = {}

        self.ip = dss.auxiliaries.zmq.get_ip()                                       # auto ip for now
        self.crm = '10.44.170.10:17700'                                              # crm ip and port

    def connect_to_drone(self):
        '''Creates a new drone object and adds it to the drone dictionary'''
        drone_name = "drone"+ str(len(self.drone_dict))
        new_drone = app_single_drone_attempt.Drone(self.ip, drone_name, self.crm)
        if new_drone.drone_connected:
            self.drone_dict[drone_name] = new_drone
            return True
        else:
            new_drone.kill()                                                         # kill any threads that were created
            return False
    
    def get_list_of_drones(self):
        '''Returns a list of all drones'''
        return self.drone_dict.keys()
    
    def kill(self):
        '''Kills all drones and clears the drone dictionary'''
        if not self.drone_dict == {}:
            for drone in self.drone_dict.values():
                drone.kill()
        self.drone_dict = {}

    def fly(self, mission, drone_name):
        '''Starts a new thread that flies the specified mission with the specified drone'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        if self.drone_dict[drone_name].validate_mission(mission):
            with self.drone_dict[drone_name].mission_status_lock:
                self.drone_dict[drone_name].mission_status = 'flying'
            self.drone_dict[drone_name].stop_threads.set()                         # stop the current mission
            time.sleep(3)
            self.drone_dict[drone_name].stop_threads.clear()                       # allows for next mission to be flown
            fly_thread = threading.Thread(self.drone_dict[drone_name].fly_mission(mission), daemon=True)
            fly_thread.start()
        else:
            raise Exception('Mission denied: invalid mission')
    
    def fly_random_mission(self, drone_name):
        '''Starts a new thread that flies a random mission with the specified drone'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        with self.drone_dict[drone_name].mission_status_lock:
            self.drone_dict[drone_name].mission_status = 'flying'
        self.drone_dict[drone_name].stop_threads.set()                         # stop the current mission
        time.sleep(3)
        self.drone_dict[drone_name].stop_threads.clear()                       # allows for next mission to be flown
        fly_thread = threading.Thread(self.drone_dict[drone_name].fly_random_mission(), daemon=True)
        fly_thread.start()

    def get_mission_status(self, drone_name):
        '''Returns the status of the mission, 'flying' = mission is in progress, 'waiting' = flying and waiting for a new mission, 
        'idle' = not flying and idle, 'landed' = on the ground, 'denied' = mission was denied'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        with self.drone_dict[drone_name].mission_status_lock:
            return self.drone_dict[drone_name].mission_status
    
    def return_to_home(self, drone_name):
        '''Returns the drone to its launch location'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        with self.drone_dict[drone_name].mission_status_lock:
            self.drone_dict[drone_name].mission_status = 'flying'
        self.drone_dict[drone_name].stop_threads.set()                         # stop the current mission
        time.sleep(1)
        self.drone_dict[drone_name].stop_threads.clear()                       # allows for next mission to be flown
        home_thread = threading.Thread(self.drone_dict[drone_name].return_to_home(), daemon=True)
        home_thread.start()
    
    def get_drone_position(self, drone_name):
        '''Returns the current state of the drone in the form of a dictionary {Lat: Decimal degrees , Lon: Decimal degrees , Alt: AMSL , Heading: degrees relative true north}'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        return self.drone_dict[drone_name].get_drone_location()

    def get_drone_waypoint(self, drone_name):
        '''Returns the current waypoint of the drone'''
        if not self.valid_drone_name(drone_name):
            raise KeyError('Invalid drone name')
        return self.drone_dict[drone_name].get_current_waypoint()
    
    def valid_drone_name(self, drone_name):
        '''Returns true if the drone name is valid'''
        if drone_name in self.drone_dict:
            return True
        else:
            return False