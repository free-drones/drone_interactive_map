"""
This mock simulates frontend setting mode to AUTO and gets four images from IMM.
"""

import numpy as np
import socketio as sio2
from utility.test_helper_function import create_backend_thread, init_db_and_add_all_images
from config_file import BACKEND_BASE_URL
import requests
import cv2

create_backend_thread()

# -------------Test -----------
client = sio2.Client()
client.connect(BACKEND_BASE_URL)

mode_req = {
            "fcn": "set_mode",
            "arg": {
                "mode": "AUTO",
                "zoom": {
                    "up_left":
                    {
                        "lat": 59.81335168977088,
                        "long": 17.65616516294909
                    },
                "up_right":
                    {
                        "lat": 59.81337030292837,
                        "long": 17.657929343536647
                    },
                "down_left":
                    {
                        "lat": 59.81268525262718,
                        "long": 17.65619287868557
                    },
                "down_right":
                    {
                        "lat": 59.81270386578467,
                        "long": 17.657957059273127
                    },
                "center":
                    {
                        "lat": 59.813027777777776,
                        "long": 17.65706111111111
                    }
            }
            }
        }

client.emit("init_connection", {})
client.emit("set_mode", mode_req)

image_count = 0
IMAGE_LIMIT = 4
image_list = []

@client.on('notify')
def on_message(data):
    global image_count
    global image_list
    if data["fcn"] == "new_pic":
        image_count += 1
        resp = requests.get(data["arg"]["url"])
        image = np.asarray(bytearray(resp.content), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image_list.append(image)
    if image_count >= IMAGE_LIMIT:
        if len(image_list) == 4:
            print("Test successful")
