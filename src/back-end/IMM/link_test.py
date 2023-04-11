import link
import time

link_object = link.Link()
alive = True
class Drone():
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
            print("sleeping")
            time.sleep(1)
    except Exception as e:
        print(e)
        print("uhh i died")
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
            print("sleeping")
            time.sleep(1)
    except Exception as e:
        print(e)
        print("uhh i died")
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
            print("sleeping")
            time.sleep(1)
    except Exception as e:
        print(e)
        print("uhh i died")
        link_object.kill()
        alive = False


if __name__ == '__main__':
    try:
        test_link_new_mission()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        link_object.kill()
        alive = False
    