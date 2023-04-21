"""
This file tests the communication with the GUI.
"""

import unittest
import json, os

from RDS_emulator.RDS_app import RDSThreadHandler
from utility.helper_functions import get_path_from_root
from IMM.IMM_app import *
import IMM.database.database as dbx


example_coordinates =  {"up_left":
                            {
                                "lat": 59.0,
                                "long": 16.0
                            },
                        "up_right":
                            {
                                "lat": 58.0,
                                "long": 16.0
                            },
                        "down_left":
                            {
                                "lat": 58.0,
                                "long": 16.0
                            },
                        "down_right":
                            {"lat": 58.0,
                             "long": 16.0
                             },
                        "center":
                            {
                                "lat": 58.0,
                                "long": 16.0
                            }
                        }


class TestFlask(unittest.TestCase):
    def setUp(self):
        """Settings that can be enabled/disabled"""
        dbx.use_test_database(False)
        self.app = app.test_client()
        pass

    def tearDown(self):
        """Settings that can be enabled/disabled"""
        pass


    def test_connect(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])


    def test_check_alive(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("check_alive", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"check_alive"}, recieved[0]["args"][0])

    def test_quit(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("quit", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"quit"}, recieved[0]["args"][0])

    def test_set_area(self):
        data = {"arg":{"client_id":1, "coordinates": [{"lat":58.39933088094993,"long":15.57485264561767}, 
                                                      {"lat":58.399332989149435, "long":15.575615734071752}, 
                                                      {"lat":58.3999071174593,"long":15.574849963405917},
                                                      {"lat":58.399911333789255,"long":15.575615734068975} ]}}
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        client.emit("set_area", data)
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"set_area"}, recieved[0]["args"][0])

    def test_request_view(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])
#        [(5,0),(5,5),(10,5),(10,0)]
        data = {
                "arg" : {   "type":"RGB",
                            "coordinates": {
                                             "down_left": {
                                                            "long": 5.0,
                                                            "lat": 0.0,
                                                          },

                                              "up_left": {
                                                            "long": 5.0,
                                                            "lat": 5.0
                                                         },

                                              "up_right": {
                                                            "long": 10.0,
                                                            "lat": 5.0
                                                          },

                                              "down_right": {
                                                            "long": 10.0,
                                                            "lat": 0.0
                                                            },
                                              "center": {
                                                        "long" :7.5,
                                                        "lat":7.5
                                                        }
                                           },
                            "client_id" : 1
                       }
                }

        # adding images that overlapp with coordinates obove.ax
        with dbx.session_scope() as session:
            new_image1 = dbx.Image(
                        id=111,
                        session_id=1,
                        time_taken=6,
                        width=480, height=360, type="RGB",
                        up_left=Coordinate(lat=10.0, long=0.0),
                        up_right=Coordinate(lat=10.0, long=10.0),
                        down_right=Coordinate(lat=0.0, long=10.0),
                        down_left=Coordinate(lat=0.0, long=0.0),
                        center=Coordinate(lat=5.0, long=5.0),
                        file_name="images/2.jpg"
                    )
            #[(10,-5), (10,2), (16,-5), (16,2)]
            new_image2 = dbx.Image(
                        id = 222,
                        session_id=1,
                        time_taken=6,
                        width=480, height=360, type="RGB",
                        up_left=Coordinate(lat=2.0, long=10.0),
                        up_right=Coordinate(lat=-5.0, long=16.0),
                        down_right=Coordinate(lat=2.0, long=16.0),
                        down_left=Coordinate(lat=-5.0, long=10.0),
                        center=Coordinate(lat=-1.5, long=13),
                        file_name="images/2.jpg"
                    )
            #[(15,0),(15,5),(20,5),(20,0)]
            new_image3 = dbx.Image(
                        id = 333,
                        session_id=1,
                        time_taken=6,
                        width=480, height=360, type="RGB",
                        up_left=Coordinate(lat=5.0, long=15.0),
                        up_right=Coordinate(lat=5.0, long=20.0),
                        down_right=Coordinate(lat=0.0, long=20.0),
                        down_left=Coordinate(lat=-0.0, long=15.0),
                        center=Coordinate(lat=-1.5, long=13.0),
                        file_name="images/2.jpg"
                    )

            new_image4 = dbx.Image(
                        id = 444,
                        session_id=1,
                        time_taken=6,
                        width=480, height=360, type="IR",
                        up_left=Coordinate(lat=2.0, long=10.0),
                        up_right=Coordinate(lat=-5.0, long=16.0),
                        down_right=Coordinate(lat=2.0, long=16.0),
                        down_left=Coordinate(lat=-5.0, long=10.0),
                        center=Coordinate(lat=-1.5, long=13),
                        file_name="images/2.jpg"
                    )

            new_image5 = dbx.Image(
                        id=555,
                        session_id=1,
                        time_taken=6,
                        width=480, height=360, type="IR",
                        up_left=Coordinate(lat=10.0, long=0.0),
                        up_right=Coordinate(lat=10.0, long=10.0),
                        down_right=Coordinate(lat=0.0, long=10.0),
                        down_left=Coordinate(lat=0.0, long=0.0),
                        center=Coordinate(lat=5.0, long=5.0),
                        file_name="images/2.jpg"
                    )

            session.add(new_image1)
            session.add(new_image2)
            session.add(new_image3)
            session.add(new_image4)
            session.add(new_image5)
            session.commit()

        client.emit("request_view", data)
        recieved = client.get_received()
        self.assertEqual(len(recieved[0]["args"][0]["arg"]["image_data"]), 2)
        self.assertEqual(recieved[0]["args"][0]["arg"]["image_data"][0]["image_id"], 111)
        self.assertEqual(recieved[0]["args"][0]["arg"]["image_data"][1]["image_id"], 222)

        data["arg"]["type"] = "IR"
        client.emit("request_view", data)
        recieved = client.get_received()
        self.assertEqual(len(recieved[0]["args"][0]["arg"]["image_data"]), 2)
        self.assertEqual(recieved[0]["args"][0]["arg"]["image_data"][0]["image_id"], 444)
        self.assertEqual(recieved[0]["args"][0]["arg"]["image_data"][1]["image_id"], 555)


    def test_request_priority_view(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        data = {"arg":
                    {
                        "coordinates": example_coordinates,
                        "client_id": 1,
                        "type" : "RGB"
                    }
               }

        client.emit("request_priority_view", data)
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"request_priority_view", "arg":{"force_que_id":1}}, recieved[0]["args"][0])

        data = {"arg":
                    {
                        "coordinates": example_coordinates,
                        "client_id": 1,
                        "type" : "RGB"
                    }
               }

        client.emit("request_priority_view", data)
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"request_priority_view", "arg":{"force_que_id":2}}, recieved[0]["args"][0])

    def test_clear_queue(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        with dbx.session_scope() as session:
            priority_image = dbx.PrioImage(
                session_id=1,
                time_requested=int(time.time()),
                status="PENDING",
                up_left=dbx.Coordinate(1.0, 5.0),
                up_right=dbx.Coordinate(5.0, 5.0),
                down_right=dbx.Coordinate(5.0, 1.0),
                down_left=dbx.Coordinate(1.0, 1.0),
                center=dbx.Coordinate(3.0, 3.0)
                )

            session.add(priority_image)
            session.commit()

        with dbx.session_scope() as session:
            self.assertEqual(session.query(dbx.PrioImage).first().status, "PENDING")

        client.emit("clear_que", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"clear_que"}, recieved[0]["args"][0])

        with dbx.session_scope() as session:
            self.assertEqual(session.query(dbx.PrioImage).first().status, "CANCELLED")

    def test_set_mode(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        data = {"arg":{"mode": "MAN", "zoom":example_coordinates}}
        client.emit("set_mode", data)
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"set_mode"}, recieved[0]["args"][0])


    def test_get_info(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        with dbx.session_scope() as session:
            drone = Drone(
                id="one",
                session_id=1,
                last_updated=876,
                time2bingo = 20
            )
            session.add(drone)

        client.emit("get_info", {})
        recieved = client.get_received()

        self.assertEqual({"fcn":"ack", "fcn_name":"get_info", "arg":{"data":[{"drone-id": "one","time2bingo":20}]}}, recieved[0]["args"][0])

        with dbx.session_scope() as session:
            drone = Drone(
                session_id=1,
                id="two",
                last_updated=2121,
                time2bingo = 11
            )
            session.add(drone)

        client.emit("get_info", {})
        recieved = client.get_received()

        self.assertEqual({"fcn":"ack", "fcn_name":"get_info", "arg":{"data":[{"drone-id":"one","time2bingo":20}, {"drone-id":"two","time2bingo":11}]}}, recieved[0]["args"][0])

    def test_que_ETA(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])

        with dbx.session_scope() as session:
            image = PrioImage(
                session_id=1,
                time_requested=123,
                status="PENDING",
                eta=2121,
                up_left=Coordinate(1.0, 5.0),
                up_right=Coordinate(5.0, 5.0),
                down_right=Coordinate(5.0, 1.0),
                down_left=Coordinate(-1.0, 1.0),
                center=Coordinate(3.0, 3.0)
            )
            session.add(image)

        client.emit("que_ETA", {})
        recieved = client.get_received()
        self.assertEqual(2121, recieved[0]["args"][0]["arg"]["ETA"])


    def test_send_to_gui(self):
        client = socketio.test_client(app)
        self.assertTrue(client.is_connected())
        client.emit("init_connection", {})
        recieved = client.get_received()
        client_id = recieved[0]["args"][0]["arg"]["client_id"]

        thread_handler.get_gui_pub_thread().send_to_gui("hello world")
        recieved = client.get_received()
        self.assertEqual(recieved[0]["args"][0], "hello world")

        thread_handler.get_gui_pub_thread().send_to_gui("hello world1", client_id)
        recieved = client.get_received()
        self.assertEqual("hello world1", recieved[0]["args"][0])

        # Perform some tests to check so the system is still working.
        with dbx.session_scope() as session:
            drone = Drone(
                id="one",
                session_id=1,
                last_updated=876,
                time2bingo = 20
            )
            session.add(drone)
            session.commit()

        client.emit("get_info", {})
        recieved = client.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"get_info", "arg":{"data":[{"drone-id":"one","time2bingo":20}]}}, recieved[0]["args"][0])


if __name__ == "__main__":
    unittest.main()
