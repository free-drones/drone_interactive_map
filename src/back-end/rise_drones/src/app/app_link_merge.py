#!/usr/bin/env python3

'''
APP "app_template"

This app connects to CRM and receives an app_id.
'''

import json
import logging
import threading
import time
import numpy as np
import zmq
import sys
import traceback
import argparse

import dss.auxiliaries
import dss.client

#--------------------------------------------------------------------#

__author__ = 'Lennart Ochel <lennart.ochel@ri.se>, Andreas Gising <andreas.gising@ri.se>, Kristoffer Bergman <kristoffer.bergman@ri.se>, Hanna Müller <hanna.muller@ri.se>, Joel Nordahl'
__version__ = '0.2.0'
__copyright__ = 'Copyright (c) 2022, RISE'
__status__ = 'development'

#--------------------------------------------------------------------#

_logger = logging.getLogger('single_drone')
_context = zmq.Context()
IP = dss.auxiliaries.zmq.get_ip()

#--------------------------------------------------------------------#

class Waypoint():
  '''Class used to store position data'''
  def __init__(self):
    self.lat = 0.0
    self.lon = 0.0
    self.alt = 0.0

  def set_lla(self, lat, lon, alt):
    self.lat = lat
    self.lon = lon
    self.alt = alt

  def copy_lla(self, other_wp):
    self.lat = other_wp.lat
    self.lon = other_wp.lon
    self.alt = other_wp.alt

def ne_to_ll(loc1, d_northing, d_easting):
  d_lat = d_northing/(1852*60)
  d_lon = d_easting/(1852*60*np.cos(loc1.lat/180*np.pi))
  return (d_lat, d_lon)
def get_3d_distance(loc1, loc2):
  dlat = loc2.lat - loc1.lat
  dlon = loc2.lon - loc1.lon
  dalt = loc2.alt - loc1.alt

  # Convert to meters
  d_northing = dlat * 1852 * 60
  d_easting = dlon *1852 * 60 * np.cos(loc1.lat/180*np.pi)

  # Calc distances
  d_2d = np.sqrt(d_northing**2 + d_easting**2)
  d_3d = np.sqrt(d_northing**2 + d_easting**2 + dalt**2)

  # Calc bearing
  bearing = np.arctan2(d_easting, d_northing)
  return (d_northing, d_easting, dalt, d_2d, d_3d, bearing)

class Link():
  '''This class is used to connect to drones and send missions to them'''
  def __init__(self):
      self.drone_dict = {}

      self.ip = IP                                     # auto ip for now
      self.crm = '10.44.170.10:17700'                  # crm ip and port
      self.alive=True

      # The application sockets
      # Use ports depending on subnet used to pass RISE firewall
      # Rep: ANY -> APP
      self._app_socket = dss.auxiliaries.zmq.Rep(_context,self.ip, label='link', min_port=17700, max_port=17750)
      print(self._app_socket.port)
      print(self._app_socket.ip)
      
      self._commands = {'connect_to_drone':       {'request': self._request_connect_to_drone},
                        'get_list_of_drones':     {'request': self._request_get_list_of_drones},
                        'fly':                    {'request': self._request_fly},
                        'fly_random_mission':      {'request': self._request_fly_random_mission},
                        'get_mission_status':     {'request': self._request_get_mission_status},
                        'get_drone_waypoint':     {'request': self._request_get_drone_waypoint},
                        'return_to_home':         {'request': self._request_return_to_home},
                        'get_drone_position':     {'request': self._request_get_drone_position},}

  
  def main(self):
    '''Listens for requests from ANY, tries to carry out said requests and replies'''
    print("i am listening on ip: " ,self._app_socket.ip ," and port: ", self._app_socket.port)
    _logger.info('Reply socket for link is listening on port: %d', self._app_socket.port)
    while self.alive:
      try:
        print("Waiting for message...")
        msg = self._app_socket.recv_json()
        print(f"Received message: {msg}")
        msg = json.loads(msg)
        fcn = msg['fcn'] if 'fcn' in msg else ''
        if fcn in self._commands:
          request = self._commands[fcn]['request']
          answer = request(msg)
        else:
          answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Request not supported')
        answer = json.dumps(answer)
        print(f"Sending answer: {answer}")
        self._app_socket.send_json(answer)
      except KeyboardInterrupt:
          _logger.warning('Shutdown due to keyboard interrupt')
          break
      except:
        pass
    self._app_socket.close()
    _logger.info("Reply socket closed, thread exit")
    

#-------------------------- Request functions --------------------------#
  def _request_get_list_of_drones(self, msg):
    '''Handles get_list_of_drones request and sends the list of drones as a reply.'''
    # Call the get_list_of_drones function
    list_of_drones = self.get_list_of_drones()

    # Construct the reply
    reply = {'status': 'success',
            'fcn': 'get_list_of_drones',
            'drone_list': list(list_of_drones)} # Convert the keys view object to a list
    return reply
  

  def _request_fly(self, msg):
    '''Handles the fly request and starts a new thread that flies the specified mission with the specified drone.'''
    # Extract the required information from the msg
    mission = msg['mission']
    drone_name = msg['drone_name']

    if mission is None or drone_name is None:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'Missing required information (mission or drone_name)'}
        return reply

    try:
        self.fly(mission, drone_name)
        reply = {'status': 'success',
                'fcn': 'fly',
                'message': f'Mission started for drone {drone_name}'}
    except KeyError:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply
  

  def _request_fly_random_mission(self, msg):
    '''Handles the fly request and starts a new thread that flies the specified mission with the specified drone.'''
    # Extract the required information from the msg
    drone_name = msg['drone_name']

    if  drone_name is None:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'Missing required information drone_name'}
        return reply

    try:
        self.fly_random_mission(drone_name)
        reply = {'status': 'success',
                'fcn': 'fly',
                'message': f'Random mission started for drone {drone_name}'}
    except KeyError:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply
  

  def _request_get_mission_status(self, msg):
    '''Handles the get_mission_status request and returns the mission status of the specified drone.'''
    # Extract the required information from the msg
    drone_name = msg.get('drone_name')

    if drone_name is None:
        reply = {'status': 'error',
            'fcn': 'get_mission_status',
            'message': 'Missing required information (drone_name)'}
        return reply
    try:
        mission_status = self.get_mission_status(drone_name)
        reply = {'status': 'success',
            'fcn': 'get_mission_status',
            'drone_name': drone_name,
            'mission_status': mission_status}
    except KeyError:
        reply = {'status': 'error',
            'fcn': 'get_mission_status',
            'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply


  def _request_connect_to_drone(self, msg):
    '''Handles the connect_to_drone request and creates a new drone object, adding it to the drone dictionary.'''
    connected = self.connect_to_drone()
    if connected:
        reply = {'status': 'success',
            'fcn': 'connect_to_drone',
            'message': 'Drone connected successfully',
            'drone_name': f'drone{len(self.drone_dict) - 1}'}
    else:
        reply = {'status': 'error',
            'fcn': 'connect_to_drone',
            'message': 'Failed to connect to drone'}
    return reply
  

  def _request_get_drone_waypoint(self, msg):
    '''Handles the get_drone_waypoint request and returns the current waypoint of the specified drone.'''
    # Extract the required information from the msg
    drone_name = msg.get('drone_name')

    if drone_name is None:
        reply = {'status': 'error',
                'fcn': 'get_drone_waypoint',
                'message': 'Missing required information (drone_name)'}
        return reply

    try:
        waypoint = self.get_drone_waypoint(drone_name)
        reply = {'status': 'success',
                'fcn': 'get_drone_waypoint',
                'drone_name': drone_name,
                'drone_waypoint': waypoint}
    except KeyError:
        reply = {'status': 'error',
                'fcn': 'get_drone_waypoint',
                'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply
  

  def _request_return_to_home(self, msg):
    '''Handles the return_to_home request and returns the specified drone to its launch location.'''
    # Extract the required information from the msg
    drone_name = msg.get('drone_name')

    if drone_name is None:
        reply = {'status': 'error',
                'fcn': 'return_to_home',
                'message': 'Missing required information (drone_name)'}
        return reply

    try:
        self.return_to_home(drone_name)
        reply = {'status': 'success',
                'fcn': 'return_to_home',
                'message': f'Drone {drone_name} returning to home'}
    except KeyError:
        reply = {'status': 'error',
            'fcn': 'return_to_home',
            'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply
  

  def _request_get_drone_position(self, msg):
    '''Handles the get_drone_position request and returns the current state of the specified drone.'''
    # Extract the required information from the msg
    drone_name = msg.get('drone_name')

    if drone_name is None:
        reply = {'status': 'error',
                'fcn': 'get_drone_position',
                'message': 'Missing required information (drone_name)'}
        return reply

    try:
        drone_position = self.get_drone_position(drone_name)
        reply = {'status': 'success',
                'fcn': 'get_drone_position',
                'drone_name': drone_name,
                'drone_position': drone_position}
    except KeyError:
        reply = {'status': 'error',
                'fcn': 'get_drone_position',
                'message': 'Invalid drone name'}
    except Exception:
        reply = {'status': 'error',
                'fcn': 'fly',
                'message': 'something went wrong'}
    return reply
  
  
# -------------------------- Drone Management -------------------------- # 
  def connect_to_drone(self):
    '''Creates a new drone object and adds it to the drone dictionary'''
    print("i am trying to connect to a drone")
    drone_name = "drone"+ str(len(self.drone_dict))
    new_drone = Drone(self.ip, drone_name, self.crm)
    if new_drone.drone_connected:
        self.drone_dict[drone_name] = new_drone
        print("i connected to a drone")
        return True
    else:
        # kill any threads that were created
        new_drone.kill()
        return False


  def get_list_of_drones(self):
      '''Returns a list of all drones'''
      return self.drone_dict.keys()
  

  def kill(self):
      '''Kills all drones and clears the drone dictionary, runs on keyboard interrupt'''
      if not self.drone_dict == {}:
          for drone in self.drone_dict.values():
              drone.kill()
      self.drone_dict = {}
      self.alive = False
      self._app_socket.close()


  def fly(self, mission, drone_name):
      '''Starts a new thread that flies the specified mission with the specified drone'''
      if not self.valid_drone_name(drone_name):
          raise KeyError('Invalid drone name')
      if self.drone_dict[drone_name].validate_mission(mission):
          with self.drone_dict[drone_name].mission_status_lock:
              self.drone_dict[drone_name].mission_status = 'flying'
          # stop the current mission
          self.drone_dict[drone_name].stop_threads.set()
          time.sleep(3)
          # allows for next mission to be flown
          self.drone_dict[drone_name].stop_threads.clear()
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
      # stop the current mission
      self.drone_dict[drone_name].stop_threads.set()
      time.sleep(3)
      # allows for next mission to be flown
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
      # stop the current mission
      self.drone_dict[drone_name].stop_threads.set()
      time.sleep(3)
      # allows for next mission to be flown
      home_thread = threading.Thread(self.drone_dict[drone_name].return_to_home(), daemon=True)
      home_thread.start()


  def get_drone_position(self, drone_name):
      '''Returns the current state of the drone in the form of a dictionary {Lat: Decimal degrees , Lon: Decimal degrees , Alt: AMSL , Heading: degrees relative true north}'''
      if not self.valid_drone_name(drone_name):
          raise KeyError('Invalid drone name')
      return self.drone_dict[drone_name].get_drone_location()


  def get_drone_waypoint(self, drone_name):
      '''Returns the current waypoint of the drone, {‘"lat" : lat , "lon": lon , "alt": new_alt, "alt_type": "amsl", "heading": degrees relative true north,  "speed": speed}'''
      if not self.valid_drone_name(drone_name):
          raise KeyError('Invalid drone name')
      return self.drone_dict[drone_name].get_current_waypoint()


  def valid_drone_name(self, drone_name):
      '''Returns true if the drone name is valid'''
      if drone_name in self.drone_dict:
          return True
      else:
          return False

class Drone():
  # Init
  def __init__(self, app_ip, app_id, crm, _context=_context):
    # Create Client object
    self.drone = dss.client.Client(timeout=2000, exception_handler=None, context=_context)
    self.mission = {}
    self.mission_status = 'idle'
    self.drone_connected = False
    self.drone_mission = None
    self.fly_var = False

    # threading events for thread control
    self.stop_threads = threading.Event()

    # Create CRM object
    self.crm = dss.client.CRM(_context, crm, app_name=app_id, desc='single drone connection', app_id="")

    # initialize variables
    self._alive = True
    self._dss_data_thread = None
    self._dss_data_thread_active = False
    self._dss_info_thread = None
    self._dss_info_thread_active = False

    # locks for objects that can be accessed by multiple threads
    self.drone_mission_lock = threading.Lock()
    self.mission_status_lock = threading.Lock()
    self.fly_mission_lock = threading.Lock()
    self.mission_lock = threading.Lock()

    # Find the VPN ip of host machine
    auto_ip = dss.auxiliaries.zmq.get_ip()
    if auto_ip != app_ip:
      _logger.warning("Automatic get ip function and given ip does not agree: %s vs %s", auto_ip, app_ip)

    # The application sockets
    # Use ports depending on subnet used to pass RISE firewall
    # Rep: ANY -> APP
    self._app_socket = dss.auxiliaries.zmq.Rep(_context, label='app', min_port=self.crm.port, max_port=self.crm.port+50)
    # Pub: APP -> ANY
    self._info_socket = dss.auxiliaries.zmq.Pub(_context, label='info', min_port=self.crm.port, max_port=self.crm.port+50)

    # Start the app reply thread
    self._app_reply_thread = threading.Thread(target=self._main_app_reply, daemon=True)
    self._app_reply_thread.start()

    # Register with CRM (self.crm.app_id is first available after the register call)
    _ = self.crm.register(app_ip, self._app_socket.port)

    # All nack reasons raises exception, registreation is successful
    _logger.info('App %s listening on %s:%s', self.crm.app_id, self._app_socket.ip, self._app_socket.port)
    _logger.info(f'App_template_photo_mission registered with CRM: {self.crm.app_id}')

    # drone position tracking
    self.start_pos_received = False
    self.start_pos = Waypoint() # Start position of the drone
    self.drone_pos = Waypoint() # Current position of the drone

    # Update socket labels with received id
    self._app_socket.add_id_to_label(self.crm.app_id)
    self._info_socket.add_id_to_label(self.crm.app_id)

    # Supported commands from ANY to APP
    self._commands = {'push_dss':     {'request': self._request_push_dss}, # Not implemented
                      'get_info':     {'request': self._request_get_info}}
    
    # Start class specific threads
    self.connect_to_drone()
    self.setup_dss_info_stream()
    
    # Cheat battery level because it is not implemented in DSS
    self.battery_level = 100.0 

    #Parameters for generate_random_mission()
    self.default_speed = 5.0
    #distance between waypoints
    self.wp_dist = 20.0
    #geofence parameters
    self.delta_r_max = 50.0
    self.height_max = 30.0
    self.height_min = 14.0
    #maximum total time (seconds)
    self.t_max = 240.0
    #take-off height
    self.takeoff_height = 15.0


  @property
  def alive(self):
    '''checks if application is alive'''
    return self._alive


  def kill(self):
    '''This method runs on KeyBoardInterrupt, time to release resources and clean up.
      Disconnect connected drones and unregister from crm, close ports etc..'''
    _logger.info("Closing down...")
    self._alive = False
    # Kill info and data thread
    self._dss_info_thread_active = False
    self._dss_data_thread_active = False
    self._info_socket.close()
    # stop all other threads
    with self.drone_mission_lock:
      if self.drone_mission is not None:
        self.mission_status = 'idle'
        self.drone_mission = None
        self.stop_threads.set()

    # Unregister APP from CRM
    _logger.info("Unregister from CRM")
    answer = self.crm.unregister()
    if not dss.auxiliaries.zmq.is_ack(answer):
      _logger.error('Unregister failed: {answer}')
    _logger.info("CRM socket closed")

    # Disconnect drone if drone is alive
    if self.drone.alive:
      #wait until other DSS threads finished
      time.sleep(0.5)
      _logger.info("Closing socket to DSS")
      self.drone.close_dss_socket()

    _logger.debug('~ THE END ~')


  def _main_app_reply(self):
    '''Listens for requests from ANY, tries to carry out said requests and replies'''
    _logger.info('Reply socket is listening on port: %d', self._app_socket.port)
    while self.alive:
      try:
        msg = self._app_socket.recv_json()
        msg = json.loads(msg)
        fcn = msg['fcn'] if 'fcn' in msg else ''
        if fcn in self._commands:
          request = self._commands[fcn]['request']
          answer = request(msg)
        else :
          answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Request not supported')
        answer = json.dumps(answer)
        self._app_socket.send_json(answer)
      except:
        pass
    self._app_socket.close()
    _logger.info("Reply socket closed, thread exit")


#-------------------------- Request functions --------------------------#
  def _request_push_dss(self, msg):
    '''Not implemented'''
    answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Not implemented')
    return answer


  def _request_get_info(self, msg):
    '''Returns info about the application, specifically the app_id and the ports for info/data streams'''
    answer = dss.auxiliaries.zmq.ack(msg['fcn'])
    answer['id'] = self.crm.app_id
    answer['info_pub_port'] = self._info_socket.port
    answer['data_pub_port'] = None
    return answer


  def setup_dss_info_stream(self):
    '''Setup the DSS info stream thread'''
    #Get info port from DSS
    info_port = self.drone.get_port('info_pub_port')
    if info_port:
      self._dss_info_thread = threading.Thread(
        target=self._main_info_dss, args=[self.drone._dss.ip, info_port])
      self._dss_info_thread_active = True
      self._dss_info_thread.start()


  def task_await_init_point(self):
    '''Wait for start position from drone'''
    # Wait until info stream up and running
    while self.alive and not self.start_pos_received:
      _logger.debug("Waiting for start position from drone...")
      time.sleep(1.0)


  def setup_dss_data_stream(self):
    '''Setup the DSS data stream thread (Not implemented)'''
    #Get data port from DSS
    data_port = self.drone.get_port('data_pub_port')
    if data_port:
      self._dss_data_thread = threading.Thread(
        target=self._main_data_dss, args=[self.drone._dss.ip, data_port])
      self._dss_data_thread_active = True
      self._dss_data_thread.start()


  def _main_info_dss(self, ip, port):
    '''The main function for subscribing to info messages from the DSS.'''
    # Enable LLA stream
    self.drone._dss.data_stream('LLA', True)
    self.drone._dss.data_stream('battery', True)
    # Create info socket and start listening thread
    info_socket = dss.auxiliaries.zmq.Sub(_context, ip, port, "info " + self.crm.app_id)
    print(self._dss_data_thread_active)
    while self._dss_info_thread_active:
      try:
        (topic, msg) = info_socket.recv()
        if topic == "LLA":
          self.drone_pos.lat = msg['lat']
          self.drone_pos.lon = msg['lon']
          self.drone_pos.alt = msg['alt']
          if not self.start_pos_received:
            self.start_pos.lat = msg['lat']
            self.start_pos.lon = msg['lon']
            self.start_pos.alt = msg['alt']
            self.start_pos_received = True
        elif topic == 'battery':
          _logger.debug("Not implemented yet...")
        else:
          _logger.warning("Topic not recognized on info link: %s", topic)
      except:
        pass
    info_socket.close()
    _logger.info("Stopped thread and closed info socket")


  def _main_data_dss(self, ip, port):
    '''The main function for subscribing to data messages from the DSS.)'''
    # Create data socket and start listening thread
    data_socket = dss.auxiliaries.zmq.Sub(_context, ip, port, "data " + self.crm.app_id)
    while self._dss_data_thread_active:
      try:
        (topic, msg) = data_socket.recv()
        if topic in ('photo', 'photo_low'):
          data = dss.auxiliaries.zmq.string_to_bytes(msg["photo"])
          photo_filename = msg['metadata']['filename']
          dss.auxiliaries.zmq.bytes_to_image(photo_filename, data)
          json_filename = photo_filename[:-4] + ".json"
          dss.auxiliaries.zmq.save_json(json_filename, msg['metadata'])
          _logger.info("Photo saved to " + msg['metadata']['filename']  + "\r")
          _logger.info("Photo metadata saved to " + json_filename + "\r")
          self.transferred += 1
        else:
          _logger.info("Topic not recognized on data link: %s", topic)
      except:
        pass
    data_socket.close()
    _logger.info("Stopped thread and closed data socket")


  def connect_to_drone(self, capabilities=['SIM']):
    '''Ask the CRM for a drone with specified capabilities (default simulated ['SIM']) and connect to it'''
    answer = self.crm.get_drone(capabilities)
    if dss.auxiliaries.zmq.is_nack(answer):
      _logger.error(f'Did not receive a drone: {dss.auxiliaries.zmq.get_nack_reason(answer)}')
      _logger.info('No available drone')
      self.drone_connected = False
      return
    # Connect to the drone, set app_id in socket
    try:
      self.drone.connect(answer['ip'], answer['port'], app_id=self.crm.app_id)
      _logger.info(f"Connected as owner of drone: [{self.drone._dss.dss_id}]")
      self.drone_connected = True
    except:
      _logger.info("Failed to connect as owner, check crm")
      self.drone_connected = False
      return


  def valid_mission(self, mission):
    '''Check if all the required keys for a mission are present'''
    for wp_id in range(0, len(mission)):
      for key in ['lat', 'lon', 'alt', 'alt_type', 'heading', 'speed']:
        id_str = "id%d" % wp_id
        if key not in mission[id_str]:
          return False
    return True


  def task_launch_drone(self, height):
    '''Go through the launch procedure for the drone'''
    #Initialize drone
    self.drone.try_set_init_point()
    self.drone.set_geofence(max(2, self.height_min-2), self.height_max+2, self.delta_r_max+10)
    self.drone.await_controls()
    self.drone.arm_and_takeoff(height)
    self.drone.reset_dss_srtl()


  def return_to_home(self):
    '''Start a thread that returns the drone to launch position'''
    mission_rtl = threading.Thread(target=self.fly_rtl, args=(), daemon=True)
    mission_rtl.start()
    _logger.info("Flying home")


  def fly_rtl(self):
    '''Fly the drone to the launch position and set the mission status to landed'''
    self.drone.rtl()
    while not self.stop_threads:
      if not self.drone._dss.get_armed():
        with self.mission_status_lock:
          self.mission_status = 'landed'


  def generate_random_mission(self, n_wps):
    '''Function to construct a new mission based on current position and a
    given area '''
    #Compute distance from start position
    mission = {}
    current_wp = Waypoint()
    current_wp.copy_lla(self.drone_pos)
    for wp_id in range(0, n_wps):
      (_, _, _, d_start, _, bearing) = get_3d_distance(self.start_pos, current_wp)
      if d_start <= self.delta_r_max - self.wp_dist:
        #Safe to generate a random point (meter)
        delta_dir = np.random.uniform(-np.pi, np.pi)
      else:
        #move back towards start pos
        delta_dir = (bearing + 2*np.pi) % (2 * np.pi) - np.pi
      #Compute new lat lon
      d_northing = self.wp_dist*np.cos(delta_dir)
      d_easting = self.wp_dist*np.sin(delta_dir)
      (d_lat, d_lon) = ne_to_ll(current_wp, d_northing, d_easting)
      new_lat = current_wp.lat + d_lat
      new_lon = current_wp.lon + d_lon
      # Compute new altitude
      new_height = current_wp.alt - self.start_pos.alt + np.random.uniform(-2.0, 2.0)
      new_alt = self.start_pos.alt + min(self.height_max, max(self.height_min, new_height))
      current_wp.set_lla(new_lat, new_lon, new_alt)

      id_str = "id%d" % wp_id
      mission[id_str] = {
        "lat" : new_lat, "lon": new_lon, "alt": new_alt, "alt_type": "amsl", "heading": "course", "speed": self.default_speed
      }
    # Add start position as final wp
    id_str = "id%d" % n_wps
    mission[id_str] = {
        "lat" : self.start_pos.lat, "lon": self.start_pos.lon, "alt": new_alt, "alt_type": "amsl", "heading": "course", "speed": self.default_speed
    }
    return mission


  def fly_mission(self, mission):
    '''Start a thread that flies the given mission'''
    with self.mission_lock:
      self.mission = mission
    with self.fly_mission_lock:
      self.fly_var = True
    with self.drone_mission_lock:
      self.drone_mission = threading.Thread(target=self.task_execute_mission, args=(mission,), daemon=True)
      self.drone_mission.start()


  def fly_random_mission(self, n_wps = 10):
    '''Start a thread that flies a random mission of default length 5 waypoints'''
    if not self.drone._dss.get_armed():
      self.task_launch_drone(self.takeoff_height)
    self.task_await_init_point()
    mission = self.generate_random_mission(n_wps)
    self.mission = mission
    with self.fly_mission_lock:
      self.fly_var = True
    with self.drone_mission_lock:
      self.drone_mission = threading.Thread(target=self.task_execute_mission, args=(mission,), daemon=True)
      self.drone_mission.start()


  def get_drone_state(self):
    '''Get drone state, this will be a dictionary with the following keys: Lat, Lon, ALT, Agl, vel_n, vel_e, vel_d, gnss_state[0-6] (global navigation satellite system), flight_state'''
    return self.drone.get_state()



  def get_current_waypoint(self):
    '''Get current waypoint in lon, lat, alt'''
    return self.drone.get_currentWP()



  def task_execute_mission(self, mission):
    '''Flies a mission and updates the mission status accordingly'''
    while not self.stop_threads.is_set():
      self.drone.upload_mission_LLA(mission)
      time.sleep(0.5)
      # Fly waypoints, allow PILOT intervention.
      start_wp = 0
      while self.fly_var:
        try:
          self.drone.fly_waypoints(start_wp)
        except dss.auxiliaries.exception.Nack as nack:
          if nack.msg == 'Not flying':
            _logger.info("Pilot has landed")
            with self.mission_status_lock:
              self.mission_status = 'landed'
          else:
            _logger.info("Fly mission was nacked %s", nack.msg)
            with self.mission_status_lock:
              self.mission_status = 'denied'
          break
        except dss.auxiliaries.exception.AbortTask:
          # PILOT took controls
          (current_wp, _) = self.drone.get_currentWP()
          # Prepare to continue the mission
          start_wp = current_wp
          _logger.info("Pilot took controls, awaiting PILOT action")
          self.drone.await_controls()
          _logger.info("PILOT gave back controls")
          # Try to continue mission
          continue
        else:
          # Mission is completed
          self.fly_var = False
          with self.mission_status_lock:
            self.mission_status = 'waiting'
          break
      with self.mission_status_lock:
        self.mission_status = 'waiting'


  def main(self):
    '''Main loop of the application'''
    while self.alive():
      time.sleep(1)


def _main(app_ip= None, crm = '10.44.170.10:17700', app_id = "app_single"):
  '''Main function to innitialize the application and start the main loop'''
  try:
    app = Link()
  except dss.auxiliaries.exception.NoAnswer:
    _logger.error('Failed to instantiate application: Probably the CRM couldn\'t be reached')
    sys.exit()
  except:
    _logger.error('Failed to instantiate application\n%s', traceback.format_exc())
    sys.exit()

  # Try to setup objects and initial sockets
  try:
    # Try to run main
    app.main()
  except KeyboardInterrupt:
    _logger.warning('Shutdown due to keyboard interrupt')
    app.kill()
  try:
    app.kill()
  except:
    _logger.error(f'unexpected exception\n{traceback.format_exc()}')


#--------------------------------------------------------------------#
if __name__ == '__main__':
  _main()