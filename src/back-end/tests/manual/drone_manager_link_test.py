from IMM.drone_manager.helper_functions import generate_dummy_route
from IMM.drone_manager.drone_manager import DroneManager
from utility.helper_functions import create_logger
import time

LOGGER_NAME = "drone_manager_link_test"
_logger = create_logger(LOGGER_NAME)

def test_fly_auto_routes():
    try:
        alive = True
        dummy_routes = [generate_dummy_route(offset=i) for i in range(2)]
        drone_manager = DroneManager()
        drone_manager.set_routes(dummy_routes)
        _logger.debug("attempting to connect drone_manager to RDS")
        drone_manager.connect()
        _logger.debug("attempting to retrieve list of drones")
        drone_manager.drones = drone_manager.get_crm_drones()
        _logger.debug(f"received list of drones: {drone_manager.drones}")
        if drone_manager.drones:
            d1 = drone_manager.drones[0]
            _logger.debug("attempting to retrieve status of first drone")
            status = drone_manager.link.get_drone_status(d1)
            _logger.debug(f"received status of first drone: {status}")
            _logger.debug("attempting to retrieve battery of first drone")
            battery = drone_manager.link.get_drone_battery(d1)
            _logger.debug(f"received battery of first drone: {battery}")
            _logger.debug("attempting to fly random mission with first drone")
            success = drone_manager.link.fly_random_mission(d1)
            _logger.debug(f"apparent {'success' if success else 'failure'} of executing random mission with first drone")
            while alive:
                print("sleeping after success")
                time.sleep(7)
    
    except Exception as e:
        print(e)
        print("uhh i died")
        drone_manager.link.kill()
        alive = False
        


    # while True:
    #     drone_manager.drones = drone_manager.get_crm_drones()
    #     if drone_manager.drones:
    #         print("dm received drones from CRM")
    #         break
    #     else:
    #         print("no drones received from CRM")
    #     time.sleep(3)

    #drone_manager.run()
    
    # generate routes
    # start drone manager thread
    # run it
    # set routes

if __name__ == "__main__":
    test_fly_auto_routes()