import threading
import zmq
import json
from utility.helper_functions import create_logger
from config_file import DRONE_APP_REQ_URL, DRONE_APP_SUB_URL
import queue

'''This class is used to connect to drones and send missions to them'''

_context = zmq.Context()
_logger = create_logger("link")
_link_alive_event = threading.Event()

class Socket_SUB():
    def __init__(self, link_queue):
        self.socket = _context.socket(zmq.SUB)
        self.socket.connect(DRONE_APP_SUB_URL)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.mutex = threading.Lock()
        self.queue = link_queue
        self.alive = _link_alive_event

    def recieve(self) -> dict:
        '''Recieves a message from the drone_application'''
        while self.alive.is_set():
            try:
                msg = self.socket.recv_json()
                msg = json.loads(msg)
            except KeyboardInterrupt:
                _logger.debug("Keyboard interrupt, closing socket")
                self.socket.close()
            except zmq.Again as e:
                _logger.error("Error receiving message (timeout): {e}")
            except zmq.ZMQError as e:
                _logger.error(f"Error receiving message: {e}")
            except json.JSONDecodeError as e:
                _logger.error(f"Error decoding message: {e}")
                
            
            _logger.debug(f"Received message: {msg}")
            if msg['topic'] == 'lost_drones':
                lost_drones = msg['drones']
                number_of_lost_drones = len(lost_drones)
                self.queue.put({'topic':'lost_drones', 'data': {'lost_drones': lost_drones, 'number_of_lost_drones': number_of_lost_drones}})
            elif msg['topic'] == 'gained_drones':
                gained_drones = msg['drones']
                number_of_gained_drones = len(gained_drones)
                self.queue.put({'topic':'gained_drones', 'data': {'gained_drones': gained_drones, 'number_of_gained_drones': number_of_gained_drones}})
            elif msg['topic'] == 'battery_level':
                battery_level = msg['battery_level']
                drone = msg['drone']
                self.queue.put({'topic':'battery_level', 'data': {'drone': drone, 'battery_level': battery_level}})
            elif msg['topic'] == 'drone_status':
                drone_status = msg['drone_status']
                drone = msg['drone']
                self.queue.put({'topic':'drone_status', 'data': {'drone': drone, 'drone_status': drone_status}})
        self.socket.close()

class Socket_REQ():
    def __init__(self):
        self.socket = _context.socket(zmq.REQ)
        # Port and IP of the drone_application
        self.socket.connect(DRONE_APP_REQ_URL)
        self.mutex = threading.Lock()
        self.alive = _link_alive_event
    
    def send_and_recieve(self, data) -> dict:
        '''Sends a message to the drone_application and returns the reply'''
        with self.mutex:
            try:
                _logger.debug(f"Sending message: {data}")
                msg = data
                msg_str = json.dumps(msg)
                self.socket.send_json(msg_str)
            except zmq.ZMQError as e:
                _logger.error(f"Error sending message: {e}")
                return None

            try:
                reply = self.socket.recv_json()
                reply = json.loads(reply)
            except KeyboardInterrupt:
                _logger.debug("Keyboard interrupt, closing socket")
                self.socket.close()
                return None
            except zmq.Again as e:
                _logger.error("Error receiving message (timeout): {e}")
                return None
            except zmq.ZMQError as e:
                _logger.error(f"Error receiving message: {e}")
                return None
            except json.JSONDecodeError as e:
                _logger.error(f"Error decoding received JSON message: {e}")
                return None
            _logger.debug(f"Received reply: {reply}")
            return reply
    
    def request_success(self, reply):
        '''Checks if the reply from the drone_application is a success'''
        if reply['status'] == 'success':
            return True
        else:
            return False

    def close(self):
        self.socket.close()
        _logger.debug("Socket closed")      

class Link():
    '''This class is used to send and recieve information/requests from and to the drone_application'''
    def __init__(self):
        _link_alive_event.set()

        self.drone_dict = {}
        self.socket_req = Socket_REQ()
        self.msg_queue = queue.Queue()
        self.socket_sub = Socket_SUB(self.msg_queue)
        self.sub_thread = threading.Thread(target=self.socket_sub.recieve, daemon=True)
        self.sub_thread.start()
                                           
    def connect_to_drone(self):
        '''Attempts to connect to a drone'''
        msg = {'fcn':'connect_to_drone'}
        _logger.debug(f"Sending connect_to_drone message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"succesfully connected to drone: {reply['message']}")
            return True
        else:
            if reply['status'] == 'denied':
                _logger.info(f"msg denied: {reply['message']}")
            else:
                _logger.error(f"Error connecting to drone: {reply['message']}")
            return False
        
    def connect_to_all_drones(self):
        '''Attempts to connect to as many drones as possible'''
        msg = {'fcn':'connect_to_all_drones'}
        _logger.debug(f"Sending connect_to_all_drones message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"connect_to_all_drones success: {reply['message']}")
            return reply["message"]
        else:
            if reply['status'] == 'denied':
                _logger.info(f"msg denied: {reply['message']}")
            else:
                _logger.error(f"Error connecting to drones: {reply['message']}")
            return False
    
    def get_list_of_drones(self):
        '''Gets a list of all connected drones'''
        msg = {'fcn': 'get_list_of_drones'}
        _logger.debug(f"Sending get_list_of_drones message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"Received drone list: {reply['drone_list']}")
            return reply['drone_list']
        else:
            _logger.error(f"Error getting list of drones: {reply['message']}")
            return False

    def fly(self, mission, drone):
        '''Attempts to fly the specified mission with the specified drone'''
        msg = {'fcn': 'fly', 'mission': mission.as_mission_dict(), 'drone_name': drone.id}
        _logger.debug(f"Sending fly message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug("request success for fly")
            return True
        else:
            _logger.error(f"request failed for fly: {reply['message']}")
            return False 
    
    def fly_random_mission(self, drone, n_wps = 10):
        '''Attempts to fly a random mission with the specified drone'''
        msg = {'fcn': 'fly_random_mission', 'drone_name': drone.id, 'n_wps': n_wps}
        _logger.debug(f"Sending fly_random_mission message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug("request success for fly_random_mission")
            return True
        else:
            _logger.error(f"request failed for fly_random_mission: {reply['message']}")
            return False

    def get_drone_status(self, drone):
        '''Gets the status of the mission, 'flying' = mission is in progress, 'waiting' = flying and waiting for a new mission, 
        'idle' = not flying and idle, 'landed' = on the ground, 'denied' = mission was denied, 'charging' = charging'''
        msg = {'fcn': 'get_drone_status', 'drone_name': drone.id}
        _logger.debug(f"Sending get_drone_status message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"Received mission status: {reply['mission_status']}")
            return reply['mission_status']
        else:
            _logger.error(f"Error getting mission status: {reply['message']}")
            return False
    
    def return_to_home(self, drone):
        '''Attempts to return the drone to its home position'''
        msg = {'fcn': 'return_to_home', 'drone_name': drone.id}
        _logger.debug(f"Sending return_to_home message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            print("request success for return_to_home")
            return True
        else:
            print(reply['message'])
            return False
    
    def get_drone_position(self, drone):
        '''Gets the current state of the drone in the form of a dictionary {Lat: Decimal degrees , Lon: Decimal degrees , Alt: AMSL , Heading: degrees relative true north}'''
        msg = {'fcn': 'get_drone_position', 'drone_name': drone.id}
        _logger.debug(f"Sending get_drone_position message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"Received drone position: {reply['drone_position']}")
            return reply['drone_position']
        else:
            _logger.error(f"Error getting drone position: {reply['message']}")
            return False

    def get_drone_waypoint(self, drone):
        '''Gets the current waypoint of the drone, {"lat" : lat , "lon": lon , "alt": new_alt, "alt_type": "amsl", "heading": degrees relative true north,  "speed": speed}'''
        msg = {'fcn': 'get_drone_waypoint', 'drone_name': drone.id}
        _logger.debug(f"Sending get_drone_waypoint message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"Received drone waypoint: {reply['drone_waypoint']}")
            return reply['drone_waypoint']
        else:
            _logger.error(f"Error getting drone waypoint: {reply['message']}")
            return False
    
    def valid_drone_name(self, drone):
        '''Returns True if the drone name is valid, False otherwise'''
        msg = {'fcn': 'get_valid_drone_name', 'drone_name': drone.id}
        _logger.debug(f"Sending valid_drone_name message: {msg}")
        reply = self.socket.send_and_recieve(msg)
        if self.socket.request_success(reply):
            _logger.debug(f"Received valid drone name: {reply['valid']}")
            return reply['valid']
        else:
            _logger.error(f"Error getting valid drone name: {reply['message']}")
            return False
    
    def get_drone_battery(self, drone):
        return 100
    
    def kill(self):
        '''Closes socket'''
        _logger.debug("Closing socket")
        _link_alive_event.clear()
        self.sub_thread.join()
        self.socket_req.close()

