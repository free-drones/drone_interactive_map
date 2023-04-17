import unittest
from IMM.drone_manager.mission import Mission
from IMM.drone_manager.route import Route
from IMM.drone_manager.node import Node
from IMM.drone_manager.drone import Drone
from IMM.drone_manager.drone_manager import DroneManager
from IMM.drone_manager.helper_functions import generate_dummy_route
import os

FULL_CHARGE_LEVEL = 95

# Use mockup RDS link
os.environ["LINK_MOCKUP"] = "True"

class TestHelper(unittest.TestCase):
    def setUp(self):
        self.drone_manager = DroneManager()
        self.drone1, self.drone2, self.drone3 = Drone("drone1"), Drone("drone2"), Drone("drone3")
        self.drone_manager.drones = [self.drone1, self.drone2, self.drone3]
        self.drone_manager.link = _LinkDummy()
        self.r1, self.r2 = generate_dummy_route(offset=0), generate_dummy_route(offset=1)
        self.drone_manager.routes = [self.r1, self.r2]

    def tearDown(self):
        pass

    def test_mission_conversion(self):
        """
        Creates a mission with a route and checks that the convertion to a Rise Drone System-style mission dictionary is correct
        """
        route = generate_dummy_route()
        mission = Mission(route)
        mission_dict = mission.as_mission_dict()
        correct_mission_dict = {
            "id0" : { "lat" : 58.407910, "lon": 15.596624, "alt": 1, "alt_type": "amsl", "heading": "course" },
            "id1" : { "lat" : 58.408582, "lon": 15.596526, "alt": 1, "alt_type": "amsl", "heading": "course" },
            "id2" : { "lat" : 58.408631, "lon": 15.597775, "alt": 1, "alt_type": "amsl", "heading": "course" },
            "id3" : { "lat" : 58.407848, "lon": 15.597987, "alt": 1, "alt_type": "amsl", "heading": "course" },
        }
        
        self.assertEqual(mission_dict, correct_mission_dict)
    
    def test_resource_management(self):
        """
        Tests resource managements ability to handle the reallocation of routes needed when batteries run out/gets charged
        """
        self.drone_manager.resource_management()

        self.assertEqual(self.r1.drone, self.drone1)
        self.assertEqual(self.r2.drone, self.drone2)
        self.assertEqual(self.drone1.route, self.r1)
        self.assertEqual(self.drone2.route, self.r2)
        
        self.assertEqual(self.drone_manager.link.drone_statuses["drone1"]["status"], "idle")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone2"]["status"], "idle")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone3"]["status"], "charging")
        self.assertIsNone(self.drone3.route)

        # 100 100 0 Battery levels
        self.drone_manager.link.dummy_charge()
        # 92 70 20 Battery levels
        self.drone_manager.resource_management()
        self.drone_manager.link.dummy_charge()
        # 84 40 40 Battery levels
        self.drone_manager.resource_management()
        self.drone_manager.link.dummy_charge()
        # 76 20 60 Battery levels
        self.drone_manager.resource_management()
        self.drone_manager.link.dummy_charge()
        # 68 0 80 Battery levels
        self.drone_manager.resource_management()
        self.assertEqual(self.drone_manager.link.drone_statuses["drone1"]["status"], "idle")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone2"]["status"], "charging")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone3"]["status"], "charging")

        self.assertEqual(self.r1.drone, self.drone1)
        self.assertEqual(self.drone1.route, self.r1)
        
        self.assertIsNone(self.r2.drone)
        self.assertIsNone(self.drone2.route)

        self.drone_manager.link.dummy_charge()
        # 60 -20 100 Battery levels
        self.drone_manager.resource_management()

        self.assertEqual(self.drone_manager.link.drone_statuses["drone1"]["status"], "idle")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone2"]["status"], "charging")
        self.assertEqual(self.drone_manager.link.drone_statuses["drone3"]["status"], "idle")
        
        self.assertEqual(self.r1.drone, self.drone1)
        self.assertEqual(self.drone1.route, self.r1)

        self.assertEqual(self.r2.drone, self.drone3)
        self.assertEqual(self.drone3.route, self.r2)
        


    def test_assign_missions(self):
        """ 
        Tests the method DroneManager.assign_missions. Creates two drones and two routes, assigns 
        them to each other and calls the assign_missions method to create and assign/execute missions for each route-drone pair.
        """
        
        for i, route in enumerate(self.drone_manager.routes):
            route.drone = self.drone_manager.drones[i]
            self.drone_manager.drones[i].route = route

        self.drone_manager.assign_missions()

        self.assertEqual(self.r1.drone, self.drone1)
        self.assertEqual(self.r2.drone, self.drone2)

        self.assertIsInstance(self.r1.drone.current_mission, Mission)
        self.assertIsInstance(self.r2.drone.current_mission, Mission)

        self.assertEqual(self.r1.drone.current_mission.route, self.r1)
        self.assertEqual(self.r2.drone.current_mission.route, self.r2)


class _LinkDummy():
    def __init__(self):
        self.drone_statuses = {
            "drone1": {
                    "status": "idle",
                    "battery": 100
            },
            "drone2": {
                    "status": "idle",
                    "battery": 100
            },
            "drone3": {
                    "status": "idle",
                    "battery": 0
            },
        }

    def get_drone_status(self, drone):
        return self.drone_statuses[drone.id]["status"]
    
    def fly(self, mission, drone):
        return True
    
    def get_drone_position(self, drone):        
        return {"lat": 58, "lon": 16, "alt": "amsl", "heading": "course"}

    def get_drone_battery(self, drone):
        return self.drone_statuses[drone.id]["battery"]

    def return_to_home(self, drone):
        self.drone_statuses[drone.id]["status"] = "charging"
    
    def dummy_charge(self):
        self.drone_statuses["drone1"]["battery"] -= 8
        self.drone_statuses["drone2"]["battery"] -= 30
        self.drone_statuses["drone3"]["battery"] += 20
        for drone in ["drone1", "drone2", "drone3"]:
            if self.drone_statuses[drone]["battery"] > FULL_CHARGE_LEVEL:
                self.drone_statuses[drone]["status"] = "idle"
        

if __name__ == "__main__":
    unittest.main()