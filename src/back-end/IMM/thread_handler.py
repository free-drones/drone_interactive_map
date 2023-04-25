"""This file handles the IMM threads. The class ThreadHandler contains all
threads and can start them at the same time.
"""

import time

from IMM.threads.thread_rds_pub import RDSPubThread
from IMM.threads.thread_rds_sub import RDSSubThread
from IMM.threads.thread_gui_pub import GUIPubThread
from IMM.threads.thread_info_fetcher import InfoFetcherThread
from IMM.drone_manager.drone_manager import DroneManager

class ThreadHandler:
    """Regularly fetches information from the RDS and processes client requests"""
    def __init__(self, socketio):
        """Initiates the thread.

        Keyword arguments:
        socketio -- The SocketIO object retrieved when creating the app.
        """

        super().__init__()
        self.rds_pub_thread = RDSPubThread(self)
        self.gui_pub_thread = GUIPubThread(self, socketio)
        self.rds_sub_thread = RDSSubThread(self)
        self.info_fetcher_thread = InfoFetcherThread()
        self.drone_manager_thread = DroneManager()

    def start_threads(self):
        """Starts the threads"""
        self.rds_pub_thread.start()
        self.rds_sub_thread.start()
        self.gui_pub_thread.start()
        self.info_fetcher_thread.start()
        self.drone_manager_thread.start()

    def stop_threads(self):
        """Stops the threads. Used for debugging."""
        self.info_fetcher_thread.stop()
        time.sleep(2.1)  # Make sure it doesnt send calls
        self.rds_pub_thread.stop()
        self.gui_pub_thread.stop()
        self.drone_manager_thread.stop()

    def get_rds_pub_thread(self):
        return self.rds_pub_thread

    def get_rds_sub_thread(self):
        return self.rds_sub_thread

    def get_gui_pub_thread(self):
        return self.gui_pub_thread

    def get_drone_manager_thread(self):
        return self.drone_manager_thread