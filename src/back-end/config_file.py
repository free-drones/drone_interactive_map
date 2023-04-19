"""
This file contains settings for the server.
"""
import zmq
import logging
context = zmq.Context() # The common context for zeroMQ connections.

"""
TILE_SERVER_BASE_URL is used in /IMM/threads/thread_rds_sub.py.

It's specifies at which address the Tile Server is being hosted.
"""
TILE_SERVER_AVAILABLE = True
TILE_SERVER_BASE_URL = "http://localhost/osm"

"""BACKEND_BASE_URL specifies at which adress the Server is being hosted."""
BACKEND_BASE_URL = "http://pum2020.linkoping-ri.se:65008"

"""Server settings"""
SERVER_PORT = 8080
SERVER_LOG_OUTPUT = True
SERVER_CORS_ALLOWED_ORIGINS= '*'

"""URLS for communicating with RDS sockets"""
RDS_pub_socket_url = "tcp://localhost:5570"
RDS_sub_socket_url = "tcp://localhost:5571"
RDS_req_socket_url = "tcp://localhost:5572"

# Time interval for fetching info from RDS.
UPDATE_INTERVAL = 2

"""If set to False, no image processing is performed, except rotation and rescaling."""
ENABLE_IMAGE_PROCESSING = True

"""File where log messages should be written."""
LOG_FILE = "log.log"

"""Minimum log level to write to console."""
CONSOLE_LOG_LEVEL = logging.WARNING

"""Minimum log level to write to log file."""
FILE_LOG_LEVEL = logging.DEBUG

"""Drone application socket url"""
DRONE_APP_REQ_URL = 'tcp://10.44.170.10:17720'
DRONE_APP_SUB_URL = 'tcp://10.44.170.10:17721'
