"""
This file contains various help functions that are used in the program.

See individual functions for comments.
"""

import logging
import os, platform
from shapely.geometry import Polygon, Point
import config_file as config

def get_path_from_root(path):
    """Returns the full path to the specified (relative) path.

    Keyword arguments:
    path -- A string containing the path from the project root folder. Separator '/'

    Returns a string containg the full path from root of the device running IMM.
    """
    res = os.path.dirname(__file__)  # Get the path to the directory where this file is located.
    path_to_wd = res.split(os.sep)[:-1]

    # os.path for windows does not insert a file path separator after drive names since drives 
    # have their own current directories. A file separator is therefore added after the drive name 
    # so the drive's root is used.
    # TODO: implement this more robustly
    if len(path_to_wd[0]) == 2 and ":" in path_to_wd[0]:
        path_to_wd[0] = path_to_wd[0] + os.sep
    else:
        path_to_wd[0] = os.sep + path_to_wd[0]

    path_to_file = path.split("/")
    return os.path.join(*path_to_wd, *path_to_file)


def coordinates_list_to_json(coordinates):
    """Convert a coordinate list to json format.

    If only four coordinates are provided, it is assumed that the center
    coordinate is missing. If so, it is calculated based on the north-south
    oriented bounding box of the coordinates.

    Keyword arguments:
    coordinates     A list where the coordinates are given in order up_left,
                    up_right, down_right, down_left and center. Each
                    coordinate is a (latitude, longitude) list or tuple.

    Returns a dictionary following the format specified in the RDS API.
    """

    lats = [coordinate[0] for coordinate in coordinates]
    longs = [coordinate[1] for coordinate in coordinates]
    min_lat = min(lats)
    max_lat = max(lats)
    min_long = min(longs)
    max_long = max(longs)
    center_lat = (min_lat + max_lat) / 2
    center_long = (min_long + max_long) / 2
    coordinates.append([center_lat, center_long])

    point_order = ["up_left", "up_right", "down_right", "down_left", "center"]
    direction_order = ["lat", "long"]
    return {
        point_order[i] : {
            direction_order[j] : coordinates[i][j] for j in range(len(direction_order))
        } for i in range(len(point_order))
    }

def coordinates_json_to_list(coordinates):
    """Convert a coordinate json to list format.

    Keyword arguments:
    coordinates     A dictionary following the format specified in the RDS API.

    Returns a list where the coordinates are given in order up_left,
    up_right, down_right, down_left and center. Each coordinate is a
    (latitude, longitude) list or tuple.
    """

    point_order = ["up_left", "up_right", "down_right", "down_left", "center"]
    direction_order = ["lat", "long"]
    return [
        [coordinates[point][direction] for direction in direction_order] for point in point_order
    ]


def dig(value_dict, key_path):
    """Recursively checks each key in ''key_path and sees if it exists in ''value_dict''

    Keyword arguments:
    value_dict -- A dict containing the values to be checked.
    key_path -- A list containing the keys in the path that will be checked
                in value_dict.

    Returns a boolean which is true if the key path existed and false if not.
    """

    if not key_path:
        return False

    elif isinstance(key_path, str) and key_path in value_dict:
        return True

    elif key_path[0] not in value_dict.keys():
        return False
    else:
        return dig(value_dict[key_path[0]], key_path[1:])


def check_keys_exists(value_dict, key_paths):
    """Checks the keys in ''value_dict'' and sees if it matches the key paths supplied in ''key_paths'' list

    Keyword arguments:
    value_dict -- A dict containing the values to be checked.
    key_paths -- A list containing the paths of keys that will be checked in value_dict.

    Returns a boolean which is true if all key paths existed and false if not.
    """

    for key_path in key_paths:
        if not dig(value_dict, key_path):
            return True
    return False




"""
Geometry functions
"""
class GeometryError(Exception):
    pass

def is_overlapping(square1, square2):
    """Returns true if two squares are overlapping.

    This functions takes a list of 4 points as input, which must be in
    the following order [bottom_left, top_left, top_right, bottom_right].
    If not the function will return an error message.

    Square1 and square2 will be made into shapely-Polygons and then the
    function will see if they intersects.

    keyword arguments:
    square1 -- A list with [bottom_left, top_left, top_right, bottom_right],
               where each element is a tuple with (long, lat). Where long and lat
               are a floating point number representing latitude and longitude.

    square2 -- A list with [bottom_left, top_left, top_right, bottom_right],
               where each element is a tuple with (long, lat). Where long and lat
               are a floating point number representing latitude and longitude.
    """

    # Error handling
    if len(square1) != 4 or len(square2) != 4:
        raise GeometryError("Wrong size input")
    elif type(square1) != list and type(square2) != list:
        raise GeometryError("Input is not as a list")

    polygon1 = Polygon(square1)
    polygon2 = Polygon(square2)

    if polygon1.intersects(polygon2):
        return True
    else:
        return False


def polygon_contains_point(in_point, in_polygon):
    """Returns true if point is within polygon (NOTE: the polygon must be a quadrilateral, *not* a general polygon)

    This function takes a point as (x,y) and
    a list as [bottom_left, top_left, top_right, bottom_right]
    If not the function will return an error message.

    The polygon will be made into shapely-Polygon and the point into a
    shapely-Point.

    Keyword arguments:
    in_point -- A tuple representing (long, lat). Where long and lat
                are a floating point number representing latitude and longitud.
                
    in_polygon -- A list with [bottom_left, top_left, top_right, bottom_right],
               where each element is a tuple with (long, lat). Where long and lat
               are a floating point number representing latitude and longitude.
    '"""

    # Error handling
    if len(in_polygon) != 4 or len(in_point) != 2:
        raise GeometryError("Wrong size input")
    elif type(in_point) != tuple and type(in_polygon) != list:
        raise GeometryError("Input wrong format")

    point = Point(in_point[0], in_point[1])
    polygon = Polygon(in_polygon)

    if point.within(polygon):
        return True
    else:
        return False

def create_logger(logger_name, file_level=config.FILE_LOG_LEVEL, console_level=config.CONSOLE_LOG_LEVEL, custom_file_name=None):
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(logger_name)

    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter(format))
    logger.addHandler(console)
    
    if custom_file_name:
        file = logging.FileHandler(custom_file_name)
    else:
        file = logging.FileHandler(config.LOG_FILE)
    file.setLevel(file_level)
    file.setFormatter(logging.Formatter(format))
    logger.addHandler(file)

    # Ensure that the global log level includes requested log levels
    logging.getLogger().setLevel(min(file_level, console_level))

    return logger
