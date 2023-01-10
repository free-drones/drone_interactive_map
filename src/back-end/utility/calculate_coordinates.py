"""Implement a script to approximate image coordinates from metadata.

The script uses the command line utility exiftool for Linux. This can
be installed with "sudo apt install exiftool". exiftool is used to
extract the exif metadata from the images.

To process all images in a directory, run this script from the directory.
The script will output all image coordinates to coordinates.JSON.

It is assumed that latitudinal coordinates are in the range [-90, 90] where
0 is at the equator and north is in the positive direction. Similarly,
longitudinal coordinates are in the range [-180, 180] where 0 is the Greenwich
Meridian and east is in the positive direction.

All functions taking metadata as a keyword argument expects a dictionary.
The key and value is the title and value in the exiftool printout, with
all whitespace and colons removed. The coordinate calculation only works
on images that contains the metadata fields GPSLatitude, GPSLongitude,
RelateAltitude, FieldOfView, ExifImageWidth, ExifImageHeight and FlightYawDegree.
"""

import subprocess
from math import sin, cos, tan, pi, hypot
import os
import json

from utility.helper_functions import coordinates_list_to_json

def to_decimal_coordinate(deg, min, sec):
    """Convert a coordinate given in deg, min, sec format to decimal degree.

    Keyword arguments:
    deg -- The coordinate degrees.
    min -- The coordinate minutes.
    sec -- The coordinate seconds.

    Returns the coordinate in decimal format.
    """
    return deg + min / 60 + sec / 3600

def get_center(metadata):
    """Retrieve the image center point from metadata.

    Return the center point as a (latitude, longitude) tuple. Coordinate is
    expressed in decimal degree where N/E is the reference direction.
    """
    lat = metadata["GPSLatitude"].replace('"', "").replace("'", "").split()
    lat = (-1 if lat[4] == "S" else 1) * to_decimal_coordinate(float(lat[0]), float(lat[2]), float(lat[3]))
    long = metadata["GPSLongitude"].replace('"', "").replace("'", "").split()
    long = (-1 if long[4] == "W" else 1) * to_decimal_coordinate(float(long[0]), float(long[2]), float(long[3]))
    return lat, long

def get_altitude(metadata):
    """Return the altitude the image was taken at.

    Keyword arguments:
    metadata -- The metadata as described above.
    """
    return float(metadata["RelativeAltitude"])

def get_fov(metadata):
    """Return the fov if the image in radians.

    Keyword arguments:
    metadata -- The metadata as described above.
    """
    return float(metadata["FieldOfView"].split()[0]) * pi / 180

def get_dimensions(metadata):
    """Return the width and height of the image in pixels.

    Keyword arguments:
    metadata -- The metadata as described above.
    """
    return int(metadata["ExifImageWidth"]), int(metadata["ExifImageHeight"])

def get_yaw(metadata, offset=5):
    """Return the drone yaw when picture was taken.

    Yaw is given in counter_clockwise radians. An adjustment is made to compensate
    for apparent uncalibrated drone readings.

    Keyword arguments:
    metadata -- The metadata as described above.
    offset -- Value offset caused by uncalibrated drone sensors.
    """
    return -(float(metadata["FlightYawDegree"]) - offset) * pi / 180

def get_offset(fov, altitude, aspect_ratio):
    """Return the distance in meters from center point to edges.

    Keyword arguments:
    fov -- The camera field of view.
    altitude -- The distance from the camera to the ground.
    aspect_ration -- The image aspect ration.
    """
    viewX = tan(fov / 2) * altitude
    viewY = viewX / aspect_ratio
    return viewX, viewY

def rotate(points, theta):
    """Rotate a set of 2D points theta radians counter-clockwise.

    Keyword arguments:
    points -- A list of 2D coordinates to rotate.
    theta -- The rotation angle in radians.

    Returns a list of rotated coordinates.
    """
    return [
        [x * cos(theta) - y * sin(theta),
         x * sin(theta) + y * cos(theta)]
    for x, y in points]

def m_to_deg(m, lat):
    """Converts meters to degrees at the given latitude.

    The distance is assumed to be small compared to size of the earth.

    Assumes the WGS84 earth speroid. For more information, see:
    https://en.wikipedia.org/wiki/Geographic_coordinate_system

    Keyword arguments:
    m -- A 2-tuple of distance in meters in latitudinal and longitudinal
         directions respectively.
    lat -- The latitude where the distance should be meassured.

    Returns the distances converted to fractions of degrees.
    """
    lat = lat * pi / 180
    m_per_deg_lat = 111132.92 - 559.82 * cos(2*lat) + 1.175 * cos(4*lat) - 0.0023 * cos(6*lat)
    m_per_deg_long = 111412.84 * cos(lat) - 93.5 * cos(3*lat) + 0.118 * cos(5*lat)
    return [m[0] / m_per_deg_lat, m[1] / m_per_deg_long]

def to_coords(center, offset):
    """Returns the coordinates at offset from center.

    Keyword arguments:
    center -- The center coordinate.
    offset -- A list of offsets from center.
    """
    res = []
    for x, y in offset:
        offset = m_to_deg([y, x], center[0])
        res.append([center[0] + offset[0], center[1] + offset[1]])
    return res

def calculate_coordinates(image_path):
    """Return the approximate corner coordinates of an image.

    Keyword arguments:
    image_path -- The absolute or relative path to the image.
    """
    exif = str(subprocess.check_output(["exiftool", image_path]))
    exif = exif.split("\\n")
    exif = [line.split(": ") for line in exif]
    exif = {
        line[0].replace(" ", "") : line[1].replace("\\", "") for line in exif if len(line) == 2
    }

    center = get_center(exif)
    altitude = get_altitude(exif)
    fov = get_fov(exif)
    width, height = get_dimensions(exif)
    yaw = get_yaw(exif)
    x, y = get_offset(fov, altitude, width / height)
    offset = [[-x, y], [x, y], [x, -y], [-x, -y]]
    offset = rotate(offset, yaw)
    corners = to_coords(center, offset)
    return coordinates_list_to_json(corners + [center])

if __name__ == "__main__":
    files = os.listdir(os.getcwd())
    files = sorted([file for file in files if ".JPG" in file])
    result = {}
    for file in files:
        result[file] = calculate_coordinates(file)
        print("Processed", file)
    with open("coordinates.JSON", 'w') as outfile:
        json.dump(result, outfile)
