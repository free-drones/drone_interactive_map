from IMM.drone_manager.link import Link
import time
from utility.helper_functions import create_logger
'''
This is a test script for the link module. It is not intended to be run as a part of the main program.
To run this test, first the crm needs to have simulated drones running. Then start qgroundcontrol and connect to the simulated drones. 
This will be done by setting the folowing information in "connections" in qgroundcontrol 
tcp/ip with ip 10.44.170.10 and the port will be the mavproxy process port that is not taken by the dss, 
you can find this information on c2m2 (in a webbrowser type 10.44.170.10 when connected to openvpn). 
When this is done and you are connected to the drones, set them to guided mode in qgroundcontrol.
After that ssh in to the RISE server (for us it is at 10.44.170.10 with openvpn running) and run app_drone_link, then run this script.
'''

link_object = Link()
alive = True
_logger = create_logger("link_test")
class Drone:
    def __init__(self, drone_name) -> None:
        self.id = drone_name
        

def test_link_two_drone():
    try:
        link_object.connect_to_drone()
        link_object.connect_to_drone()
        drone_list = link_object.get_list_of_drones()
        drone_object_list = []
        alive = True
        for drone in drone_list:
            drone_object_list.append(Drone(drone))
        for drone in drone_object_list:
            link_object.fly_random_mission(drone)
        time.sleep(10)
        for drone in drone_object_list:
            link_object.fly_random_mission(drone)
        while(alive):
            _logger.info("sleeping")
            time.sleep(1)
    except Exception as e:
        _logger.info(e)
        link_object.kill()
        alive = False

def test_link_all_drones():
    try:
        link_object.connect_to_all_drones()
        drone_list = link_object.get_list_of_drones()
        drone_object_list = []
        alive = True
        for drone in drone_list:
            drone_object_list.append(Drone(drone))
        for drone in drone_object_list:
            link_object.fly_random_mission(drone)
        time.sleep(10)
        for drone in drone_object_list:
            link_object.fly_random_mission(drone)
        while(alive):
            _logger.info("sleeping")
            time.sleep(1)
    except Exception as e:
        _logger.info(e)
        link_object.kill()
        alive = False

def test_link_new_mission():
    try:
        link_object.connect_to_all_drones()
        drone_list = link_object.get_list_of_drones()
        drone_object_list = []
        alive = True
        for drone in drone_list:
            drone_object_list.append(Drone(drone))
        for drone in drone_object_list:
            link_object.fly_random_mission(drone, 4)
        time.sleep(10)
        for drone in drone_object_list:
            link_object.fly_random_mission(drone, 8)
        while(alive):
            _logger.info("sleeping")
            time.sleep(1)
    except Exception as e:
        _logger.info(e)
        link_object.kill()
        alive = False


if __name__ == '__main__':
    try:
        test_link_new_mission()
    except KeyboardInterrupt:
        _logger.info('KeyboardInterrupt')
        link_object.kill()
        alive = False
    