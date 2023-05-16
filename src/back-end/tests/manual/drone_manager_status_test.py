from IMM.drone_manager.helper_functions import *
from IMM.drone_manager.drone_manager import DroneManager
from utility.helper_functions import create_logger
import time

"""
Manual test that tests communication between the Drone Manager and RISE Drone System, via the Link class.
This test specifically tests that the Drone Manager receives status updates from RISE Drone System.

Hardcoded routes are generated and are set as routes in the drone manager. Currently generates 1 route.
The drone manager is run by calling its run-function where it first connects to RDS and then performs
'resource management' which assigns drones to routes. Then missions are created and uploaded for those 
drones. The test is checked by looking at the printouts for the drone in question. If the status and
location updates as expected, things work as planned.

How to use:

- Make sure code generates 1 route

- Create 1 drone in CRM/web interface (10.44.170.10/tasks)

- Make sure the drone is started in the same area as the route 
  is generated in and that the route doesn't go outside the geofence radius. 
  Double check the geofence settings in the RDS config file (.rise_drone/.config, look for 'app_drone_link')
  Unit is meters.

- Make sure the altitude in waypoints is properly set for the area you are flying in.
  Linköping has around 50-100 m above sea level, Skara around 120 m. The 
  altitude in QGC shows altitude above ground, while the altitude in 
  mission waypoints is altitude above sea level. See dm_config file.

"""

LOGGER_NAME = "drone_manager_status_test"
_logger = create_logger(LOGGER_NAME)

def status_test():
    try:
        alive = True
        NUM_OF_ROUTES = 1
        dummy_route = [generate_dummy_route_skara(offset=i) for i in range(NUM_OF_ROUTES)]

        drone_manager = DroneManager()
        drone_manager.set_routes(dummy_route)
        _logger.debug("attempting to connect drone_manager to RDS")
        drone_manager.run()
        while alive:
            print("sleeping after success")
            time.sleep(7)
    
    except KeyboardInterrupt as e:
        alive = False
        drone_manager.link.kill()
        print("Exit test due to KeyboardInterrupt")
    
    except Exception as e:
        alive = False
        drone_manager.link.kill()
        print(e)
        raise e


if __name__ == "__main__":
    status_test()
