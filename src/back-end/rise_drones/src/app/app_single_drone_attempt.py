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

    #self.setup_dss_data_stream() # Not implemented
        #App-specific parameters
    
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

#--------------------------------------------------------------------#
  @property
  def alive(self):
    '''checks if application is alive'''
    return self._alive

#--------------------------------------------------------------------#
# This method runs on KeyBoardInterrupt, time to release resources and clean up.
# Disconnect connected drones and unregister from crm, close ports etc..
  def kill(self):
    '''Kill the application, close sockets, stop threads and unregister from CRM'''
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

#--------------------------------------------------------------------#
# Application reply thread
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

#--------------------------------------------------------------------#
# Application reply: 'push_dss'
  def _request_push_dss(self, msg):
    '''Not implemented'''
    answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Not implemented')
    return answer

#--------------------------------------------------------------------#
# Application reply: 'get_info'
  def _request_get_info(self, msg):
    '''Returns info about the application, specifically the app_id and the ports for info/data streams'''
    answer = dss.auxiliaries.zmq.ack(msg['fcn'])
    answer['id'] = self.crm.app_id
    answer['info_pub_port'] = self._info_socket.port
    answer['data_pub_port'] = None
    return answer

#--------------------------------------------------------------------#
# Setup the DSS info stream thread
  def setup_dss_info_stream(self):
    '''Setup the DSS info stream thread'''
    #Get info port from DSS
    info_port = self.drone.get_port('info_pub_port')
    if info_port:
      self._dss_info_thread = threading.Thread(
        target=self._main_info_dss, args=[self.drone._dss.ip, info_port])
      self._dss_info_thread_active = True
      self._dss_info_thread.start()
#--------------------------------------------------------------------#
# await init point
  def task_await_init_point(self):
    '''Wait for start position from drone'''
    # Wait until info stream up and running
    while self.alive and not self.start_pos_received:
      _logger.debug("Waiting for start position from drone...")
      time.sleep(1.0)
#--------------------------------------------------------------------#
# Setup the DSS data stream thread
  def setup_dss_data_stream(self):
    '''Setup the DSS data stream thread (Not implemented)'''
    #Get data port from DSS
    data_port = self.drone.get_port('data_pub_port')
    if data_port:
      self._dss_data_thread = threading.Thread(
        target=self._main_data_dss, args=[self.drone._dss.ip, data_port])
      self._dss_data_thread_active = True
      self._dss_data_thread.start()

#--------------------------------------------------------------------#
# The main function for subscribing to info messages from the DSS.

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
          #Not supported yet in the DSS
          #self._battery_level = msg['battery status']
          #if self._battery_level < self._battery_threshold:
          # self.keep_flying = False
          #set keep_flying flag to false when battery lower than threshold
        else:
          _logger.warning("Topic not recognized on info link: %s", topic)
      except:
        pass
    info_socket.close()
    _logger.info("Stopped thread and closed info socket")

#--------------------------------------------------------------------#
# The main function for subscribing to data messages from the DSS.
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
#--------------------------------------------------------------------#
# Connect to the drone

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
  #--------------------------------------------------------------------#
  #check if all the required keys for a mission are present
  def valid_mission(self, mission):
    '''Check if all the required keys for a mission are present'''
    for wp_id in range(0, len(mission)):
      for key in ['lat', 'lon', 'alt', 'alt_type', 'heading', 'speed']:
        id_str = "id%d" % wp_id
        if key not in mission[id_str]:
          return False
    return True

#--------------------------------------------------------------------#
#launch drone
  def task_launch_drone(self, height):
    '''Go through the launch procedure for the drone'''
    #Initialize drone
    self.drone.try_set_init_point()
    self.drone.set_geofence(max(2, self.height_min-2), self.height_max+2, self.delta_r_max+10)
    self.drone.await_controls()
    self.drone.arm_and_takeoff(height)
    self.drone.reset_dss_srtl()

  
#--------------------------------------------------------------------#
  def return_to_home(self):
    '''Start a thread that returns the drone to launch position'''
    mission_rtl = threading.Thread(target=self.fly_rtl, args=(), daemon=True)
    mission_rtl.start()
    _logger.info("Flying home")

#--------------------------------------------------------------------#
#fly rtl
  def fly_rtl(self):
    '''Fly the drone to the launch position and set the mission status to landed'''
    self.drone.rtl()
    while not self.stop_threads:
      if not self.drone._dss.get_armed():
        with self.mission_status_lock:
          self.mission_status = 'landed'

#--------------------------------------------------------------------#
#random mission time
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
  
#--------------------------------------------------------------------#
  #function to fly a mission
  def fly_mission(self, mission):
    '''Start a thread that flies the given mission'''
    with self.mission_lock:
      self.mission = mission
    with self.fly_mission_lock:
      self.fly_var = True
    with self.drone_mission_lock:
      self.drone_mission = threading.Thread(target=self.task_execute_mission, args=(mission,), daemon=True)
      self.drone_mission.start()
#--------------------------------------------------------------------#
#fly random mission
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

#--------------------------------------------------------------------#
#function to get state of the drone
  def get_drone_state(self):
    '''Get drone state, this will be a dictionary with the following keys: Lat, Lon, ALT, Agl, vel_n, vel_e, vel_d, gnss_state[0-6] (global navigation satellite system), flight_state'''
    return self.drone.get_state()
#--------------------------------------------------------------------#
#function to get the current waypoint
  def get_current_waypoint(self):
    '''Get current waypoint in lon, lat, alt'''
    return self.drone.get_currentWP()
#--------------------------------------------------------------------#
  #thread to execute mission
  
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

#--------------------------------------------------------------------#
# TEST SECTION
#--------------------------------------------------------------------#

  def main(self):
    '''test purposes'''
    while self.alive():
      time.sleep(1)

def _main(app_ip, crm = '10.44.170.10:17700', app_id = "app_single"):
  '''test purposes'''
  # Parse command-line arguments
  parser = argparse.ArgumentParser(description='APP "app_noise"', allow_abbrev=False, add_help=False)
  parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
  parser.add_argument('--app_ip', type=str, help='ip of the app', required=False)
  parser.add_argument('--id', type=str, default=None, help='id of this app_noise instance if started by crm')
  parser.add_argument('--crm', type=str, help='<ip>:<port> of crm', required=False)
  parser.add_argument('--log', type=str, default='debug', help='logging threshold')
  parser.add_argument('--owner', type=str, help='id of the instance controlling app_noise - not used in this use case')
  parser.add_argument('--stdout', action='store_true', help='enables logging to stdout')
  args = parser.parse_args()
  args.app_ip = dss.auxiliaries.zmq.get_ip()
  args.crm = '10.44.170.10:17700'

  # Identify subnet to sort log files in structure
  subnet = dss.auxiliaries.zmq.get_subnet(ip=args.app_ip)
  # Initiate log file
  dss.auxiliaries.logging.configure('app_noise', stdout=args.stdout, rotating=True, loglevel=args.log, subdir=subnet)

  # Create the AppNoise class
  try:
    app = Drone(args.app_ip, args.id, args.crm)
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
    print('', end='\r')
    _logger.warning('Shutdown due to keyboard interrupt')
  except dss.auxiliaries.exception.Nack as error:
    _logger.error(f'Nacked when sending {error.fcn}, received error: {error.msg}')
  except dss.auxiliaries.exception.NoAnswer as error:
    _logger.error(f'NoAnswer when sending: {error.fcn} to {error.ip}:{error.port}')
  except:
    _logger.error(f'unexpected exception\n{traceback.format_exc()}')

  try:
    app.kill()
  except:
    _logger.error(f'unexpected exception\n{traceback.format_exc()}')


#--------------------------------------------------------------------#
if __name__ == '__main__':
  '''test purposes'''
  _main()