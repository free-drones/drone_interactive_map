from IMM.drone_manager.link import Link
import time
import threading
import queue
'''
This is a test script for the link module. It is not intended to be run as a part of the main program.
To run this test, first the crm needs to have simulated drones running. Then start qgroundcontrol and connect to the simulated drones. 
This will be done by setting the folowing information in "connections" in qgroundcontrol 
tcp/ip with ip 10.44.170.10 and the port will be the mavproxy process port that is not taken by the dss, 
you can find this information on c2m2 (in a webbrowser type 10.44.170.10 when connected to openvpn). 
When this is done and you are connected to the drones, set them to guided mode in qgroundcontrol.
After that ssh in to the RISE server (for us it is at 10.44.170.10 with openvpn running) and run app_drone_link, then run this script.
'''
STATUS_TEST = True
MONITOR_TEST = False
link_object = Link()
alive = True
event_queue = queue.Queue()
update_recieved_event = threading.Event()

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

def status_printer():
    alive = True
    while alive:
        try:
            #print('trying to get status update')
            msg = link_object.msg_queue.get()
            #print(f'got status update: {msg}')
            if msg is not None:
                if msg['topic'] =='drone_status':
                    #print(f'topic is drone_status, trying to get data')
                    data = msg['data']
                    print(f'Recieved drone status update with the data being: {data}')
                    if data['drone_status'] == 'waiting':
                        event_queue.put({'drone':data['drone'], 'update':'status_update', 'drone_status':data['drone_status']})
                        update_recieved_event.set()
                        print(f'update recieved: {update_recieved_event.is_set()}')
                        #print('mission done')
                elif msg['topic'] == 'lost_drone':
                    print(f'topic is lost_drone, trying to get data')
                    data = msg['data']
                    print(f'Recieved drone status update with the data being: {data}')
                    event_queue.put({'drone':data['drone'], 'update':'lost_drone'})
                    update_recieved_event.set()
                elif msg['topic'] == 'gained_drone':
                    print(f'topic is new_drone, trying to get data')
                    data = msg['data']
                    print(f'Recieved drone status update with the data being: {data}')
                    event_queue.put({'drone':data['drone'], 'update':'gained_drone'})
                    update_recieved_event.set()
            while update_recieved_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            alive = False
        except Exception as e:
            print(e)
            pass

def update_logic_test():
    alive = True
    while alive:
        try:
            link_object.connect_to_all_drones()
            drone_list = link_object.get_list_of_drones()
            drone_object_list = {}
            for drone in drone_list:
                drone_object_list[drone] = Drone(drone)
            for drone in drone_object_list:
                link_object.fly_random_mission(drone_object_list[drone])
                print('mission started')
            try:
                while True:
                    if update_recieved_event.is_set():
                        update = event_queue.get()
                        update_recieved_event.clear()
                        print(f'update recieved: {update}')
                        if update['update'] == 'status_update':
                            if update['drone_status'] == 'waiting':
                                print(f'mission done for drone: {update["drone"]}')
                                link_object.fly_random_mission(drone_object_list[update["drone"]])
                                print(f'mission started again for drone: {update["drone"]}')
                        elif update['update'] == 'lost_drone':
                            print(f'drone lost: {update["drone"]}')
                            print(f'old drone list: {drone_object_list}')
                            drone_object_list.pop(update['drone'])
                            print(f'new drone list: {drone_object_list}')
                        elif update['update'] == 'gained_drone':
                            if link_object.connect_to_drone():
                                new_drone_list = link_object.get_list_of_drones()
                                for drone in new_drone_list:
                                    if drone not in drone_object_list:
                                        print(f'old drone list: {drone_object_list}')
                                        drone_object_list[drone] = Drone(drone)
                                        link_object.fly_random_mission(drone_object_list[drone])
                                        print(f'mission started for new drone: {drone}')
                                print(f'new drone list: {drone_object_list}')
                    else:
                        print('Bussiness as usual')
                        time.sleep(1)
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                link_object.kill()
                alive = False
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            link_object.kill()
            alive = False
        except Exception as e:
            print(e)
            print("uhh i died")
            link_object.kill()
            alive = False


if __name__ == '__main__':
    try:
        if STATUS_TEST:
            print('Starting status test thread')
            status_test_thread = threading.Thread(target=status_printer, daemon=True)
            status_test_thread.start()
        update_logic_test()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        link_object.kill()
        alive = False
    