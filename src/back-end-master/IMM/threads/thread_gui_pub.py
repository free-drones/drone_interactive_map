"""This file contains the thread that is used for sending data and messages to
the front-end (GUI). It should be started trough the thread_handler.py.

To send a new message/request to front-end call the function add_request() which
will put the message in a queue.
"""

from threading import Thread, Event
from utility.helper_functions import create_logger

LOGGER_NAME = "thread_gui_pub"
_logger = create_logger(LOGGER_NAME)

class GUIPubThread(Thread):
    """This thread sends data to the GUI"""

    def __init__(self, thread_handler, socketio):
        """
        Initiates the thread.

        keyword arguments:
        thread_handler -- The class ThreadHandler, can be found in thread_handler.py
        socketio -- The SocketIO object which is created in IMM_app.py.
        """

        super().__init__()
        self.request_queue = []
        self.running = True
        self.thread_handler = thread_handler
        self.requests_available = Event()
        self.socketio = socketio

    def run(self):
        """Handles request if there are some in the request queue."""
        while self.running:
            self.requests_available.wait()
            request = self.request_queue.pop(0)

            if request["fcn"] == "new_pic":
                self.send_to_gui(request)

            if len(self.request_queue) == 0:
                self.requests_available.clear()

    def send_to_gui(self, msg, to_client_id = None):
        """Sends the message to clients connected to the server (using SocketIO).
        Should not be called outside this thread.

        Keyword arguments:
        msg -- A json containing the message to be sent.
        to_client_id --  An integer (or None) representing a SocketIO room.
                         There is one room per UserSession.
        """
        if to_client_id is None:
            _logger.debug(f"Sending notify request: {msg}")
            self.socketio.emit("notify", msg)
        else:
            _logger.debug(f"Sending notify request to client {to_client_id}: {msg}")
            self.socketio.emit("notify", msg, to_client_id)

    def add_request(self, request):
        """Adds a new request for the thread to handle.
        This function should always be called when you want to send a new
        request.

        Keyword arguments:
        request --  A json containing the request.
        """

        self.request_queue.append(request)
        self.requests_available.set()

    def stop(self):
        """Stops the thread. Used for debugging.
        Should always be called trough thread_handler.py.
        """

        self.running = False
        self.add_request({"fcn": "stop"})
        self.requests_available.set()
