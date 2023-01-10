"""
This file contains tests for image processing. When run, it applies image processing to
all jpg images in the sample_images directory. They must be taken in the area of
sample_images/tileTestImage.png to perform as expected.
"""

import os
import cv2

from utility.calculate_coordinates import calculate_coordinates
from IMM.image_processing import _tune_image_coordinates
from IMM.image_processing import STATUS_SUCCESS, STATUS_NO_BUILDINGS_IN_DRONE_IMAGE, STATUS_NO_BUILDINGS_IN_TILE_IMAGE, STATUS_MOVED_MATCH, STATUS_DISTORTED_MATCH
from utility.helper_functions import get_path_from_root, coordinates_list_to_json

TILE_COORDS = coordinates_list_to_json([
    [59.812636, 17.654736],
    [59.812636, 17.660082],
    [59.811393, 17.660082],
    [59.811393, 17.654736]
])

def image_test():
    success = 0
    no_drone_building = 0
    no_tile_building = 0
    moved_match = 0
    distorted = 0
    total = 0
    image_dir = get_path_from_root("/sample_images/")
    images = sorted([image_dir + file for file in os.listdir(image_dir) if "jpg" in file.lower()])
    for image in images:
        print("Processing image", image)
        tile_image = cv2.imread(get_path_from_root("/tests/manual/sample_images/tileTestImage.png"))
        drone_file = image
        drone_image = cv2.imread(drone_file)
        drone_coordinates = calculate_coordinates(drone_file)
        result = _tune_image_coordinates(tile_image, TILE_COORDS, drone_image, drone_coordinates, debug=True)
        total += 1
        if result == STATUS_SUCCESS:
            success += 1
        elif result == STATUS_NO_BUILDINGS_IN_TILE_IMAGE:
            no_tile_building += 1
        elif result == STATUS_NO_BUILDINGS_IN_DRONE_IMAGE:
            no_drone_building += 1
        elif result == STATUS_MOVED_MATCH:
            moved_match += 1
        elif result == STATUS_DISTORTED_MATCH:
            distorted += 1

    fails = total - success
    print()
    print("=== STATISTICS ===")
    print("Processed", total, "images. Found", success, "matches. Success rate:", success/total)
    print("Fail causes:")
    print("  No tile buildings detected:", no_tile_building)
    print("  No drone buildings detected:", no_drone_building)
    print("  No candidate match found with acceptable distortion:", distorted)
    print("  Best candidate moved too far, probable mismatch:", moved_match)
    print("  Other:", fails - no_tile_building - no_drone_building - distorted - moved_match)

if __name__ == "__main__":
    image_test()
