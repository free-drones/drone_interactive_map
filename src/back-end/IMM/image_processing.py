"""
This file handles image processing, see individual function comments for 
functionallity. The process function is the intended entry point for the
image processing.

Two distinct types of images are processed, tile images and drone images.
Tile images are images of the map provided by OpenStreetMap. Drone images
are aerial photos of an area taken by a drone. The goal of the image
processing is to take preliminary coordinates for the drone image and alter
them to better fit the corresponding tile image.

Throughout this file, including documentation, "pixel coordinate" denotes
the (row, column) coordinate of a pixel in an image, relative to the upper
left corner, while "coordinate" denotes a location relative to a coordinate
systemet external to the image in question. In particular "corner coordinates"
denotes the coordinates of the image corner pixels relative to this external
coordinate system.

The perspective transform is used throughout the image processing. For more
information on this transform, see:
https://docs.opencv.org/2.4/modules/imgproc/doc/geometric_transformations.html

All image arguments are assumed to be cv2 images, i.e. numpy arrays where
image rows and columns are in the first and second array dimension
respetively. Color channels are optinally in the third dimension. Color
images are assumed to be in BGR format without an alpha channel, unless
specified otherwise.
"""

import math
import cv2
import numpy

import utility.image_util as image_util
from utility.image_util import BLUE, GREEN, RED
from utility.helper_functions import coordinates_list_to_json, create_logger
from config_file import TILE_SERVER_AVAILABLE, ENABLE_IMAGE_PROCESSING

""" Feature colors in the tile image. """
__TILE_COLOR_HOUSE = image_util.pixel(201, 208, 217)
__TILE_COLOR_URBAN = image_util.pixel(233, 239, 242)
__TILE_COLOR_FIELD = image_util.pixel(213, 240, 238)
__TILE_COLOR_ROAD = image_util.pixel(255, 255, 255)
__TILE_COLOR_PARKING = image_util.pixel(238, 238, 238)

""" Status codes. """
STATUS_SUCCESS = 0
STATUS_NO_BUILDINGS_IN_DRONE_IMAGE = -1
STATUS_NO_BUILDINGS_IN_TILE_IMAGE = -2
STATUS_DISTORTED_MATCH = -3
STATUS_MOVED_MATCH = -4

LOGGER_NAME = "image_processing"
__logger = create_logger(LOGGER_NAME)


def __find_tile_buildings(image):
    """Detect buildings in the tile image.
    
    Keyword arguments:
    image -- The tile image to process.

    Returns a list of all detected buildings. Each building is given
    as a list of coordinates defining the building outline.
    """
    EDGE_DILATION = 3
    CANNY_LOW_THRES = 100
    CANNY_HIGH_THRES = 255
    MIN_BUILDING_AREA = 1000
    MAX_RECT_RATIO = 1.2

    # Sharpen image to make building edges more distinct
    kernel = numpy.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    image = cv2.filter2D(image, -1, kernel)

    # Find buildings using color information
    mask = image_util.color_mask(image, __TILE_COLOR_HOUSE)

    # Draw bounding rectangle to give buildings at image edges a complete contour
    cv2.rectangle(mask, (0, 0), (mask.shape[1]-1, mask.shape[0]-1), 0, 3)

    # Find building contours using edge information
    edges = cv2.Canny(mask, CANNY_LOW_THRES, CANNY_HIGH_THRES)
    edges = cv2.dilate(edges, numpy.ones((EDGE_DILATION, EDGE_DILATION), numpy.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out non-rectangular buildings, as they are not reliably
    # detectable in the drone images. Also remove small contours
    # caused by image interference
    buildings = []
    for contour in contours:
        area = cv2.contourArea(contour)
        bound = cv2.minAreaRect(contour)
        bound_area = cv2.contourArea(cv2.boxPoints(bound))
        if area > MIN_BUILDING_AREA and bound_area / area < MAX_RECT_RATIO:
            buildings.append(image_util.to_vertex_list(contour))

    return buildings

def __find_drone_buildings(image):
    """Detect buildings in the drone image.
    
    Keyword arguments:
    image -- The drone image to process.

    Returns a list of all detected buildings. Each building is given
    as a list of coordinates defining the building outline.
    """
    BLUR_SIZE = 5
    CANNY_LOW_THRES_FIRST = 50
    CANNY_HIGH_THRES_FIRST = 150
    EDGE_DILATION = 9
    CANNY_LOW_THRES_SECOND = 200
    CANNY_HIGH_THRES_SECOND = 255
    CONTOUR_DILATION = 25
    MIN_BUILDING_AREA = 50000
    MAX_RECT_RATIO = 1.2

    # Using a meadian blur means strong edges has an increased
    # chance to remain.
    image = image_util.blur(image, size=BLUR_SIZE, blur_type="median")

    # Find edges using the Canny algorithm. Edges are dilated to
    # increase chance of building outlines being connected.
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, CANNY_LOW_THRES_FIRST, CANNY_HIGH_THRES_FIRST)
    edges = image_util.dilate(edges, EDGE_DILATION)

    # Building contours are located in a two step process. First, all
    # contours larger than a certain threshold and approximately rectangular
    # are marked on a binary map and dilated. Then, new contours are found
    # in this binary map. The purpose of this is to increase the likelihood that
    # contours detected separately but belonging to the same building are
    # rejoined to a single contour.
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contour_map = numpy.zeros(edges.shape, numpy.uint8)
    for cont in contours:
        area = cv2.contourArea(cont)
        rect = cv2.minAreaRect(cont)
        box = cv2.boxPoints(rect)
        bound_area = cv2.contourArea(box)
        if area > MIN_BUILDING_AREA and bound_area / area < MAX_RECT_RATIO:
            cv2.drawContours(contour_map, [cont], -1, 255, -1)
    contour_map = image_util.dilate(contour_map, CONTOUR_DILATION)

    edges = cv2.Canny(contour_map, CANNY_LOW_THRES_SECOND, CANNY_HIGH_THRES_SECOND)
    edges = image_util.dilate(edges, EDGE_DILATION)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    buildings = []
    for cont in contours:
        if cv2.contourArea(cont) > MIN_BUILDING_AREA:
            buildings.append(image_util.to_vertex_list(cont))

    return buildings

def __get_perspective(img1_dim, coordinates1, img2_dim, coordinates2):
    """Return perspective transform between two images.

    The prespective transform is calculated using the known corner coordinates of
    the two images and gives the transformation from pixel coordinates in img2 to
    pixel coordinates in img1.
    
    Keyword arguments:
    img1_dim -- The shape of the first image.
    coordinates1 -- The corner coordinates of img1.
    img2_dim -- The shape of the second image.
    coordinates2 -- The corner coordinates of img2.
    """

    # Coordinates of lower left corner of image 1.
    start_lat = coordinates1["down_left"]["lat"]
    start_long = coordinates1["down_left"]["long"]

    # Factors to convert from pixels in image 1 to degrees.
    deg2pix_lat = img1_dim[0] / (coordinates1["up_left"]["lat"] - coordinates1["down_left"]["lat"])
    deg2pix_long = img1_dim[1] / (coordinates1["up_right"]["long"] - coordinates1["up_left"]["long"])

    # Calculate the pixel coordinates in image 1 of the corners of image 2.
    coords_in_img1 = []
    for key in ["up_left", "up_right", "down_right", "down_left"]:
        lat_offset = coordinates2[key]["lat"] - start_lat
        long_offset = coordinates2[key]["long"] - start_long
        y_offset = img1_dim[0] - (lat_offset * deg2pix_lat)
        x_offset = long_offset * deg2pix_long
        coords_in_img1.append([x_offset, y_offset])

    # Setup pixel coordinates in numpy format.
    coords_in_img1 = numpy.array(coords_in_img1, numpy.float32)
    coords_in_img2 = numpy.array([
        [0, 0],
        [img2_dim[1] - 1, 0],
        [img2_dim[1] - 1, img2_dim[0] - 1],
        [0, img2_dim[0] - 1]
    ], numpy.float32)

    # Calculate perspective transform using the corner pixels of image 2 as
    # matched points.
    transform = cv2.getPerspectiveTransform(coords_in_img2, coords_in_img1)

    return transform

def __find_distance(p1, p2):
    """Return the total distance between pairs of 2D points in p1 and p2.
    
    The distance is calculated as dist = sum{ |p1[i] - p2[i]| }.

    Keyword arguments:
    p1 -- The first list of points.
    p2 -- The second list of points.

    Throws ValueError if p1 and p2 has different lengths.
    """
    if len(p1) != len(p2):
        raise ValueError("Number of points must match.")
    dist = 0
    for i in range(len(p1)):
        x1, y1 = p1[i]
        x2, y2 = p2[i]
        dist += math.hypot(x1-x2, y1-y2)
    return dist

def __get_transform_from_match(area1, area2):
    """Return perspective transform from minimum bounding box of two areas.

    Each area is given as a list of 2D points representing the area outline.
    
    Keyword arguments:
    area1 -- The points of the first area.
    area2 -- The points of the second area.
    """

    def order_vertices(rect):
        """Utility function to ensure points are in the same order

        Taken from this tutorial:
        https://www.pyimagesearch.com/2014/05/05/building-pokedex-python-opencv-perspective-warping-step-5-6/
        """
        pts = rect.reshape(4, 2)
        res = numpy.zeros((4, 2), dtype=numpy.float32)

        s = pts.sum(axis=1)
        res[0] = pts[numpy.argmin(s)]
        res[2] = pts[numpy.argmax(s)]

        diff = numpy.diff(pts, axis=1)
        res[1] = pts[numpy.argmin(diff)]
        res[3] = pts[numpy.argmax(diff)]

        return res

    rect1 = cv2.minAreaRect(image_util.to_contour(area1))
    rect1 = cv2.boxPoints(rect1)
    rect2 = cv2.minAreaRect(image_util.to_contour(area2))
    rect2 = cv2.boxPoints(rect2)

    rect1 = order_vertices(rect1)
    rect2 = order_vertices(rect2)

    return cv2.getPerspectiveTransform(rect1, rect2)

def __get_side_lengths(vertices):
    """Return the distance between consecutive (wrapping) pairs of vertices.
    
    Keyword arguments:
    vertices -- A list of 2D coordinates.
    """
    res = []
    for i in range(len(vertices[0])):
        x1, y1 = vertices[0][i][0]
        x2, y2 = vertices[0][(i + 1) % len(vertices[0])][0]
        res.append(math.hypot(x1-x2, y1-y2))
    return res

def _tune_image_coordinates(tile_image, tile_coordinates, drone_image, drone_coordinates, debug=False):
    """Process images to find perspective transform between a tile image and a drone image.

    Look for matching features present on the map and in the drone image.
    I such matches are found, the transform is calculated based on these matches. If no matches are found,
    the preliminary coordinates are used instead.

    Coordinates are given on the format specified in the RDS API.

    tile_image -- An image of the map, ideally covering the entire
                  area covered by the drone image's real position.
    tile_coordinates -- Coordinates of the tile image's corners.
    drone_image -- The drone image to map to the tile image.
    drone_coordinates -- Preliminary coordinates of the drone image. The
                         more accurate these are, the more likely a match
                         can be found and mismatches avoided.
    debug -- Intermediary images will be displayed during
             processing if debug=True. Default False.

    Returns a status code and the calculated perspective transform.
    """
    MAX_DISTORTION = .03
    MAX_MOVEMENT = 700

    preliminary_transform = __get_perspective(tile_image.shape, tile_coordinates, drone_image.shape, drone_coordinates)

    if debug:
        # Show preliminary image positions.
        warped = cv2.warpPerspective(drone_image, preliminary_transform, (tile_image.shape[1], tile_image.shape[0]))
        warped = image_util.add_images(tile_image, warped)
        image_util.show_comparison(tile_image, warped)

    tile_buildings = __find_tile_buildings(tile_image)

    if len(tile_buildings) == 0:
        return STATUS_NO_BUILDINGS_IN_TILE_IMAGE, preliminary_transform

    drone_buildings = __find_drone_buildings(drone_image)
    drone_buildings_warped = [
        image_util.warp(building, preliminary_transform) for building in drone_buildings
    ]

    if len(drone_buildings) == 0:
        return STATUS_NO_BUILDINGS_IN_DRONE_IMAGE, preliminary_transform

    if debug:
        # Show detected buildings.
        drone_contours = [
            image_util.to_contour(building) for building in drone_buildings_warped
        ]
        tile_contours = [
            image_util.to_contour(building) for building in tile_buildings
        ]
        drone_marked = cv2.warpPerspective(drone_image, preliminary_transform, (tile_image.shape[1], tile_image.shape[0]))
        drone_marked = image_util.add_images(tile_image, drone_marked)
        drone_marked = cv2.drawContours(drone_marked, drone_contours, -1, RED, 10)
        tile_marked = tile_image.copy()
        tile_marked = cv2.drawContours(tile_marked, tile_contours, -1, RED, 5)

        image_util.show_comparison(tile_marked, drone_marked)

    # Track the drone building index, tile building index and total vertex
    # move distance of the best match.
    best_match = -1, -1, 1000000000

    # Find a matching pair of buildings.
    for i in range(len(drone_buildings_warped)):
        drone_building = drone_buildings_warped[i]
        for j in range(len(tile_buildings)):
            tile_building = tile_buildings[j]

            # Calculate perspective transform if these buildings were a match.
            candidate = __get_transform_from_match(drone_building, tile_building)
            candidate = candidate.dot(preliminary_transform)

            # Calculate drone image corner coordinates with the preliminary and
            # the candidate perspective transform.
            dh, dw = drone_image.shape[:2]
            original_coordinates = [[0, 0], [dw, 0], [dw, dh], [0, dh]]
            first_coordinates = image_util.warp(original_coordinates, preliminary_transform)
            candidate_coordinates = image_util.warp(original_coordinates, candidate)

            # Meassure total move distance of corner coordinates in candidate transform
            # compared to the preliminary transform.
            dist = __find_distance(first_coordinates, candidate_coordinates)

            # Meassure "distortion", i.e. ratio between new image diagonals. In a correct
            # building match, this ratio should be close to 1.
            middle1 = math.hypot(
                candidate_coordinates[0][0] - candidate_coordinates[2][0],
                candidate_coordinates[0][1] - candidate_coordinates[2][1]
            )
            middle2 = math.hypot(
                candidate_coordinates[1][0] - candidate_coordinates[3][0],
                candidate_coordinates[1][1] - candidate_coordinates[3][1]
            )
            distortion = middle1 / middle2

            # Discard candidate if distortion is too bad. Probable mismatch.
            if not abs(distortion - 1) < MAX_DISTORTION:
                continue

            if best_match[0] == -1 or dist < best_match[2]:
                best_match = i, j, dist

    if best_match[0] == -1:
        return STATUS_DISTORTED_MATCH, preliminary_transform

    # A correct match shouldn't move the image too far from the preliminary
    # position. Discard the best match if it moved the image too far.
    if best_match[2] > MAX_MOVEMENT:
        return STATUS_MOVED_MATCH, preliminary_transform

    if debug:
        # Show match.
        drone_contours = [
            image_util.to_contour(building) for building in drone_buildings_warped
        ]
        tile_contours = [
            image_util.to_contour(building) for building in tile_buildings
        ]
        drone_marked = cv2.warpPerspective(drone_image, preliminary_transform, (tile_image.shape[1], tile_image.shape[0]))
        drone_marked = image_util.add_images(tile_image, drone_marked)
        drone_marked = cv2.drawContours(drone_marked, drone_contours, -1, RED, 10)
        tile_marked = tile_image.copy()
        tile_marked = cv2.drawContours(tile_marked, tile_contours, -1, RED, 5)
        cv2.drawContours(drone_marked, drone_contours, best_match[0], GREEN, 10)
        cv2.drawContours(tile_marked, tile_contours, best_match[1], GREEN, 5)
        image_util.show_comparison(tile_marked, drone_marked)

    transform = __get_transform_from_match(drone_buildings_warped[best_match[0]], tile_buildings[best_match[1]])
    transform = transform.dot(preliminary_transform)
    if debug:
        # Show final position.
        warped = cv2.warpPerspective(drone_image, transform, (tile_image.shape[1], tile_image.shape[0]))
        final_version = image_util.add_images(tile_image, warped)
        image_util.show_comparison(tile_image, final_version)

    return STATUS_SUCCESS, transform

def __rotate_image(drone_image, transform, tile_dim, tile_coordinates):
    """Rotates the drone image and calculates new drone coordinates.

    The drone image is rotated so that it is north oriented. An alpha channel
    is added to the image to handle areas not covered by the image after rotation.
    
    Keyword arguments:
    drone_image -- The drone image.
    transform -- The perspective transform from the drone image to the tile image.
    tile dim -- The shape of the tile image.
    tile_coordinates -- The corner coordinates of the tile image.

    Returns the rotated image, now including an alpha channel, and the corner
    coordinates of the rotated image.
    """

    height = drone_image.shape[0]
    width = drone_image.shape[1]

    # Find corner pixel coordinates after transform
    corners = [[0, 0], [width, 0], [width, height], [0, height]]
    new_corners = image_util.warp(corners, transform)

    # Find bounding box of warped image
    minx = maxx = new_corners[0][0]
    miny = maxy = new_corners[0][1]
    for x, y in new_corners[1:]:
        minx = math.floor(min(minx, x))
        maxx = math.ceil(max(maxx, x))
        miny = math.floor(min(miny, y))
        maxy = math.ceil(max(maxy, y))

    # Calculate new corner coordinates based on the known corner coordinates
    # of the tile image.
    tile_diff_lat = tile_coordinates["up_left"]["lat"] - tile_coordinates["down_left"]["lat"]
    tile_diff_long = tile_coordinates["up_right"]["long"] - tile_coordinates["up_left"]["long"]
    lat_per_pixel = tile_diff_lat / tile_dim[0]
    long_per_pixel = tile_diff_long / tile_dim[1]
    drone_lat_max = tile_coordinates["up_left"]["lat"] - miny * lat_per_pixel
    drone_lat_min = tile_coordinates["up_left"]["lat"] - maxy * lat_per_pixel
    drone_long_min = tile_coordinates["up_left"]["long"] + minx * long_per_pixel
    drone_long_max = tile_coordinates["up_left"]["long"] + maxx * long_per_pixel
    drone_coordinates = coordinates_list_to_json([
        [drone_lat_max, drone_long_min],
        [drone_lat_max, drone_long_max],
        [drone_lat_min, drone_long_max],
        [drone_lat_min, drone_long_min]
    ])

    # If warped image is outside the tile_image, some coordinates might
    # become negative, causing issues when rotating the image. We fix
    # this by adding movement to the transform.
    move = numpy.matrix(numpy.identity(3), numpy.float32)
    if minx < 0:
        move[0, 2] += -minx
        maxx += -minx
        minx = 0
    if miny < 0:
        move[1, 2] += -miny
        maxy += -miny
        miny = 0
    transform = move * transform

    # Adapt transform matrix to retain image resolution after transformation
    scaling = min(height / abs(maxy - miny), width / abs(maxx - minx)) / 4
    transform[2, :] /= scaling
    maxx = int(maxx * scaling); minx = int(minx * scaling); maxy = int(maxy * scaling); miny = int(miny * scaling)

    # Add alpha channel to image to avoid black borders.
    b, g, r = cv2.split(drone_image)
    alpha = numpy.ones(b.shape, dtype=numpy.uint8) * 255
    drone_image = cv2.merge((b, g, r, alpha))

    rotated_image = cv2.warpPerspective(drone_image, transform, dsize=(maxx, maxy))
    rotated_image = rotated_image[miny:maxy, minx:maxx]

    return rotated_image, drone_coordinates

def process(tile_image, tile_coordinates, drone_image, drone_coordinates, debug=False):
    """Perform image processing of a drone image.

    The image processing pipeline takes as input a tile image, a drone image and corner coordinates
    for these images. Matching rectangular buildings are located in both images, and if a match
    is found new corner coordinates for the drone image are calculated. The drone image is then
    rotated so that it is north oriented, based on the old corner coordinates if no match was found.

    Keyword arguments:
    tile_image -- The tile image.
    tile_coordinates -- The corner coordinates of the tile image.
    drone_image -- The drone image.
    drone_coordinates -- The corner coordinates of the drone image.
    debug -- If True, debug information is displayed, such as intermediary steps in the image
             processing pipeline. Default is False.

    Returns the corner coordinates of the rotated drone image, and the rotated drone image. The rotated
    image includes an alpha channel.
    """
    if TILE_SERVER_AVAILABLE and tile_image is None:
        __logger.warning("TILE_SERVER_AVAILABLE is True, but no valid tile image was passed to image processing.")

    find_better_matching = TILE_SERVER_AVAILABLE and ENABLE_IMAGE_PROCESSING and (tile_image is not None)
    if find_better_matching:
        status, transform = _tune_image_coordinates(tile_image, tile_coordinates, drone_image, drone_coordinates, debug=debug)

        if status == STATUS_SUCCESS:
            __logger.info("Image processing successful")
        elif status == STATUS_NO_BUILDINGS_IN_TILE_IMAGE:
            __logger.info("No buildings detected in tile image")
        elif status == STATUS_NO_BUILDINGS_IN_DRONE_IMAGE:
            __logger.info("No buildings detected in drone image")
        elif status == STATUS_DISTORTED_MATCH:
            __logger.info("No undistorted building match detected")
        elif status == STATUS_MOVED_MATCH:
            __logger.info("No sufficiently close building match detected")
        else:
            __logger.warning(f"Invalid status code returned from image processing: {status}")

        rotated_image, drone_coordinates = __rotate_image(drone_image, transform, tile_image.shape, tile_coordinates)
    else:
        transform = __get_perspective([750, 1000], tile_coordinates, drone_image.shape, drone_coordinates)
        rotated_image, drone_coordinates = __rotate_image(drone_image, transform, [750, 1000], tile_coordinates)
        
    return drone_coordinates, rotated_image
