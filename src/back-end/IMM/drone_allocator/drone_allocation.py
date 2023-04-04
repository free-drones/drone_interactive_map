from random import randrange

import pygame
import os

class Path():
	def __init__(self):
		self.available = True
		self.length = self.dummy_length()
		# waypoints = []...

	def dummy_length(self):
		# Calculate length from waypoints
		# NOTE: NOT REQUIRED. Placeholder value for potential future (WIP) improvements
		return randrange(40, 80)

	def dummy_visit_length(self):
		# This represents how much the length decreases when a drone
		# visits a path, since part of the path will be explored.
		# In practice this won't be used, since you can simply look at
		# the length of the list of unexplored nodes.
		return randrange(4, 10)

	def set_assigned(self, assigned):
		# NOTE: This might not be necessary. Can probably modify self.available directly instead
		# of using this method.
		if self.available != assigned:
			if self.available:
				raise ValueError("Cannot unassign a path that is already available!")
			else:
				raise ValueError("Cannot assign an unavailable path!")
		
		self.available = not self.available # Toggle availability status

		# NOTE: This will likely be handled in a different way in the actual product
		if not assigned:
			# Decrease length when path is unassigned
			self.length -= self.dummy_visit_length() # NOTE: NOT REQUIRED

class Drone():
	def __init__(self):
		self.start_time = 0

		self.flight_duration = randrange(15, 25) # Arbitrary flight duration (for demo purposes)
		self.charge_duration = randrange(2, 5) # Arbitrary charge duration (for demo purposes)

		self.time_to_return = self.est_time_to_return() # NOTE: Used for further (WIP) improvements
		self.time_to_bingo_fuel = self.flight_duration # NOTE: Used for further (WIP) improvements

		self.manual_mode = False

		# Modes:
		# "ready": ready to fly (as soon as the start time has passed)
		# "flying": currently flying
		# "charging": currently charging
		# "waiting": if the drone is unavailable or it does not have an assigned path, it needs to wait.
		self.status = "waiting"
		self.modes = ["ready", "flying", "charging", "waiting"]

		self.path = None
		self.available_paths = []

	def set_status(self, new_status):
		""" 
		Set the status of the drone.
		"""
		if new_status in self.modes: # Make sure the status exists
			self.status = new_status
		else:
			print(f"Status '{new_status}' is not in the list of mission modes!")

	def assign_path(self, path):
		"""
		Assign a path.
		"""
		# TODO: handle case where the path is already assigned? (e.g assert or print a warning)
		path.set_assigned(True)
		self.path = path

	def unassign_path(self):
		"""
		Unassign a path.
		"""
		# TODO: handle case where the path is already unassigned? (e.g assert or print a warning)
		self.path.set_assigned(False)
		self.path = None

	def est_time_to_return(self):
		"""
		NOTE: Placeholder value for potential future (WIP) improvements
		"""
		return randrange(2, 7)

	def on_begin_flying(self):
		"""
		This method is called when the drone begins to fly (i.e when the status is set to "flying").
		"""
		assert self.available_paths is not None

		#paths_by_length = sorted(available_paths, key=lambda x: x.length, reverse=True)
		longest_path = max(self.available_paths, key=lambda x: x.length)
		self.assign_path(longest_path)
		#print("Assign a flight path!")
		
	def on_done_flying(self):
		"""
		This method is called when the drone stops flying.
		"""
		self.manual_mode = False
		self.unassign_path()

	def on_done_charging(self, current_time):
		"""
		This method is called when the has finished charging.
		"""
		self.start_time = current_time

	def await_start(self, current_time):
		"""
		Await start by setting the drone status to "waiting" and
		shifting the start time to the current time.
		"""
		self.set_status("waiting")
		self.start_time = current_time

	def invoke_callback(self, callback_fn, *args, **kwargs):
		# Status change!
	    if not args and not kwargs:
	        callback_fn()
	    elif args and not kwargs:
	        callback_fn(*args)
	    elif kwargs and not args:
	        callback_fn(**kwargs)
	    else:
	        callback_fn(*args, **kwargs)

	def update_status(self, current_time):
		"""
		Update the status based on the current time and call appropriate callback methods
		"""
		if self.manual_mode:
			print(self.available_paths)
			print(self.status)

		if not self.available_paths and self.status == "ready":
			print("NO AVAILABLE PATHS!")
			self.await_start(current_time)

		if current_time >= self.start_time:
			if self.status == "ready":
				self.invoke_callback(self.on_begin_flying)
				self.set_status("flying")

		# In the actual product: Bingo fuel (check if bingo fuel == 0 maybe?).
		if current_time >= self.start_time + self.flight_duration:
			if self.status == "flying":
				self.invoke_callback(self.on_done_flying)
				self.set_status("charging")

		# in the actual product: Check when the drone has finished charging.
		if current_time >= self.start_time + self.flight_duration + self.charge_duration:
			if self.status == "charging":
				self.invoke_callback(self.on_done_charging, current_time)
				self.set_status("waiting")

	def dummy_time_to_reach_path(self, path):
		# Get path endpoint nodes
		# Calculate distance to both
		# Pick closest one
		# Approximate time to reach the closest node based on speed and distance
		
		# NOTE: NOT REQUIRED. Placeholder value for potential future (WIP) improvements
		return self.time_to_return

	def get_available_paths(self, paths, current_time):
		"""
		Get all available paths from this drone's perspective.

		"""
		# If drone is in manual mode, return a dummy path object.
		# In the actual product, this could correspond to a path with a single waypoint?
		# Or maybe a specialized path object that handles manual mode differently
		if self.manual_mode:
			return [ Path() ]

		available = []
		for path in paths:
			# Is the path available (unvisited by any drones)?
			if path.available:
				available.append(path)
			# This is used to handle the time frame where a drone is about to leave its path, and
			# another drone can reach it by the time the first drone has left the path.
			# This is currently completely untested. (WIP)
			elif self.status == "flying": # ?? Should probably be ready or waiting?
				if current_time >= self.start_time + self.time_to_bingo_fuel - self.dummy_time_to_reach_path(path):
					available.append(path)
		return available

	def update(self, paths, current_time):
		self.time_to_bingo_fuel = self.flight_duration - current_time
		self.available_paths = self.get_available_paths(paths, current_time)
		self.update_status(current_time)

	def __str__(self):
		"""
		String representation of a drone object.
		Used to print the status.
		"""
		repr_s = ""
		if self.status == "ready":
			repr_s += "R"
		elif self.status == "flying":
			repr_s += "F-->"
			if not self.manual_mode: 
				repr_s += "\t -A"
		elif self.status == "charging":
			repr_s += "C..."
		elif self.status == "waiting":
			repr_s += "X-"

		if self.manual_mode:
			repr_s += "\t ||M"

		return repr_s


class Mission():
	"""
	Mission class to handle all the interactions between drones and paths
	"""
	def __init__(self, num_drones, num_paths, greedy=False):
		# Drones
		self.drones = [Drone() for i in range(num_drones)] # Create drones
		self.num_drones = num_drones

		# Paths
		self.paths = [Path() for i in range(num_paths)] # Create paths
		self.num_paths = num_paths

		# Manual mode
		self.manual_mode = False
		self.manual_drones = [] # List of drones that are in manual mode.
		self.num_allocated_manual = 1 # Number of drones that are allowed to be in manual mode simultaneously.
		self.greedy = greedy # Used to decide the number of auto drones. (get_target_num_available)

	def available_drones(self):
		"""
		Number of available drones that are currently waiting.
		"""
		drones = [drone for drone in self.drones if drone.status == "waiting"]
		return drones

	def update_manual_drones_status(self):
		"""
		Update the list of manual drones.
		"""
		self.manual_drones = [drone for drone in self.manual_drones if drone.manual_mode]

	def toggle_manual_mode(self):
		"""
		Toggle manual mode.
		"""
		self.manual_mode = not self.manual_mode

	def get_target_num_available(self, has_all_manual):
		"""
		Return the number of ("waiting") drones to reserve for manual mode.
		has_all_manual: Is the list of manual drones full? 
						(see self.num_allocated_manual and self.manual_drones)
		"""
		if has_all_manual and self.greedy:
			# In greedy allocation, reserve one less drone for manual mode
			# if it already has the correct number of manual drones.
			return max(1, self.num_allocated_manual - 1)
		return self.num_allocated_manual

	def update(self, current_time):
		self.update_manual_drones_status()
		has_all_manual = len(self.manual_drones) == self.num_allocated_manual

		# Find all available drones.
		available_drones = self.available_drones()

		# Calculate number of drones to use for auto mode.
		num_available_drones = self.get_target_num_available(has_all_manual)
		
		# Assign allowed number of drones (leave some for the manual mode)
		while len(available_drones) > num_available_drones:
			drone = available_drones.pop()
			drone.set_status("ready")

		# Assign manual drones until the number of assigned drones is equal to the target number of manual drones
		if self.manual_mode:
			if not has_all_manual:
				# Available drones after auto mode drones have been assigned.
				available_drones = self.available_drones()
				if available_drones:
					available_drone = available_drones.pop()
					available_drone.manual_mode = True
					available_drone.set_status("ready")
					self.manual_drones.append(available_drone)
				else:
					print("Awaiting available drone for manual mode!")

		# Update drones
		for drone in self.drones:
			drone.update(self.paths, current_time)

	def __str__(self):
		"""
		String representation of a mission object.
		"""
		repr_s = ""
		manual_status = "ON" if self.manual_mode else "OFF"
		for drone in self.drones:
			repr_s += str(drone)
			if drone is self.drones[0]: # First drone
				repr_s += f"\t\t Manual mode: {manual_status}, Num allocated: {self.num_allocated_manual}, Greedy: {self.greedy}"
			repr_s += "\n"
		repr_s += "\n"
		return repr_s	

def main():
	pygame.display.set_mode((100, 100))
	NUM_DRONES = 10 # Number of drones.
	NUM_PATHS = 7 # Number of paths.
	GREEDY = False # Greedy assignment of auto drones?
	mission = Mission(NUM_DRONES, NUM_PATHS, GREEDY) # Initialize mission
	t = 0

	while True:
		time = int(t)
		mission.update(time)
		os.system('cls')
		print(f"{time=}")
		print(str(mission))

		# Keyboard events.
		# m: toggle manual mode
		# w: increase number of manual drones
		# s: decrease number of manual drones 
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_m:
					mission.toggle_manual_mode()
				if event.key == pygame.K_w:
					mission.num_allocated_manual += 1
				if event.key == pygame.K_s:
					if mission.num_allocated_manual > 1:
						mission.num_allocated_manual -= 1

		t += 0.08

if __name__ == '__main__':
	main()