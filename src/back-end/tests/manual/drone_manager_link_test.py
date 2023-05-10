from IMM.drone_manager.helper_functions import *
from IMM.drone_manager.drone_manager import DroneManager
from utility.helper_functions import create_logger
import time

"""
Manual test that tests communication between the Drone Manager and RISE Drone System, via the Link class.

Hardcoded routes are generated and are set as routes in the drone manager. Currently generates 2 routes.
The drone manager is run by calling its run-function where it first connects to RDS and then performs
'resource management' which assigns drones to routes. Then missions are created and uploaded for those 
drones.

How to use:

- Make sure code generates N routes

- Create N or more drones in CRM/web interface (10.44.170.10/tasks)

- Make sure the drones are started in the same area as the routes 
  are generated in and that routes do not go outside the geofence radius. 
  Double check the geofence settings in the RDS config file (.rise_drone/.config, look for 'app_drone_link')
  Unit is meters.

- Make sure the altitude in waypoints is properly set for the area you are flying in.
  Linköping has around 40 m above sea level, Skara around 120 m. The 
  altitude in QGC shows altitude above ground, while the altitude in 
  mission waypoints is altitude above sea level. See dm_config file.

"""




LOGGER_NAME = "drone_manager_link_test"
_logger = create_logger(LOGGER_NAME)

def test_fly_auto_routes():
    """ See docstring for the whole file for details """
    try:
        alive = True
        NUM_OF_ROUTES = 2
        # dummy_routes = [generate_dummy_route(offset=i) for i in range(2)]
        dummy_routes = [generate_dummy_route_skara(offset=i) for i in range(NUM_OF_ROUTES)]
        # dummy_routes = [generate_long_dummy_route()]

        drone_manager = DroneManager()
        drone_manager.set_routes(dummy_routes)
        _logger.debug("attempting to connect drone_manager to RDS")
        drone_manager.run()
        while alive:
            print("sleeping after success")
            time.sleep(7)
    
    except Exception as e:
        print(e)
        print("uhh i died")
        drone_manager.link.kill()
        alive = False
        raise e

if __name__ == "__main__":
    test_fly_auto_routes()