"""
This file contains all the threads that are used for the RDS simulation.
"""

import platform
import numpy
import os, cv2
from RDS_emulator.database import RDSImage, rds_session_scope
from threading import Thread, Semaphore
from PIL import Image as PIL_image
import time
import json
import zmq

context = zmq.Context()


class DroneThread(Thread):
    """
    Simulates a drone flying for FLYING_TIME seconds and then takes an image.
    """

    def __init__(self):
        """
        Initializes the thread.
        """
        super().__init__()
        self.image_queue = []
        self.FLYING_TIME = 2
        self.count = 0
        self.new_image = False
        self.running = True
        self.mode = "MAN"
        self.stuff_is_changing = False

    def run(self):
        """
        Runs the threads.
        """
        while self.running:
            if not self.new_image and len(self.image_queue) > 0:
                self.countdown() # Simulate drone flying to location
                # print("Image arrived")
                self.new_image = True
            else:
                time.sleep(.1)

    def add_image_to_queue(self, image):
        """
        Adds an image to the queue.

        Keyword arguments:
        image -- An instance of the image from the rds database to be added to the queue.

        """
        self.image_queue.append(image)

    def pop_first_image(self):
        """
        Pops the first image in the queue.

        Returns the popped image.

        """
        self.new_image = False
        return self.image_queue.pop(0)

    def has_new_image(self):
        """Checks if drone thread has a new image.

        Returns a boolean.

        """

        return self.new_image

    def countdown(self):
        """
        Counts down for FLYING_TIME seconds. This simulates the drone flying to a location before taking an image.
        """

        self.count = self.FLYING_TIME
        while self.count > 0:
            time.sleep(1)
            self.count -= 1

    def next_image_eta(self):
        """
        Returns how many seconds there are left until the next image will be sent.
        """

        return self.count

    def stop(self):
        """
        Stops the thread, used for debugging.
        """

        self.running = False

    def set_mode(self, mode):
        """
        Sets the mode of the drone-thread.

        Keyword arguments:
        mode -- The mode to be set represented by a string.
        """
        self.mode = mode

    def get_mode(self):
        """
        Returns what mode the drone thread are in (AUTO or MAN).
        """
        return self.mode

    def start_change(self):
        self.stuff_is_changing = True

    def stop_change(self):
        self.stuff_is_changing = False

    def is_changing(self):
        return self.stuff_is_changing


class IMMPubThread(Thread):
    """
    Simulates RDS Publish link
    """

    def __init__(self, socket_url, drone):
        """
        Initializes the thread.

        Keyword arguments:
        socket_url -- The url of the socket the thread will bind to through zeroMQ.
                      This is the socket thread_rds_sub will connect to to listen for new images during testing.
        drone -- Instance of the drone-thread to check for new images.
        """
        super().__init__()
        self.socket = context.socket(zmq.REQ)
        self.socket.bind(socket_url)
        self.drone_thread = drone
        self.running = True
        self.sema = Semaphore(0)

    def run(self):
        """
        Runs the thread.
        """
        while self.running:
            if self.drone_thread.new_image:
                self.new_pic(self.drone_thread.pop_first_image())
                response = self.socket.recv_json()
                #print(response)
            else:
                time.sleep(0.1)

    def new_pic(self, image):
        """
        Called when a new picture is taken, send this to the client that wanted it.

        Keyword arguments:
        image -- An instance of the image from the rds database to be sent to IMM.
        """

        image_array = cv2.imread(image.image_path)
        metadata = {
            "fcn": "new_pic",
            "arg": {
                "drone_id": "one",
                "type": "RGB",
                "force_queue_id": image.force_queue_id,
                "coordinates": image.coordinates
            }
        }
        self.send_image(metadata, image_array)

    def send_image(self, metadata, image_array, flags=0, copy=True, track=False):
        """
        Sends the image to IMM.
        It first sends the metadata of the image and then the image array itself.

        Keyword arguments:
        metadata -- A dictionary/json representing the metadata of the image. Info about shape of the image array
                    (width and height) is added to the json here.

        image_array -- The numpy 2d array representing the image.

        See pyzmq for additional information
        https://pyzmq.readthedocs.io/en/latest/api/zmq.html.
        flags -- Integer that sets flags for zeroMQ: 0 or NOBLOCK
        copy -- A boolean that tells zeroMQ to copy the received image: True or False.
        track -- Tells zeroMQ to track the message: True or False. (ignored if copy=True).

        """

        array_info = dict(
            dtype=str(image_array.dtype),
            shape=image_array.shape,
        )

        metadata["array_info"] = array_info
        arr = image_array[0]
        self.socket.send_json(metadata, flags | zmq.SNDMORE)
        self.socket.send(image_array, flags, copy=copy, track=track)

    def stop(self):
        """
        Stops the thread, used for debugging.
        """
        request = {
            "fcn": "stop"
        }
        self.socket.send_json(request)
        resp = self.socket.recv()
        self.running = False


class IMMSubThread(Thread):
    """
    Simulates RDS-Subscribe link
    """

    def __init__(self, socket_url, drone):
        """
        Initializes the thread.

        Keyword arguments:
        socket_url -- The url of the socket the thread will bind to through zeroMQ.
                      This is the socket thread_rds_sub will connect to to listen for new images during testing.
        drone -- Instance of the drone-thread to check for new images.
        """
        super().__init__()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(socket_url)
        self.drone_thread = drone
        self.running = True

    def run(self):
        """
        Runs the thread.
        """
        while self.running:
            try:
                request = self.socket.recv_json()
                if request["fcn"] == "add_poi":
                    self.socket.send_json(self.add_poi(request["arg"]))

                elif request["fcn"] == "stop":
                    self.stop()
                else:
                    self.socket.send_json(json.dumps({"msg": "nothing happened"}))
            except:
                pass

    def add_poi(self, poi):
        """
        Gets corner coordinates from client

        Keyword arguments:
        poi -- A json representing a point of interest.

        Returns a response for zeroMQ to send back to IMM.
        """
        coordinates = poi["coordinates"]
        # Maybe add a wait here to make it threadsafe
        with rds_session_scope() as session:
            if self.drone_thread.get_mode() == "MAN":
                
                # TODO: This is temporarily set to just retrieve any image from the db, should instead retrieve the most
                #   fitting image(s), e.g. by center point
                # Original code:
                #       image = session.query(RDSImage).filter_by(coordinates=coordinates).first()
                image = session.query(RDSImage).first()

                if image is not None:
                    image.force_queue_id = poi["force_queue_id"]
                    self.drone_thread.add_image_to_queue(image)
                    return {"msg": "Image added to queue"}
                else:
                    print("Image with those coordinates does not exist")
                    print("Common fixes:")
                    print("1. Run RDS_emulator/init_db_and_add_images.py")
                    print("2. Make sure that the coordinates corresponds to an image that actually exists.")
                    return {"msg":"Something went wrong"}

    def stop(self):
        """
        Stops the thread, used for debugging.
        """
        self.socket.send_json({"fcn": "ack"})
        self.running = False


class IMMRepThread(Thread):
    """
    Simulates the Reply-link (INFO-link)
    """

    def __init__(self, socket_url, drone):
        super().__init__()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(socket_url)
        self.drone_thread = drone
        self.running = True

    def run(self):
        """
        Runs the thread.
        """

        while self.running:
            request = self.socket.recv_json()
            self.drone_thread.start_change()
            if request["fcn"] == "queue_ETA":
                self.eta()
            elif request["fcn"] == "set_mode":
                self.socket.send_json(self.set_mode(request))
            elif request["fcn"] == "stop":
                self.stop()
            elif request["fcn"] == "get_info":
                self.get_info()
            else:
                self.socket.send_json({"msg":"ack"})
        print("RDS REP STOP")

    def get_info(self):
        """
        Returns info on connected drones, for now
        """
        response = {
            "fcn": "ack",
            "arg": "get_info",
            "arg2": {
                "drone-id": "one",
                "time2bingo": 15
            },
            "arg3": {
                "drone-id": "two",
                "time2bingo": 30
            },
            "arg4": {
                "drone-id": "three",
                "time2bingo": 45
            }
        }
        self.socket.send_json(response)

    def set_area(self):
        """
        Sets the area.
        """
        pass

    def clear_queue(self):
        """
        Returns info on connected drones, for now.
        """
        pass

    def eta(self):
        """
        Returns the time (in seconds) until next picture
        """

        res = {
            "fcn": "ack",
            "arg": "queue_ETA",
            "arg2": str(self.drone_thread.next_image_eta())
        }
        # print("ETA", res)
        self.socket.send_json(res)

    def stop(self):
        """
        Stops the thread, used for debugging.
        """
        self.socket.send_json({"fcn":"ack"})
        self.running = False

    def set_mode(self, request):
        """
        Sets the mode of the RDS.
        If mode is set to AUTO, all images in RDS_emulator/AUTO_images/auto_sequence_test_images folder will be added
        to the drone-threads image queue and be sent to IMM in a sequence at a fixed rate (Each FLYING_TIME seconds).

        Keyword arguments:
        request -- A json representing the request.

        Returns a response for zeroMQ to send back to IMM.
        """
        self.drone_thread.set_mode(request["arg"]["mode"])
        if request["arg"]["mode"] == "AUTO":
            self.add_auto_images_to_queue() # So images will be sent continously.
        return {"msg": "mode set"}

    def add_auto_images_to_queue(self):
        """
        Adds all images in RDS_emulator/AUTO_images/auto_sequence_test_images folder to drone thread image queue.
        """
        with rds_session_scope() as session:
            auto_images = session.query(RDSImage).filter_by(mode="AUTO").all()
            for image in auto_images:
                self.drone_thread.add_image_to_queue(image)
            i = 0
