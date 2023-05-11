"""
Config file for the drone manager and related functionality.
"""

DRONE_SPEED = 5.0  # the speed that mission waypoints get, seemingly has no effect (yet)

WAIT_TIME = 1  # wait time for drone manager between each iteration of resource management/mission assignment. 
               # Lower wait time means more frequent calls to RDS

MIN_CHARGE_LEVEL = 20  # the battery level under which drones are sent to home for charging
FULL_CHARGE_LEVEL = 95  # the battery level at which charging drones are considered fully charged and made available for missions

ALTITUDE = 50       # waypoint altitude over the ground
