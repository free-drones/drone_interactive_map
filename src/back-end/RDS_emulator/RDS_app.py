"""
This file is used for simulating the RDS system which can respond to the IMM requests
when performing tests. This contains a class that handles the RDS threads.

See files in this folder for details.
"""

from RDS_emulator.RDS_emu import *
from RDS_emulator.RDS_config_file import *


class RDSThreadHandler:
    """
    This thread handles the RDS threads.
    """
    def __init__(self):
        """
        Initializes the RDS threads.
        """
        self.drone_thread = DroneThread()
        self.RDSPub_thread = IMMPubThread(RDSPub_socket_url, self.drone_thread)
        self.RDSSub_thread = IMMSubThread(RDSSub_socket_url, self.drone_thread)
        self.RDSRep_thread = IMMRepThread(RDSRep_socker_url, self.drone_thread)

    def start_threads(self):
        """
        Starts the threads.
        """
        self.drone_thread.start()
        self.RDSSub_thread.start()
        self.RDSPub_thread.start()
        self.RDSRep_thread.start()

    def stop_threads(self):
        """
        Stops the threads. Used for debugging.
        """
        self.drone_thread.stop()
        self.RDSPub_thread.stop()
