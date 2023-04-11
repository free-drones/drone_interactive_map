import link
import time

link_object = link.Link()
alive = True
def test_link():
    try:
        link_object.connect_to_drone()
        link_object.connect_to_drone()
        drone_list = link_object.get_list_of_drones()
        for drone in drone_list:
            link_object.fly_random_mission(drone)
        time.sleep(10)
        for drone in drone_list:
            link_object.fly_random_mission(drone)
        while(alive):
        #for drone in drone_list:
            #link_object.get_mission_status(drone)
            #if link_object.get_mission_status(drone) == 'waiting':
                #print("flying next mission")
                #link_object.fly_random_mission(drone)
            print("sleeping")
            time.sleep(1)
    except Exception as e:
        print("uhh i died")
        link_object.kill()
        alive = False



if __name__ == '__main__':
    try:
        test_link()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        link_object.kill()
        alive = False
    