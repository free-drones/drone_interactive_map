"""
This file tests the database.
"""

import unittest

from random import randint, uniform, seed
from time import sleep
from threading import Thread

from IMM.database.database import Coordinate
from IMM.database.database import UserSession, Client, AreaVertex, Image, PrioImage, Drone
from IMM.database.database import session_scope, use_test_database

from sqlalchemy.exc import IntegrityError

class CoordinateTester(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(Coordinate(1, 1), Coordinate(1, 1))
        self.assertEqual(Coordinate(-1, -1), Coordinate(-1, -1))
        self.assertNotEqual(Coordinate(1, 1), Coordinate(-1, -1))
        self.assertNotEqual(Coordinate(1, -1), Coordinate(-1, 1))
        self.assertNotEqual(Coordinate(1, 1), None)
        self.assertNotEqual(Coordinate(1, 1), self)

    def test_composite_values(self):
        self.assertEqual(Coordinate(1, 5).__composite_values__(), (1, 5))

    def test_eq(self):
        coord = Coordinate(1, 5)
        self.assertTrue(coord.__eq__(coord))
        self.assertTrue(coord.__eq__(Coordinate(1, 5)))
        self.assertFalse(coord.__eq__(Coordinate(10, -2)))
        self.assertFalse(coord.__eq__(Coordinate(1, -2)))
        self.assertFalse(coord.__eq__(Coordinate(2, 5)))
        self.assertFalse(coord.__eq__(None))
        self.assertFalse(coord.__eq__("test"))
        self.assertTrue(coord.__eq__(Coordinate(1, 5.0)))

    def test_ne(self):
        coord = Coordinate(1, 5)
        self.assertFalse(coord.__ne__(coord))
        self.assertFalse(coord.__ne__(Coordinate(1, 5)))
        self.assertTrue(coord.__ne__(Coordinate(10, -2)))
        self.assertTrue(coord.__ne__(Coordinate(1, -2)))
        self.assertTrue(coord.__ne__(Coordinate(2, 5)))
        self.assertTrue(coord.__ne__(None))
        self.assertTrue(coord.__ne__("test"))
        self.assertFalse(coord.__ne__(Coordinate(1, 5.0)))

    def test_repr(self):
        Coordinate(1, 1).__repr__()

class UserSessionTester(unittest.TestCase):

    def setUp(self):
        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()

    def tearDown(self):
        pass

    def test_single_entry(self):
        with session_scope() as session:
            session.add(UserSession(start_time=123, drone_mode="AUTO"))

        with session_scope() as session:
            self.assertEqual(session.query(UserSession).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(UserSession).first().drone_mode, "AUTO",
                "Wrong drone mode retrieved.")
            self.assertEqual(session.query(UserSession.drone_mode).filter(UserSession.end_time == None).scalar(), "AUTO",
                "Wrong drone mode retrieved when filtering.")
            self.assertEqual(session.query(UserSession).filter(UserSession.end_time == 123).count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_sessions = 500

        start_times = [randint(100000, 200000) for i in range(n_sessions)]
        drone_modes = ["AUTO" if randint(0, 1) == 0 else "MAN" for i in range(n_sessions)]
        user_sessions = [UserSession(start_time=start_times[i], drone_mode = drone_modes[i]) for i in range(n_sessions)]
        with session_scope() as session:
            for user_session in user_sessions:
                session.add(user_session)

        with session_scope() as session:
            sessions_in_database = session.query(UserSession).\
                order_by(UserSession.id).all()
            self.assertEqual(len(sessions_in_database), n_sessions,
                "Incorrect number of entries saved in IMM_database.")
            for i in range(n_sessions):
                with self.subTest(i=i):
                    self.assertEqual(start_times[i], sessions_in_database[i].start_time,
                        "Retrieved session has incorrect start time.")
                    self.assertEqual(drone_modes[i], sessions_in_database[i].drone_mode,
                        "Retrieved session has incorrect done mode.")
                    self.assertIsNone(sessions_in_database[i].end_time)
            self.assertEqual(session.query(UserSession).\
                filter(UserSession.end_time != None).count(), 0,
                "Found nonexistant session.")

    def test_repr(self):
        UserSession(start_time=123, drone_mode="MAN").__repr__()

    def test_not_nullable(self):
        def check_invalid(user_session):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(user_session)

        check_invalid(UserSession(start_time=123))
        check_invalid(UserSession(drone_mode="MAN"))

class ClientTester(unittest.TestCase):

    def setUp(self):
        self.SESSIONS = 5

        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()
        with session_scope() as session:
            for _i in range(self.SESSIONS):
                session.add(UserSession(
                    start_time=randint(100000, 200000),
                    end_time=randint(200000, 300000),
                    drone_mode="AUTO"
                ))

    def tearDown(self):
        pass

    def test_single_entry(self):
        client = Client(
            session_id=1,
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        )
        with session_scope() as session:
            session.add(client)

        with session_scope() as session:
            self.assertEqual(session.query(Client).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(Client).first().up_left, Coordinate(1, 5),
                "Wrong view retrieved.")
            self.assertEqual(session.query(Client).filter(Client.up_left == Coordinate(3, 3)).count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_clients = 500

        up_left = [Coordinate(uniform(1, 5), uniform(5, 10)) for i in range(n_clients)]
        up_right = [Coordinate(uniform(5, 10), uniform(5, 10)) for i in range(n_clients)]
        down_right = [Coordinate(uniform(5, 10), uniform(1, 5)) for i in range(n_clients)]
        down_left = [Coordinate(uniform(1, 5), uniform(1, 5)) for i in range(n_clients)]
        sessions = [randint(1, self.SESSIONS) for i in range(n_clients)]
        clients = [Client(
            session_id=sessions[i],
            up_left=up_left[i], up_right=up_right[i],
            down_right=down_right[i], down_left=down_left[i]
        ) for i in range(n_clients)]
        with session_scope() as session:
            for client in clients:
                session.add(client)

        with session_scope() as session:
            clients_in_database = session.query(Client).\
                order_by(Client.id).all()
            self.assertEqual(len(clients_in_database), n_clients,
                "Incorrect number of entries saved in IMM_database.")
            for i in range(n_clients):
                with self.subTest(i=i):
                    self.assertEqual(clients_in_database[i].down_left, down_left[i],
                        "Retrieved session has incorrect down_left coordinate.")
            self.assertEqual(session.query(Client).\
                filter(Client.up_left == Coordinate(0, 0)).count(), 0,
                "Found nonexistant session.")

    def test_repr(self):
        Client(
            session_id=1,
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ).__repr__()

    def test_not_nullable(self):
        def check_invalid(client):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(client)

        up_left = Coordinate(1, 5)
        up_right = Coordinate(5, 5)
        down_right = Coordinate(5, 1)
        down_left = Coordinate(1, 1)
        center = Coordinate(3, 3)
        check_invalid(Client(up_left=up_left, up_right=up_right, down_right=down_right, down_left=down_left, center=center))

    def test_foreign_key(self):
        client = Client(
            session_id=self.SESSIONS + 1,
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        )
        with self.assertRaises(IntegrityError, msg="Foreign key contraint not met."):
            with session_scope() as session:
                session.add(client)


class AreaVertexTester(unittest.TestCase):

    def setUp(self):
        self.SESSIONS = 5

        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()
        with session_scope() as session:
            for _i in range(self.SESSIONS):
                session.add(UserSession(
                    start_time=randint(100000, 200000),
                    end_time=randint(200000, 300000),
                    drone_mode="AUTO"
                ))

    def tearDown(self):
        pass

    def test_single_entry(self):
        vertex = AreaVertex(session_id=randint(1, self.SESSIONS),
            vertex_no=1, coordinate=Coordinate(lat=1.5, long=0.23))
        with session_scope() as session:
            session.add(vertex)

        with session_scope() as session:
            self.assertEqual(session.query(AreaVertex).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(AreaVertex).first().coordinate, Coordinate(1.5, 0.23),
                "Wrong vertex retrieved.")
            self.assertEqual(session.query(AreaVertex).filter(AreaVertex.coordinate == Coordinate(1.5, 0.23)).first().coordinate, Coordinate(1.5, 0.23),
                "Failed to filter by coordinate.")
            self.assertEqual(session.query(AreaVertex).filter(AreaVertex.coordinate == Coordinate(1.5, 1.5)).count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_max_vertices = 100
        n_vertices_for_session = [randint(1, n_max_vertices) for i in range(self.SESSIONS)]
        coordinates = [[Coordinate(uniform(1, 100), uniform(1, 100)) for i in range(j)] for j in n_vertices_for_session]
        vertices = [[AreaVertex(session_id=i+1, vertex_no=j, coordinate=coordinates[i][j]) for j in range(n_vertices_for_session[i])] for i in range(self.SESSIONS)]
        with session_scope() as session:
            for session_vertices in vertices:
                for vertex in session_vertices:
                    session.add(vertex)

        with session_scope() as session:
            n_vertices_in_database = session.query(AreaVertex).\
                order_by(AreaVertex.session_id, AreaVertex.vertex_no).count()
            self.assertEqual(n_vertices_in_database, sum(n_vertices_for_session),
                "Incorrect number of entries saved in database.")
            for session_id in range(self.SESSIONS):
                with self.subTest(i=session_id):
                    session_vertices = session.query(AreaVertex).filter(AreaVertex.session_id == session_id+1).all()
                    self.assertEqual(len(session_vertices), n_vertices_for_session[session_id],
                        "Incorrect number of vertices retrieved for session.")
                    for i in range(n_vertices_for_session[session_id]):
                        with self.subTest(i=i):
                            self.assertEqual(coordinates[session_id][i], session_vertices[i].coordinate,
                                "Retrieved vertex is not the same as created vertex.")
            self.assertEqual(session.query(AreaVertex).\
                filter(AreaVertex.coordinate == Coordinate(-1, -1)).count(), 0,
                "Found nonexistant vertex.")

    def test_repr(self):
        AreaVertex(session_id=1, vertex_no=1, coordinate=Coordinate(1, 1)).__repr__()

    def test_not_nullable(self):
        def check_invalid(vertex):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(vertex)

        coordinate = Coordinate(13.2, 175.4)
        check_invalid(AreaVertex(vertex_no=1, coordinate=coordinate))
        check_invalid(AreaVertex(session_id=1, coordinate=coordinate))
        check_invalid(AreaVertex(session_id=1, vertex_no=1))

    def test_foreign_key(self):

        with self.assertRaises(IntegrityError, msg="Foreign key contraint not met."):
            with session_scope() as session:
                session.add(AreaVertex(
                    session_id=self.SESSIONS + 1,
                    vertex_no=1,
                    coordinate=Coordinate(5, 5)
                ))

class ImageTester(unittest.TestCase):

    def setUp(self):
        self.SESSIONS = 5

        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()
        with session_scope() as session:
            for _i in range(self.SESSIONS):
                session.add(UserSession(
                    start_time=randint(100000, 200000),
                    end_time=randint(200000, 300000),
                    drone_mode="AUTO"
                ))

    def tearDown(self):
        pass

    def test_single_entry(self):
        image = Image(
            session_id=randint(1, self.SESSIONS),
            time_taken=randint(100000, 200000),
            width=480, height=360, type="IR",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3),
            file_name="images/1.jpg"
        )
        with session_scope() as session:
            session.add(image)

        with session_scope() as session:
            self.assertEqual(session.query(Image).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(Image.width).first()[0], 480,
                "Wrong width retrieved.")
            self.assertEqual(session.query(Image).filter(Image.height == 360).first().up_left, Coordinate(1, 5),
                "Failed to filter by coordinate.")
            self.assertEqual(session.query(Image).filter(Image.type == "LASERBEAM").count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_images = 500
        sessions = [randint(1, self.SESSIONS) for i in range(n_images)]
        time_taken = [randint(100000, 200000) for i in range(n_images)]
        width = [randint(100, 1000) for i in range(n_images)]
        height = [randint(100, 1000) for i in range(n_images)]
        type = ["IR" for i in range(n_images)]
        up_left = [Coordinate(uniform(1, 100), uniform(100, 200)) for i in range(n_images)]
        up_right = [Coordinate(uniform(100, 200), uniform(100, 200)) for i in range(n_images)]
        down_right = [Coordinate(uniform(100, 200), uniform(1, 100)) for i in range(n_images)]
        down_left = [Coordinate(uniform(1, 100), uniform(1, 100)) for i in range(n_images)]
        center = [Coordinate(100, 100) for i in range(n_images)]
        file_name = ["{}.jpg".format(i) for i in range(n_images)]

        images = [Image(
            session_id=sessions[i],
            time_taken=time_taken[i],
            width=width[i],
            height=height[i],
            type=type[i],
            up_left=up_left[i],
            up_right=up_right[i],
            down_right=down_right[i],
            down_left=down_left[i],
            center=center[i],
            file_name=file_name[i]
        ) for i in range(n_images)]
        with session_scope() as session:
            for image in images:
                session.add(image)

        with session_scope() as session:
            self.assertEqual(session.query(Image).count(), n_images,
                "Incorrect number of entries saved in database.")
            for session_id in range(self.SESSIONS):
                with self.subTest(i=session_id):
                    n_session_images = session.query(Image).filter(Image.session_id == session_id).count()
                    self.assertEqual(n_session_images, sessions.count(session_id),
                        "Incorrect number of images retrieved for session.")
            images_in_database = session.query(Image).order_by(Image.id).all()
            for i in range(n_images):
                with self.subTest(i=i):
                    self.assertEqual(images_in_database[i].up_left, up_left[i],
                        "Retrieved Image is not the same object as inserted Image.")
            self.assertEqual(session.query(Image).\
                filter(Image.width == 0).count(), 0,
                "Found nonexistant vertex.")

    def test_repr(self):
        Image(
            session_id=1,
            time_taken=123,
            width=100,
            height=200,
            type="IR",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3),
            file_name="1.jpg"
        ).__repr__()

    def test_not_nullable(self):
        def check_invalid(image):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(image)

        check_invalid(Image(
            time_taken=100000,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360,
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360, type="IR",
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_left=Coordinate(1, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            file_name="1.jpg"
        ))
        check_invalid(Image(
            session_id=1, time_taken=100000,
            width=240, height=360, type="IR",
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
        ))

    def test_foreign_key(self):
        with self.assertRaises(IntegrityError, msg="Foreign key contraint not met."):
            with session_scope() as session:
                session.add(Image(
                    session_id=self.SESSIONS+1,
                    time_taken=123,
                    width=100,
                    height=200,
                    type="IR",
                    up_left=Coordinate(1, 5),
                    up_right=Coordinate(5, 5),
                    down_right=Coordinate(5, 1),
                    down_left=Coordinate(1, 1),
                    center=Coordinate(3, 3),
                    file_name="1.jpg"
                ))

class PrioImageTester(unittest.TestCase):

    def setUp(self):
        self.SESSIONS = 5

        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()
        with session_scope() as session:
            for _i in range(self.SESSIONS):
                session.add(UserSession(
                    start_time=randint(100000, 200000),
                    end_time=randint(200000, 300000),
                    drone_mode="AUTO"
                ))

    def tearDown(self):
        pass

    def test_single_entry(self):
        image = PrioImage(
            session_id=randint(1, self.SESSIONS),
            time_requested=randint(100000, 200000),
            status="PENDING", eta=randint(100, 1000),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3),
        )
        with session_scope() as session:
            session.add(image)

        with session_scope() as session:
            self.assertEqual(session.query(PrioImage).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(PrioImage.status).first()[0],
                "PENDING", "Wrong vertex retrieved.")
            self.assertEqual(session.query(PrioImage).\
                filter(PrioImage.status == "PENDING").first().status, "PENDING",
                "Failed to filter by status.")
            self.assertEqual(session.query(PrioImage).\
                filter(PrioImage.time_requested == 0).count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_images = 100
        session_ids = [randint(1, self.SESSIONS) for i in range(n_images)]
        time_requested = [randint(100000, 200000) for i in range(n_images)]
        status = ["CANCELLED" for i in range(n_images)]
        center = [Coordinate(uniform(10, 20), uniform(10, 20)) for i in range(n_images)]
        up_left = [Coordinate(uniform(0, 10), uniform(20, 30)) for i in range(n_images)]
        up_right = [Coordinate(uniform(20, 30), uniform(20, 30)) for i in range(n_images)]
        down_right = [Coordinate(uniform(20, 30), uniform(0, 10)) for i in range(n_images)]
        down_left = [Coordinate(uniform(0, 10), uniform(0, 10)) for i in range(n_images)]
        images = [PrioImage(
            session_id=session_ids[i], time_requested=time_requested[i],
            status=status[i], center=center[i],
            up_left=up_left[i], up_right=up_right[i],
            down_right=down_right[i], down_left=down_left[i]
        ) for i in range(n_images)]
        with session_scope() as session:
            for image in images:
                session.add(image)

        with session_scope() as session:
            n_images_in_database = session.query(PrioImage).order_by(PrioImage.id).count()
            self.assertEqual(n_images_in_database, n_images,
                "Incorrect number of entries saved in database.")
            for session_id in range(self.SESSIONS):
                with self.subTest(i=session_id):
                    n_session_images = session.query(PrioImage).\
                        filter(PrioImage.session_id == session_id).count()
                    self.assertEqual(n_session_images,
                        session_ids.count(session_id),
                        "Incorrect number of images retrieved for session.")
            for i in range(n_images):
                with self.subTest(i=i):
                    self.assertEqual(session.query(PrioImage).\
                        filter(PrioImage.id == i + 1).first().time_requested, time_requested[i],
                        "Retrieved image is not the same object as created image.")
            self.assertEqual(session.query(PrioImage).\
                filter(PrioImage.session_id == self.SESSIONS + 1).count(), 0,
                "Found nonexistant image.")

    def test_repr(self):
        PrioImage(
            session_id=1,
            time_requested=123,
            status="PENDING",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ).__repr__()

    def test_not_nullable(self):
        def check_invalid(image):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(image)

        check_invalid(PrioImage(
            time_requested=150000,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            status="COMPLETE",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_left=Coordinate(1, 1)
        ))
        check_invalid(PrioImage(
            session_id=1,
            time_requested=150000,
            status="COMPLETE",
            center=Coordinate(3, 3),
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1)
        ))

    def test_foreign_key(self):
        def check_invalid(obj):
            with self.assertRaises(IntegrityError, msg="Foreign key contraint not met."):
                with session_scope() as session:
                    session.add(obj)

        with session_scope() as session:
            session.add(Image(
                session_id=1,
                time_taken=123,
                width=100,
                height=200,
                type="IR",
                up_left=Coordinate(1, 5),
                up_right=Coordinate(5, 5),
                down_right=Coordinate(5, 1),
                down_left=Coordinate(1, 1),
                center=Coordinate(3, 3),
                file_name="1.jpg"
            ))

        check_invalid(PrioImage(
            session_id=self.SESSIONS+1,
            time_requested=123,
            status="PENDING",
            eta=123,
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        ))
        check_invalid(PrioImage(
            session_id=1,
            image_id=2,
            time_requested=123,
            status="PENDING",
            eta=123,
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        ))

class DroneTester(unittest.TestCase):

    def setUp(self):
        self.SESSIONS = 5

        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()
        with session_scope() as session:
            for _i in range(self.SESSIONS):
                session.add(UserSession(
                    start_time=randint(100000, 200000),
                    end_time=randint(200000, 300000),
                    drone_mode="AUTO"
                ))

    def tearDown(self):
        pass

    def test_single_entry(self):
        drone = Drone(
            session_id=1,
            id="one",
            last_updated=876,
            time2bingo=randint(100, 1000)
        )
        with session_scope() as session:
            session.add(drone)

        with session_scope() as session:
            self.assertEqual(session.query(Drone).count(), 1,
                "Wrong number of entries.")
            self.assertEqual(session.query(Drone).first().last_updated, 876,
                "Wrong drone retrieved.")
            self.assertEqual(session.query(Drone).\
                filter(Drone.session_id == 1).first().last_updated, 876,
                "Failed to filter by status.")
            self.assertEqual(session.query(Drone).\
                filter(Drone.time2bingo == 2000).count(), 0,
                "Failed to filter by nonexistant property.")

    def test_multiple_unique_entries(self):
        n_drones = 100
        session_ids = [randint(1, self.SESSIONS) for i in range(n_drones)]
        ids = ["one"+str(i) for i in range(n_drones)]
        last_updated = [randint(100000, 200000) for i in range(n_drones)]
        time2bingo = [randint(100, 1000) for i in range(n_drones)]
        drones = [Drone(
            session_id=session_ids[i],
            id=ids[i],
            last_updated=last_updated[i],
            time2bingo=time2bingo[i]
        ) for i in range(n_drones)]
        with session_scope() as session:
            for drone in drones:
                session.add(drone)

        with session_scope() as session:
            n_drones_in_database = session.query(Drone).count()
            self.assertEqual(n_drones_in_database, n_drones,
                "Incorrect number of entries saved in database.")
            for session_id in range(self.SESSIONS):
                with self.subTest(i=session_id):
                    n_session_drones = session.query(Drone).\
                        filter(Drone.session_id == session_id).count()
                    self.assertEqual(n_session_drones,
                        session_ids.count(session_id),
                        "Incorrect number of drones retrieved for session.")
            for i in range(n_drones):
                with self.subTest(i=i):
                    self.assertEqual(session.query(Drone).\
                        filter(Drone.id == ids[i]).first().last_updated, last_updated[i],
                        "Retrieved drone is not the same object as created drone.")
            self.assertEqual(session.query(Drone).\
                filter(Drone.session_id == self.SESSIONS + 1).count(), 0,
                "Found nonexistant drone.")

    def test_repr(self):
        Drone(session_id=1).__repr__()

    def test_not_nullable(self):
        def check_invalid(image):
            with self.assertRaises(IntegrityError, msg="Nullable constraint not met."):
                with session_scope() as session:
                    session.add(image)

        check_invalid(Drone())

    def test_foreign_key(self):
        with self.assertRaises(IntegrityError, msg="Foreign key contraint not met."):
            with session_scope() as session:
                session.add(Drone(session_id=self.SESSIONS + 1))

class RelationTester(unittest.TestCase):
    def setUp(self):
        seed(123)   # Avoid flaky tests by using the same seed every time.
        use_test_database()

    def tearDown(self):
        pass

    def testSessionClientRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        client = Client(
            session_id=user_session.id,
            up_left=Coordinate(1, 5), up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        )
        with session_scope() as session:
            session.add(user_session)
            session.add(client)

        with session_scope() as session:
            self.assertEqual(session.query(Client).first().session.start_time, 100,
                "Wrong session retrieved from client.")
            self.assertEqual(session.query(UserSession).first().clients[0].up_left, Coordinate(1, 5),
                "Wrong client retrieved from session.")

        with session_scope() as session:
            user_session = session.query(UserSession).first()
            user_session.clients.append(Client(
                session_id=user_session.id,
                up_left=Coordinate(3, 5), up_right=Coordinate(5, 5),
                down_right=Coordinate(5, 1), down_left=Coordinate(1, 1),
                center=Coordinate(3, 3)
            ))

        with session_scope() as session:
            self.assertEqual(session.query(Client).count(), 2,
                "Failed to add Client via UserSession.clients.")
            self.assertEqual(len(session.query(UserSession).first().clients), 2,
                "Failed to retrieve all clients from UserSession.clients.")
            retrieved_clients = session.query(Client).order_by(Client.id).all()
            self.assertEqual(retrieved_clients[0].up_left, Coordinate(1, 5))
            self.assertEqual(retrieved_clients[0].session.start_time, 100)
            self.assertEqual(retrieved_clients[1].up_left, Coordinate(3, 5))
            self.assertEqual(retrieved_clients[1].session.start_time, 100)

    def testSessionAreaVertexRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        vertex = AreaVertex(session_id=1, vertex_no=1, coordinate=Coordinate(1, 5))
        with session_scope() as session:
            session.add(user_session)
            session.add(vertex)

        with session_scope() as session:
            self.assertEqual(session.query(AreaVertex).first().session.start_time, 100,
                "Wrong session retrieved from vertex.")
            self.assertEqual(session.query(UserSession).first().area_vertices[0].coordinate, Coordinate(1, 5),
                "Wrong vertex retrieved from session.")

        with session_scope() as session:
            user_session = session.query(UserSession).first()
            user_session.area_vertices.append(AreaVertex(
                session_id=1, vertex_no=2, coordinate=Coordinate(5, 1)
            ))

        with session_scope() as session:
            self.assertEqual(session.query(AreaVertex).count(), 2,
                "Failed to add AreaVertex via UserSession.area_vertices.")
            self.assertEqual(len(session.query(UserSession).first().area_vertices), 2,
                "Failed to retrieve all vertices from UserSession.area_verices.")
            retrieved_vertices = session.query(AreaVertex).order_by(AreaVertex.vertex_no).all()
            self.assertEqual(retrieved_vertices[0].coordinate, Coordinate(1, 5))
            self.assertEqual(retrieved_vertices[0].session.start_time, 100)
            self.assertEqual(retrieved_vertices[1].coordinate, Coordinate(5, 1))
            self.assertEqual(retrieved_vertices[1].session.start_time, 100)

    def testSessionImageRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        image = Image(
            session_id=1,
            time_taken=123,
            width=100,
            height=200,
            type="IR",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3),
            file_name="1.jpg"
        )
        with session_scope() as session:
            session.add(user_session)
            session.add(image)

        with session_scope() as session:
            self.assertEqual(session.query(Image).first().session.start_time, 100,
                "Wrong session retrieved from image.")
            self.assertEqual(session.query(UserSession).first().images[0].time_taken, 123,
                "Wrong image retrieved from session.")

        with session_scope() as session:
            user_session = session.query(UserSession).first()
            user_session.images.append(Image(
                time_taken=234,
                width=100,
                height=200,
                type="IR",
                up_left=Coordinate(1, 5),
                up_right=Coordinate(5, 5),
                down_right=Coordinate(5, 1),
                down_left=Coordinate(1, 1),
                center=Coordinate(3, 3),
                file_name="1.jpg"
            ))

        with session_scope() as session:
            self.assertEqual(session.query(Image).count(), 2,
                "Failed to add Image via UserSession.images.")
            self.assertEqual(len(session.query(UserSession).first().images), 2,
                "Failed to retrieve all images from UserSession.images.")
            retrieved_images = session.query(Image).order_by(Image.id).all()
            self.assertEqual(retrieved_images[0].time_taken, 123)
            self.assertEqual(retrieved_images[0].session.start_time, 100)
            self.assertEqual(retrieved_images[1].time_taken, 234)
            self.assertEqual(retrieved_images[1].session.start_time, 100)

    def testSessionPrioImageRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        prio_image = PrioImage(
            session_id=1,
            time_requested=123,
            status="PENDING",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        )
        with session_scope() as session:
            session.add(user_session)
            session.add(prio_image)

        with session_scope() as session:
            self.assertEqual(session.query(PrioImage).first().session.start_time, 100,
                "Wrong session retrieved from image.")
            self.assertEqual(session.query(UserSession).first().prio_images[0].time_requested, 123,
                "Wrong image retrieved from session.")

        with session_scope() as session:
            user_session = session.query(UserSession).first()
            user_session.prio_images.append(PrioImage(
                time_requested=234,
                status="CANCELLED",
                up_left=Coordinate(1, 5),
                up_right=Coordinate(5, 5),
                down_right=Coordinate(5, 1),
                down_left=Coordinate(1, 1),
                center=Coordinate(3, 3)
            ))

        with session_scope() as session:
            self.assertEqual(session.query(PrioImage).count(), 2,
                "Failed to add PrioImage via UserSession.prio_images.")
            self.assertEqual(len(session.query(UserSession).first().prio_images), 2,
                "Failed to retrieve all images from UserSession.prio_images.")
            retrieved_images = session.query(PrioImage).order_by(PrioImage.id).all()
            self.assertEqual(retrieved_images[0].time_requested, 123)
            self.assertEqual(retrieved_images[0].session.start_time, 100)
            self.assertEqual(retrieved_images[1].time_requested, 234)
            self.assertEqual(retrieved_images[1].session.start_time, 100)

    def testSessionDroneRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        drone = Drone(session_id=1, id="one", last_updated=123)
        with session_scope() as session:
            session.add(user_session)
            session.add(drone)

        with session_scope() as session:
            self.assertEqual(session.query(Drone).first().session.start_time, 100,
                "Wrong session retrieved from drone.")
            self.assertEqual(session.query(UserSession).first().drones[0].session_id, 1,
                "Wrong drone retrieved from session.")

        with session_scope() as session:
            user_session = session.query(UserSession).first()
            user_session.drones.append(Drone(session_id=1, id="two", last_updated=123))

        with session_scope() as session:
            self.assertEqual(session.query(Drone).count(), 2,
                "Failed to add Drone via UserSession.drones.")
            self.assertEqual(len(session.query(UserSession).first().drones), 2,
                "Failed to retrieve all drones from UserSession.drones.")
            retrieved_drones = session.query(Drone).order_by(Drone.id).all()
            self.assertEqual(retrieved_drones[0].last_updated, 123)
            self.assertEqual(retrieved_drones[0].session.start_time, 100)
            self.assertEqual(retrieved_drones[1].last_updated, 123)
            self.assertEqual(retrieved_drones[1].session.start_time, 100)

    def testImagePrioImageRelation(self):
        user_session = UserSession(id=1, start_time=100, end_time=200, drone_mode="AUTO")
        image = Image(
            session_id=1,
            time_taken=234,
            width=100,
            height=200,
            type="IR",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3),
            file_name="1.jpg"
        )
        prio_image = PrioImage(
            session_id=1,
            image_id=1,
            time_requested=123,
            status="PENDING",
            up_left=Coordinate(1, 5),
            up_right=Coordinate(5, 5),
            down_right=Coordinate(5, 1),
            down_left=Coordinate(1, 1),
            center=Coordinate(3, 3)
        )
        with session_scope() as session:
            session.add(user_session)
            session.add(image)
            session.add(prio_image)

        with session_scope() as session:
            self.assertEqual(session.query(PrioImage).first().image.time_taken, 234,
                "Wrong image retrieved from prioimage.")
            self.assertEqual(session.query(Image).first().prio_image.time_requested, 123,
                "Wrong prioimage retrieved from image.")

        with session_scope() as session:
            prio_image = session.query(PrioImage).first()
            session.add(Image(
                session_id=1,
                time_taken=345,
                width=100,
                height=200,
                type="IR",
                up_left=Coordinate(1, 5),
                up_right=Coordinate(5, 5),
                down_right=Coordinate(5, 1),
                down_left=Coordinate(1, 1),
                center=Coordinate(3, 3),
                file_name="1.jpg",
                prio_image=prio_image
            ))

        with session_scope() as session:
            self.assertEqual(session.query(PrioImage).count(), 1,
                "Failed to move PrioImage relation via Image.prio_image.")
            self.assertEqual(session.query(PrioImage).first().image.time_taken, 345,
                "Failed to move PrioImage relation via Image.prio_image.")
            self.assertIsNone(session.query(Image).order_by(Image.id).first().prio_image,
                "Failed to move PrioImage relation via Image.prio_image.")
            self.assertEqual(session.query(Image).filter(Image.id==2).first().prio_image.time_requested, 123,
                "Failed to move PrioImage relation via Image.prio_image.")

class DatabaseConcurrencyTester(unittest.TestCase):

    def insert_sessions(self, n_sessions):
        with session_scope() as session:
            for i in range(n_sessions):
                session.add(UserSession(start_time=i, end_time=i, drone_mode="AUTO"))
                sleep(0.01)
            self.assertEqual(len(session.new), n_sessions,
                "Wrong number of UserSessions added to session.")

        with session_scope() as session:
            self.assertEqual(len(session.new), 0,
                "New UserSessions present after commit")

    def setUp(self):
        use_test_database(in_memory=False)

    def tearDown(self):
        pass

    def run_threads(self, func, n_threads):
        results = [None for i in range(n_threads)]

        def wrapper(i):
            nonlocal results
            try:
                func()
            except Exception as e:
                results[i] = e

        threads = [Thread(target=lambda: wrapper(i)) for i in range(n_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return results

    def test_concurrency(self):
        n_threads = 10
        n_sessions_per_thread = 10
        results = self.run_threads(lambda: self.insert_sessions(n_sessions_per_thread), n_threads)
        for res in results:
            self.assertIsNone(res)
        with session_scope() as session:
            self.assertEqual(session.query(UserSession).count(), n_threads * n_sessions_per_thread,
                "Incorrect number of sessions commited to database")

if __name__ == "__main__":
    unittest.main()
