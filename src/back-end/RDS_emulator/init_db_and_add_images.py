"""
Initilizes db and adds all images from AUTO_images/auto_sequence_test_images
"""

from utility.test_helper_function import init_db_and_add_all_images
from RDS_emulator.database import use_test_database_rds
from threading import Thread

init_db_thread = Thread(target=use_test_database_rds(False))
init_db_thread.start()
init_db_and_add_all_images()

print("Database created successfully and images added")
