"""This file contains the thread that is used to subscribe and listen to new_pic
response from RDS. The thread will retrive the response and match the image in
new_pic to the map (image processing), save new image and it's adjusted coordinates
to the database. The thread will also notify front-end if the image is prioritized.

This file also handles image processing of received images.
"""

import math
import cv2
import numpy, time
import requests
import logging
from config_file import context, zmq
from config_file import RDS_sub_socket_url
from threading import Thread
from utility.helper_functions import check_keys_exists
from utility.session_functions import get_session_id
from IMM.database.database import Image, PrioImage, session_scope, UserSession, Coordinate
from IMM.image_processing import process
from utility.helper_functions import get_path_from_root, coordinates_list_to_json, coordinates_json_to_list, create_logger
import json, datetime
from config_file import TILE_SERVER_BASE_URL, BACKEND_BASE_URL, TILE_SERVER_AVAILABLE

X_AXIS = 1
Y_AXIS = 0

LOGGER_NAME = "thread_rds_sub"
_logger = create_logger(LOGGER_NAME)

def generate_image_name(timestamp):
    """Generates a unique image namen based on timestamp (unixtime).

    Keyword arguments:
    timestamp -- An integer representing unixtime.

    Returns an unique name for an image represented by a string.
    """

    with session_scope() as session:
        count = session.query(Image).filter_by(time_taken=timestamp).count()
    readable_time = datetime.datetime.fromtimestamp(timestamp)
    image_datetime = readable_time.strftime("%Y-%m-%d_%H-%M-%S")
    image_name = image_datetime + "_(" + str(count) + ")" + ".png"
    return image_name


def save_image(image_array):
    """Calls generate_image_name and uses the name to save the new_pic image
    array as a png image in IMM/images.

    Keyword arguments:
    new_pic -- A numpy 2d array representing an image.

    Returns the current timestamp (int) and the generated image name (string).
    """

    timestamp = int(time.time())
    image_name = generate_image_name(timestamp)
    image_path = get_path_from_root("/IMM/images/") + image_name
    cv2.imwrite(image_path, image_array)
    return timestamp, image_name


def deg2num(lat_deg, lon_deg, zoom):
    """Converts latitude and longitude (in degrees) to their corresponding tile
    indexes at a given zoom level.

    Keyword arguments:
    lat_deg -- A floating point number representing latitude in degrees.
    lon_deg -- A floating point number representing longitude in degrees.
    zoom -- An integer representing the zoom level on map (needed for calculation).

    Returns X and Y integer tile indexes on the map corresponding to the
    provided coordinates.
    """

    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_tile_index = int((lon_deg + 180.0) / 360.0 * n)
    y_tile_index = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile_index, y_tile_index


def num2deg(x_tile_index, y_tile_index, zoom):
    """Converts a tiles x and y index at a given zoom level to the corresponding
    coordinate (in degrees) of the top left corner of the tile.

    Keyword arguments:
    x_tile_index --  An integer representing the x tile index on the map.
    y_tile_index -- An integer representing the y tile index on the map.
    zoom -- An integer representing the zoom level on map (needed for calculation).

    Returns latitude and longitude coordinates (in degrees) of the top left
    corner of the tile on the position on the map represented by x_tile_index
    and y_tile_index at the given zoom level.
    """

    n = 2.0 ** zoom
    lon_deg = x_tile_index / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile_index / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def save_to_database(image_args, image_coordinates, image_array, file_data):
    """Saves the image to the database.

    Keyword arguments:
    image_args -- A json containing information about the image
                  (type of image, force_que_id etc).
    image_coordinates -- A json containing the coordinates for image's corners
                         and its center point.
    image_array -- A numpy 2d array representing the image.
    file_data -- A tuple containing the timestamp and filename of the image.
    """

    session_id = get_session_id()

    # Gather image info
    width = len(image_array[0])
    height = len(image_array)
    up_left = Coordinate(image_coordinates["up_left"]["lat"], image_coordinates["up_left"]["long"])
    up_right = Coordinate(image_coordinates["up_right"]["lat"], image_coordinates["up_right"]["long"])
    down_right = Coordinate(image_coordinates["down_right"]["lat"], image_coordinates["down_right"]["long"])
    down_left = Coordinate(image_coordinates["down_left"]["lat"], image_coordinates["down_left"]["long"])
    center = Coordinate(image_coordinates["center"]["lat"], image_coordinates["center"]["long"])

    image = Image(
        session_id=session_id,
        time_taken=file_data[0],
        width=width,
        height=height,
        type=image_args["type"],
        file_name=file_data[1],
        up_left=up_left,
        up_right=up_right,
        down_right=down_right,
        down_left=down_left,
        center=center
    )

    with session_scope() as session:
        session.add(image)
        view = coordinates_json_to_list(image_coordinates)[0:4]
        for existing_image in session.query(Image).filter(Image.is_covered == False):
            existing_image.update_covered(view)
            if existing_image.is_covered:
                _logger.info(f"{existing_image.file_name} is now covered")

        session.commit()
        image_id = image.id

    if int(image_args["force_que_id"]) > 0: # Check if prio image
        with session_scope() as session:
            prio_image = session.query(PrioImage).filter_by(id=int(image_args["force_que_id"]))
            prio_image.image_id = image_id


def get_map_coordinates(x_tile_start, x_tile_end, y_tile_start, y_tile_end, zoom):
    """Retrives the map coordinates.

    Keyword arguments:
    x_tile_start -- An integer representing the start x tile index of the map.
    x_tile_end -- An integer representing the end x tile index of the map.
    y_tile_start -- An integer representing the start y tile index of the map.
    y_tile_end -- An integer representing the start y tile index of the map.
    zoom -- The zoom level of the tile.

    Returns a json containing the coordinates (latitude, longitude) of the
    maps corners.
    """

    coord_tile_up_left = num2deg(x_tile_start, y_tile_start, zoom)
    coord_tile_up_right = num2deg(x_tile_end + 1, y_tile_start, zoom)
    coord_tile_down_left = num2deg(x_tile_start, y_tile_end + 1, zoom)
    coord_tile_down_right = num2deg(x_tile_end + 1, y_tile_end + 1, zoom)
    return coordinates_list_to_json([
        coord_tile_up_left,
        coord_tile_up_right,
        coord_tile_down_right,
        coord_tile_down_left
    ])


def get_map(image_coordinates):
    """Creates a map array from the map tiles fetched from the tile server.

    Keyword arguments:
    image_coordinates -- A json containing the coordinates for image's corners
                         and its center point.

    Returns a tuple containing the numpy array representing the map and a json
    containing the coordinates of the map.

    """

    zoom = 18
    url = TILE_SERVER_BASE_URL + "/" + str(zoom)

    # Note that all corners must be checked, since image orientation is unknown.
    x_tile_up_left_index, y_tile_up_left_index = deg2num(image_coordinates["up_left"]["lat"], image_coordinates["up_left"]["long"], zoom)
    x_tile_up_right_index, y_tile_up_right_index = deg2num(image_coordinates["up_right"]["lat"], image_coordinates["up_right"]["long"], zoom)
    x_tile_down_right_index, y_tile_down_right_index = deg2num(image_coordinates["down_right"]["lat"], image_coordinates["down_right"]["long"], zoom)
    x_tile_down_left_index, y_tile_down_left_index = deg2num(image_coordinates["down_left"]["lat"], image_coordinates["down_left"]["long"], zoom)

    x_tile_start_index = min(x_tile_up_left_index, x_tile_up_right_index, x_tile_down_right_index, x_tile_down_left_index) - 1
    x_tile_end_index = max(x_tile_up_left_index, x_tile_up_right_index, x_tile_down_right_index, x_tile_down_left_index) + 1
    y_tile_start_index = min(y_tile_up_left_index, y_tile_up_right_index, y_tile_down_right_index, y_tile_down_left_index) - 1
    y_tile_end_index = max(y_tile_up_left_index, y_tile_up_right_index, y_tile_down_right_index, y_tile_down_left_index) + 1

    map_array = None
    if TILE_SERVER_AVAILABLE:
        try:
            for y_tile in range(y_tile_start_index, y_tile_end_index + 1):
                map_row = None
                for x_tile in range(x_tile_start_index, x_tile_end_index + 1):
                    tile_url = url + "/" + str(x_tile) + "/" + str(y_tile) + ".png"
                    _logger.debug(f"Retrieving tile from {tile_url}")
                    response = requests.get(tile_url)
                    _logger.debug(f"Got response from {tile_url}")
                    tile_array = numpy.asarray(bytearray(response.content), dtype="uint8")
                    tile_2d_array = cv2.imdecode(tile_array, cv2.IMREAD_COLOR)
                    if map_row is None:
                        # Add first column tp map_row
                        map_row = tile_2d_array
                    else:
                        map_row = numpy.concatenate((map_row, tile_2d_array), axis=X_AXIS)  # Add a column

                if map_array is None:
                    # Add first row to map_array
                    map_array = map_row
                else:
                    map_array = numpy.concatenate((map_array, map_row), axis=Y_AXIS)  # Add a row

        except Exception as e:
            _logger.error("The following exception was thrown when retrieving tiles:")
            _logger.error(e)

    return map_array, get_map_coordinates(x_tile_start_index, x_tile_end_index, y_tile_start_index, y_tile_end_index, zoom)


def match_image_to_map(image_array, image_coordinates):
    """Gets the map from the tileserver that the images overlaps according to
    the image coordinates. Then the coordinates are edited for best match between
    image and map.

    Keyword arguments:
    image_array -- A numpy 2d array representing an image.
    image_coordinates -- A json containing the coordinates for image's corners
                         and its center point.

    Returns a tuple containing the edited image array and coordinates after image
    processing.
    """
    # Get map_array from tileserver at image coordinates
    map_array, map_coordinates = get_map(image_coordinates)
    edited_coordinates, edited_image = process(map_array, map_coordinates, image_array, image_coordinates)

    return edited_coordinates, edited_image

class RDSSubThread(Thread):
    """This thread subscribes to the RDS and handles the data (mostly images) received from the RDS"""

    def __init__(self, thread_handler):
        """Initiates the thread.

        Keyword arguments:
        thread_handler -- The class ThreadHandler, can be found in thread_handler.py
        """

        super().__init__()
        self.RDS_sub_socket = context.socket(zmq.REP)
        self.RDS_sub_socket.connect(RDS_sub_socket_url)
        self.thread_handler = thread_handler
        self.running = True

    def recv_image_array(self, metadata, flags=0, copy=True, track=False):
        """Receives and returns the image converted to a numpy array

        Keyword arguments:
        metadata -- A json containing information about the image that will be
                    received.

        See pyzmq for additional information
        https://pyzmq.readthedocs.io/en/latest/api/zmq.html.
        flags -- Integer that sets flags for zeroMQ: 0 or NOBLOCK
        copy -- A boolean that tells zeroMQ to copy the received image: True or False.
        track -- Tells zeroMQ to track the message: True or False. (ignored if copy=True).

        Returns a numpy 2d array representing the received image.
        """

        image_raw = self.RDS_sub_socket.recv(flags=flags, copy=copy, track=track)
        self.RDS_sub_socket.send_json(json.dumps({"msg": "ack"}))
        buf = memoryview(image_raw)
        image_array = numpy.frombuffer(buf, dtype=metadata["dtype"])
        return image_array.reshape(metadata["shape"])

    def run(self):
        """
        Handles images received by the RDS.
        """
        while self.running:
            request = self.RDS_sub_socket.recv_json()
            keys_exists = check_keys_exists(request, [("arg", "coordinates"), ("arg", "type"), ("arg", "force_que_id")])

            if keys_exists and "array_info" in request:
                # We have a new image
                image_array = self.recv_image_array(request["array_info"])
                image_coordinates = {}
                for corner in ["up_left", "up_right", "down_right", "down_left", "center"]:
                    image_coordinates[corner] = {}
                    for key in ["lat", "long"]:
                        image_coordinates[corner][key] = float(request["arg"]["coordinates"][corner][key])

                if request["arg"]["type"] == "RGB":
                    new_coordinates, new_image_array = match_image_to_map(image_array, image_coordinates)
                else:
                    new_coordinates, new_image_array = image_coordinates, image_array

                img_file_data = save_image(new_image_array)
                if not check_keys_exists(request, ("arg", "type")):
                    save_to_database(request["arg"], new_coordinates, new_image_array, img_file_data)
                _logger.info(f"Added image {img_file_data[1]} to database")
                self.notify_gui(img_file_data[1], int(request["arg"]["force_que_id"]))

            elif request["fcn"] == "stop": # For debugging
                self.RDS_sub_socket.send_json({"fcn":"ack"})
                self.running = False


    def notify_gui(self, image_file_name, force_que_id):
        """Notifies gui about new image

        Keyword arguments:
        image_file_name -- A string representing the name of an image.
        force_que_id -- A integer. If bigger than 0 the image is prioritized,
                        otherwise not.
        """

        args = {}
        with session_scope() as session:
            image = session.query(Image).filter_by(file_name=image_file_name).first()
            if image is not None:
                args["type"] = image.type
                args["prioritized"] = force_que_id > 0
                args["image_id"] = image.id
                args["time_taken"] = image.time_taken
                args["coordinates"] = image.get_coordinate_json()
                args["url"] = BACKEND_BASE_URL + "/get_image/"+str(image.id)
                request = {"fcn": "new_pic", "arg": args}
                self.thread_handler.get_gui_pub_thread().add_request(request)
