"""
This file contains functions that are used for testing purposes
"""


import threading
import time
import json, glob
from IMM.IMM_app import run_imm, thread_handler, stop_imm, socketio
from IMM.database.database import use_test_database
from RDS_emulator.RDS_app import RDSThreadHandler
from RDS_emulator.database import RDSImage, rds_session_scope, use_test_database_rds
from utility.helper_functions import get_path_from_root

def get_coordinates(coordinates):
    return {
        "up_left":{
            "lat": coordinates["up_left"][0],
            "long": coordinates["up_left"][1]
        },
        "up_right": {
            "lat": coordinates["up_right"][0],
            "long": coordinates["up_right"][1]
        },
        "down_left": {
            "lat": coordinates["down_left"][0],
            "long": coordinates["down_left"][1]
        },
        "down_right": {
            "lat": coordinates["down_right"][0],
            "long": coordinates["down_right"][1]
        },
        "center": {
            "lat": coordinates["center"][0],
            "long": coordinates["center"][1]
        }
    }


def init_db_and_add_all_images():
    """Adds images to the RDS emulator database."""
    
    # TODO: Refactor the path handling to also work on Windows. Currently hard-coded path for the example image.

    # Get coordinates json file
    with open(get_path_from_root("/RDS_emulator/AUTO_images/pum2023_images/coordinates.JSON")) as f:
        coordinates = json.load(f)
    img_file_paths = glob.glob(get_path_from_root("/RDS_emulator/AUTO_images/pum2023_images/*.JPG"))
    print(img_file_paths)
    with rds_session_scope() as session:
        # for img_path in img_file_paths:
        #     img_name = img_path.split("/")[-1]
        #     img_coordinates = coordinates[img_name]
        #     image = RDSImage(img_coordinates, img_path, "AUTO", force_que_id=0)
        #     session.add(image)
        img_path = 'C:\\Users\\Marcu\\Desktop\\RISE drone system\\drone_interactive_map\\src\\back-end\\RDS_emulator\\AUTO_images\\pum2023_images\\overview.JPG'
        img_name = 'overview.JPG'
        img_coordinates = coordinates[img_name]
        image = RDSImage(img_coordinates, img_path, "AUTO", force_que_id=0)
        session.add(image)

# -----------INIT------------------


class IMMTestThread(threading.Thread):
    """Starts the RDS emulator and IMM in test mode."""
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        self.rds_handler = RDSThreadHandler()
        self.rds_handler.start_threads()
        use_test_database(False)
        use_test_database_rds(False, remove=False)
        thread_handler.start_threads()
        run_imm()

    def stop(self):
        self.rds_handler.stop_threads()
        thread_handler.stop_threads()
        stop_imm()


imthread = IMMTestThread()


def create_backend_thread():
    imthread.start()
    socketio.handlers.append(imthread)
    time.sleep(1) # So backend server can start.


def stop_backend_thread():
    imthread.stop()
