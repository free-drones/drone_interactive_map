"""
This mock simulates frontend sending a prio image requests and then waits for it.
"""

import numpy as np
import socketio as sio2
from utility.test_helper_function import create_backend_thread, init_db_and_add_images, stop_backend_thread
from config_file import BACKEND_BASE_URL
import requests
import cv2, json
from utility.helper_functions import get_path_from_root
create_backend_thread()

# --------------------- TEST --------------------------

client = sio2.Client()
client.connect(BACKEND_BASE_URL)

# Retrieve example coordinates.
with open(get_path_from_root("/RDS_emulator/AUTO_images/auto_sequence_test_images/coordinates.JSON")) as f:
    example_coords = json.load(f)["DJI_0840.JPG"]

data_req = {
    "arg":
    {
        "coordinates": example_coords,
        "client_id": 1,
        "type": "RGB"
    }
}
# Connect to the server.
client.emit("init_connection", data={})


@client.on('response')
def on_response(data):
    if data["fcn"] == "ack" and data["fcn_name"] == "connect":
        client.emit("request_priority_view", data_req)


@client.on('notify')
def on_message(data):
    if data["fcn"] == "new_pic":
        print("Got notification about new image, Test successful")
        client.disconnect()
