"""
This file tests the integration between the database and back-end.

It specifially checks that back-end can successfully add new objects into the
database which can later be retrieved.
"""
import unittest
import json, os

from RDS_emulator.RDS_app import RDSThreadHandler
from utility.helper_functions import get_path_from_root
from IMM.IMM_app import *
import IMM.database.database as dbx

example_coordinates =  {"up_left": { "lat": 59.0, "long": 16.0 },
                        "up_right": { "lat": 58.0, "long": 16.0 },
                        "down_left": { "lat": 58.0, "long": 16.0 },
                        "down_right": {"lat": 58.0, "long": 16.0},
                        "center": { "lat": 58.0, "long": 16.0}}

def connect_to_backend(self_unittest):
    client = socketio.test_client(app)
    self_unittest.assertTrue(client.is_connected())
    client.emit("init_connection", {})
    recieved = client.get_received()
    self_unittest.assertEqual({"fcn":"ack","fcn_name":"connect", "arg":{"client_id":1}}, recieved[0]["args"][0])
    return client

class TestFlask(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        dbx.use_test_database(False)

    def tearDown(self):
        pass


    def test_connect_one_user(self):
        """Test for one user"""
        clients = connect_to_backend(self)

        # Check database
        with session_scope() as session:
            all_usersessions = session.query(UserSession).all()

            self.assertEqual(len(all_usersessions), 1)
            self.assertEqual(all_usersessions[0].id, 1)

            all_clients = session.query(Client).all()

            self.assertEqual(len(all_clients), 1)
            self.assertEqual(all_clients[0].id, 1)

    def test_connect_several_users(self):
        clients = connect_to_backend(self)

        # Add 8 clients
        clients_connected = []
        number_of_clients = 10
        for i in range(2, 10):  # 2,3,...,9,10.
            # Let another client be created.
            clients.emit("init_connection", {})
            recieved = clients.get_received()
            self.assertEqual(i, recieved[0]["args"][0]["arg"]["client_id"])
            clients_connected.append(recieved[0]["args"][0]["arg"]["client_id"])


        with session_scope() as session:
            all_usersessions = session.query(UserSession).all()

            self.assertEqual(len(all_usersessions), 1)
            self.assertEqual(all_usersessions[0].id, 1)

            all_clients = session.query(Client).all()

            self.assertEqual(len(all_clients), 9)
            for i in range(9):
                self.assertEqual(all_clients[i].id, i+1)

    def test_request_priority_view(self):
        clients = connect_to_backend(self)

        data = {"arg":
                    {
                        "coordinates": example_coordinates,
                        "client_id": 1,
                        "type" : "RGB"
                    }
               }

        clients.emit("request_priority_view", data)
        recieved = clients.get_received()
        self.assertEqual({"fcn":"ack", "fcn_name":"request_priority_view", "arg":{"force_que_id":1}}, recieved[0]["args"][0])

        with session_scope() as session:
            all_prioimage = session.query(PrioImage).all()

            self.assertEqual(len(all_prioimage), 1)
            self.assertEqual(all_prioimage[0].id, 1)

        # Add 8 prioImage
        for i in range(2,10):
            clients.emit("request_priority_view", data)
            recieved = clients.get_received()
            self.assertEqual(i, recieved[0]["args"][0]["arg"]["force_que_id"])

        with session_scope() as session:
            all_prioimage = session.query(PrioImage).all()

            self.assertEqual(len(all_prioimage), 9)
            for i in range(9):
                self.assertEqual(all_prioimage[i].id, i+1)


if __name__ == "__main__":
    unittest.main()
