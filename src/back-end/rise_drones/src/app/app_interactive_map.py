import argparse
import json
import logging
import sys
import threading
import time
import traceback
import numpy as np
#import zmq from the virtual environment
import zmq
import dss

import rise_drones.src.dss.auxiliaries
import rise_drones.src.dss.client

_logger = logging.getLogger('dss.app_interactive_map')
_context = zmq.Context()
#TODO: investigate whether gogo runs the next pending mission even if a mission is underway
#TODO: Implement ask functions for drone status, (this includes current position, waypoint, mission, etc.)
#TODO: Figure out the taking pictures part
#TODO: Clean up the file after tests (when we know what we need and what we don't)
#TODO: fix the logger for new and old functions
#TODO: Fix main so that it is coherent with the new functions and new purpose of the app
#TODO: Connect to config file
#--------------------------------------------------------------------#
class Waypoint():
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

class InteractiveMap():
  def __init__(self, app_ip, app_id, crm):

    self.drone_dict = {}

    self.mission_complete = []

    flying_missions = {}

    self.drone_mission = {}

    self.crm = dss.client.CRM(_context, crm, app_name='app_interactive_map.py', desc='interactive map mission', app_id=app_id)

    #locks
    self.mission_complete_lock = threading.Lock()
    self.drone_mission_lock = threading.Lock()
    #--------------------------------------------------------------------#

    self._alive = True
    self._dss_data_thread = None
    self._dss_data_thread_active = False
    self._dss_info_thread = None
    self._dss_info_thread_active = False

    # Find the VPN ip of host machine
    self._app_ip = app_ip
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

    # Start the mission_flier thread
    #self._mission_flier_thread = threading.Thread(target=self._mission_flier, daemon=True)
    #self._mission_flier_thread.start()

    # Supported commands from ANY to APP
    self._commands = {'push_dss':     {'request': self._request_push_dss}, # Not implemented
                      'get_info':     {'request': self._request_get_info}}

    # Register with CRM (self.crm.app_id is first available after the register call)
    _ = self.crm.register(self._app_ip, self._app_socket.port)

    # Update socket labels with received id
    self._app_socket.add_id_to_label(self.crm.app_id)
    self._info_socket.add_id_to_label(self.crm.app_id)

    # All nack reasons raises exception, registration is successful
    _logger.info('App %s listening on %s:%s', self.crm.app_id, self._app_socket.ip, self._app_socket.port)
    _logger.info(f'app_interactive_map registered with CRM: {self.crm.app_id}')

    # CONFIGS FOR STARTING CONDITIONS
    #App-specific parameters
    self.drone_pos = Waypoint()
    self.battery_level = 100.0

    self.start_pos_received = False
    self.start_pos = Waypoint()
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
    _logger.info("Closing down...")
    self._alive = False
    # Kill info and data thread
    self._dss_info_thread_active = False
    self._dss_data_thread_active = False

    # Unregister APP from CRM
    _logger.info("Unregister from CRM")
    answer = self.crm.unregister()
    if not dss.auxiliaries.zmq.is_ack(answer):
      _logger.error('Unregister failed: {answer}')
    _logger.info("CRM socket closed")

    # for every drone in drone_dict Disconnect drone if drone is alive
    for drone_name in self.drone_dict:
      if self.drone_dict[drone_name].alive:
        #wait until other DSS threads finished
        time.sleep(0.5)
        _logger.info("Closing socket to DSS")
        self.drone_dict[drone_name].close_dss_socket()

    _logger.debug('~ THE END ~')

#--------------------------------------------------------------------#
# Application reply thread
  def _main_app_reply(self):
    _logger.info(f'Reply socket is listening on: {self._app_socket.port}')
    while self.alive:
      try:
        msg = self._app_socket.recv_json()
        msg = json.loads(msg)
        fcn = msg['fcn'] if 'fcn' in msg else ''
        if fcn in self._commands:
          request = self._commands[fcn]['request']
          answer = request(msg)
        else:
          answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Request not supported')
        answer = json.dumps(answer)
        self._app_socket.send_json(answer)
      except:
        pass
    self._app_socket.close()
    _logger.info("Reply socket closed, thread exit")

#--------------------------------------------------------------------#
# Application reply: 'load_mission'
  def ask_load_mission(self, mission, drone_name):
    if self.valid_mission(mission):
      with self.drone_mission_lock:
        self.drone_mission[drone_name] = mission
      return True
    else:
      return False
#--------------------------------------------------------------------#
# Application reply: 'connect_to_drones'
  def ask_connect_to_drones(self, drone_number):
    drone_list = []
    for i in range(drone_number):
      answer = self.task_connect_to_drone()
      if answer[0]:
        drone_list.append(answer[1])
      else:
        return (drone_list, "Failed to connect to drone" + str(i))
    return (drone_list, "Connected to all drones")
      

#--------------------------------------------------------------------#
# Application reply: 'push_dss'
  def _request_push_dss(self, msg):
    answer = dss.auxiliaries.zmq.nack(msg['fcn'], 'Not implemented')
    return answer

#--------------------------------------------------------------------#
# Applicaiton reply: 'get_info'
  def _request_get_info(self, msg):
    answer = dss.auxiliaries.zmq.ack(msg['fcn'])
    answer['id'] = self.crm.app_id
    answer['info_pub_port'] = self._info_socket.port
    answer['data_pub_port'] = None
    return answer

#--------------------------------------------------------------------#
  # Setup the DSS info stream thread
  def setup_dss_info_stream(self, drone_name):
    #Get info port from DSS
    answer = self.drone_dict[drone_name]._dss.get_info()
    info_port = answer['info_pub_port']
    if info_port:
      self._dss_info_thread = threading.Thread(
        target=self._main_info_dss, args=[self.drone_dict[drone_name]._dss.ip, info_port])
      self._dss_info_thread_active = True
      self._dss_info_thread.start()

#--------------------------------------------------------------------#
  # The main function for subscribing to info messages from the DSS.
  def _main_info_dss(self, ip, port, drone_name):
    # Enable LLA stream
    self.drone_dict[drone_name]._dss.data_stream('LLA', True)
    self.drone_dict[drone_name]._dss.data_stream('battery', True)
    # Create info socket and start listening thread
    info_socket = dss.auxiliaries.zmq.Sub(_context, ip, port, "info " + self.crm.app_id)
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
  '''Function to construct a new mission based on current position and a
  given area '''
  def generate_random_mission(self, n_wps):
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
#check if all the required keys for a mission as shown above are present
  def valid_mission(self, mission):
    for wp_id in range(0, len(mission)):
      for key in ['lat', 'lon', 'alt', 'alt_type', 'heading', 'speed']:
        id_str = "id%d" % wp_id
        if key not in mission[id_str]:
          return False
    return True
    
#------------------------TASKS----------------------------------------#
  def task_connect_to_drone(self, capabilities=[]):
    drone_received = False
    while self.alive and not drone_received:
      # Get a drone
      answer = self.crm.get_drone(capabilities)
      if dss.auxiliaries.zmq.is_nack(answer):
        _logger.debug("No drone available - sleeping for 2 seconds")
        return (False, "No drone available")
        time.sleep(2.0)
      else:
        drone_received = True

    # Connect to the nth drone, set app_id in socket
    drone_name = "drone"+ str(len(self.drone_dict))
    self.drone_dict[drone_name] = dss.client.Client(timeout=2000, exception_handler=None, context=_context)
    self.drone_dict[drone_name].connect(answer['ip'], answer['port'], app_id=self.crm.app_id)
    _logger.info("Connected as owner of drone: [%s]", self.drone_dict[drone_name]._dss.dss_id)

    # Setup info stream to DSS
    self.setup_dss_info_stream(drone_name)
    return (True, drone_name)

  def task_launch_drone(self, height, drone_name):
    #Initialize drone
    self.drone_dict[drone_name].try_set_init_point()
    self.drone_dict[drone_name].set_geofence(max(2, self.height_min-2), self.height_max+2, self.delta_r_max+10)
    self.drone_dict[drone_name].await_controls()
    self.drone_dict[drone_name].arm_and_takeoff(height)
    self.drone_dict[drone_name].reset_dss_srtl()

  def task_await_init_point(self):
    # Wait until info stream up and running
    while self.alive and not self.start_pos_received:
      _logger.debug("Waiting for start position from drone...")
      time.sleep(1.0)

  def thread_mission_flier(self):
    while self.alive:
        for drone in self.drone_mission:
          if not self.valid_mission(self.drone_mission[drone]):
            _logger.error("Invalid mission for drone %s", drone)
            #TODO: send error to drone manager
            continue
          elif drone not in self.flying_missions:
            self.flying_missions[drone] = threading.Thread(target=self.task_execute_mission, args=(drone), daemon=True)
            self.flying_missions[drone].start()

  #thread to execute mission
  def task_execute_mission(self, drone_name):
    self.drone_dict[drone_name].upload_mission_LLA(self.drone_mission[drone_name])
    time.sleep(0.5)
    # Fly waypoints, allow PILOT intervention.
    start_wp = 0
    #prevent race condition for different threads trying to access mission_complete
    with self.mission_complete_lock:
      self.mission_complete[drone_name] = 'In Progress'
    while True:
      try:
        self.drone_dict[drone_name].fly_waypoints(start_wp)
      except dss.auxiliaries.exception.Nack as nack:
        if nack.msg == 'Not flying':
          with self.mission_complete_lock:
            self.mission_complete[drone_name] = 'Success'
          with self.drone_mission_lock:
            self.mission_list.pop(drone_name)
          _logger.info("Pilot has landed")
        else:
          _logger.info("Fly mission was nacked %s", nack.msg)
          with self.mission_complete_lock:
            self.mission_complete[drone_name] = 'Failed'
          with self.drone_mission_lock:
            self.mission_list.pop(drone_name)
        break
      except dss.auxiliaries.exception.AbortTask:
        # PILOT took controls
        (current_wp, _) = self.drone_dict[drone_name].get_currentWP()
        # Prepare to continue the mission
        start_wp = current_wp
        _logger.info("Pilot took controls, awaiting PILOT action")
        self.drone_dict[drone_name].await_controls()
        _logger.info("PILOT gave back controls")
        # Try to continue mission
        continue
      else:
        # Mission is completed
        with self.mission_complete_lock:
          self.mission_complete[drone_name] = 'Success'
        with self.drone_mission_lock:
            self.mission_list.pop(drone_name)
        break
    #Perform (probably don't want this here) rtl
    self.drone_dict[drone_name].rtl()


  
  def task_execute_random_missions(self, drone_name):
    # Compute number of WPs
    t_wp = self.wp_dist / self.default_speed
    n_wps = int(np.floor(self.t_max/t_wp))
    #Compute random mission
    mission = self.generate_random_mission(n_wps)
    self.drone_dict[drone_name].upload_mission_LLA(mission)
    time.sleep(0.5)
    # Fly waypoints, allow PILOT intervention.
    start_wp = 0
    while True:
      try:
        self.drone_dict[drone_name].fly_waypoints(start_wp)
      except dss.auxiliaries.exception.Nack as nack:
        if nack.msg == 'Not flying':
          _logger.info("Pilot has landed")
        else:
          _logger.info("Fly mission was nacked %s", nack.msg)
        break
      except dss.auxiliaries.exception.AbortTask:
        # PILOT took controls
        (current_wp, _) = self.drone_dict[drone_name].get_currentWP()
        # Prepare to continue the mission
        start_wp = current_wp
        _logger.info("Pilot took controls, awaiting PILOT action")
        self.drone_dict[drone_name].await_controls()
        _logger.info("PILOT gave back controls")
        # Try to continue mission
        continue
      else:
        # Mission is completed
        break
    #Perform rtl
    self.drone_dict[drone_name].rtl()

#--------------------------------------------------------------------#
# Main function
  def main(self):
    # Execute tasks
    self.task_connect_to_drone()
    self.task_launch_drone(self.takeoff_height, str(self.drone_dict.keys()[0]))
    self.task_await_init_point()
    self.task_execute_random_missions(str(self.drone_dict.keys()[0]))


#--------------------------------------------------------------------#
def _main():
  # parse command-line arguments
  parser = argparse.ArgumentParser(description='APP "app_noise"', allow_abbrev=False, add_help=False)
  parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
  parser.add_argument('--app_ip', type=str, help='ip of the app', required=True)
  parser.add_argument('--id', type=str, default=None, help='id of this app_noise instance if started by crm')
  parser.add_argument('--crm', type=str, help='<ip>:<port> of crm', required=True)
  parser.add_argument('--log', type=str, default='debug', help='logging threshold')
  parser.add_argument('--owner', type=str, help='id of the instance controlling app_noise - not used in this use case')
  parser.add_argument('--stdout', action='store_true', help='enables logging to stdout')
  args = parser.parse_args()

  # Identify subnet to sort log files in structure
  subnet = dss.auxiliaries.zmq.get_subnet(ip=args.app_ip)
  # Initiate log file
  dss.auxiliaries.logging.configure('app_noise', stdout=args.stdout, rotating=True, loglevel=args.log, subdir=subnet)

  # Create the AppNoise class
  try:
    app = InteractiveMap(args.app_ip, args.id, args.crm)
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
  _main()
