from rise_drones.src.app import app_single_drone_attempt
import dss
import dss.auxiliaries
import dss.client
import time
import threading
import zmq
import json
#TODO: Get more logging and error handling in place
#TODO: See to it that everything is thread safe
#TODO: Cover any areas where the code might break, or that we have not implemented yet
#TODO: Figure out which threads need to be daemon threads and which don't, make sure all threads are exited properly
#TODO: Why is the next drone only taking off after the first drone reaches 15m? slow i think
_context = zmq.Context()

class Socket():
    def __init__(self):
        self.socket = _context.socket(zmq.REQ)
        self.socket.connect('tcp://10.44.170.10:17728') # Replace this port with the actual port number
    
    def send_and_recieve(self, data, fcn = None) -> dict:
        '''Sends a message to the drone_application and returns the reply'''
        try:
            print(f"sending message: {data}")
            msg = data
            #msg = {'fcn': fcn}
           # msg.update(data)
            msg_str = json.dumps(msg)
            self.socket.send_json(msg_str)
        except zmq.ZMQError as e:
            print(f"Error sending message: {e}")
            return None

        try:
            print("waiting for reply")
            reply = self.socket.recv_json()
            reply = json.loads(reply)
        except zmq.Again as e:
            print(f"Error receiving message (timeout): {e}")
            return None
        except zmq.ZMQError as e:
            print(f"Error receiving message: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding received JSON message: {e}")
            return None
        print(f"received reply: {reply}")
        return reply
    
    def request_success(self, reply):
        if reply['status'] == 'success':
            return True
        else:
            return False

    def close(self):
        self.socket.close()      


class LinkRange():
    '''This class is used to connect to drones and send missions to them'''
    def __init__(self):
        self.drone_dict = {}

        self.ip = dss.auxiliaries.zmq.get_ip()                                       # auto ip for now
        print(self.ip)
        self.crm = '10.44.170.10:17700'                                              # crm ip and port
        self.socket = Socket()
                                           

    def connect_to_drone(self):
        '''Creates a new drone object and adds it to the drone dictionary'''
        msg = {'fcn':'connect_to_drone'}
        print("sending connect_to_drone message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for connect_to_drone")
            return True
        else:
            print("request failed for connect_to_drone")
            return False
    
    def get_list_of_drones(self):
        '''Returns a list of all drones'''
        msg = {'fcn': 'get_list_of_drones'}
        print("sending get_list_of_drones message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for get_list_of_drones")
            print(reply['drone_list'])
            return reply['drone_list']
        else:
            print("request failed for get_list_of_drones")
            print(reply['message'])
            return False
    
    def kill(self): #currently obsolete in the new version
        '''Kills all drones and clears the drone dictionary'''
        print("killing socket")
        self.socket.close()

    def fly(self, mission, drone_name):
        '''Starts a new thread that flies the specified mission with the specified drone'''
        msg = {'fcn': 'fly', 'mission': mission, 'drone_name': drone_name}
        print("sending fly message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            return True
        else:
            print(reply['message'])
            return False
        
    
    def fly_random_mission(self, drone_name):
        '''Starts a new thread that flies a random mission with the specified drone'''
        msg = {'fcn': 'fly_random_mission', 'drone_name': drone_name}
        print("sending fly_random_mission message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for fly_random_mission")
            return True
        else:
            print("request failed for fly_random_mission")
            print(reply['message'])
            return False

    def get_mission_status(self, drone_name):
        '''Returns the status of the mission, 'flying' = mission is in progress, 'waiting' = flying and waiting for a new mission, 
        'idle' = not flying and idle, 'landed' = on the ground, 'denied' = mission was denied'''
        msg = {'fcn': 'get_mission_status', 'drone_name': drone_name}
        print("sending get_mission_status message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for get_mission_status")
            return reply['mission_status']
        else:
            print(reply['message'])
            return False
    
    def return_to_home(self, drone_name):
        '''Returns the drone to its launch location'''
        msg = {'fcn': 'return_to_home', 'drone_name': drone_name}
        print("sending return_to_home message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for return_to_home")
            return True
        else:
            print(reply['message'])
            return False
    
    def get_drone_position(self, drone_name):
        '''Returns the current state of the drone in the form of a dictionary {Lat: Decimal degrees , Lon: Decimal degrees , Alt: AMSL , Heading: degrees relative true north}'''
        msg = {'fcn': 'get_drone_position', 'drone_name': drone_name}
        print("sending get_drone_position message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for get_drone_position")
            return reply['drone_position']
        else:
            print(reply['message'])
            return False

    def get_drone_waypoint(self, drone_name):
        '''Returns the current waypoint of the drone, {‘"lat" : lat , "lon": lon , "alt": new_alt, "alt_type": "amsl", "heading": degrees relative true north,  "speed": speed}'''
        msg = {'fcn': 'get_drone_waypoint', 'drone_name': drone_name}
        print("sending get_drone_waypoint message")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for get_drone_waypoint")
            return reply['drone_waypoint']
        else:
            print(reply['message'])
            return False
    
    def valid_drone_name(self, drone_name):
        '''Returns true if the drone name is valid'''
        if drone_name in self.drone_dict:
            print("valid drone name")
            return True
        else:
            return False