import link


def test_link():
    link_object = link.Link()
    link_object.connect_to_drone()
    link_object.connect_to_drone()
    drone_list = link_object.list_drones()
    for drone in drone_list:
        link_object.fly_random_mission(drone)



if __name__ == '__main__':
    test_link()