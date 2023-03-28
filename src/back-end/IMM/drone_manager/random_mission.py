# Example of how to generate a random mission

'''Function to construct a new mission based on current position and a
given area '''
def generate_random_mission(self, n_wps):
    #Compute distance from start position
    mission = {}
    current_wp = Waypoint()
    current_wp.copy_lla(self.drone_pos)
    for wp_id in range(0, n_wps):
        (_, _, _, d_start, _, bearing) = get_3d_distance(self.start_pos, current_wp)
        if d_start <= self.delta_r_max - self.wp_dist:
            #Safe to generate a random point (meter)
            delta_dir = np.random.uniform(-np.pi, np.pi)
        else:
            #move back towards start pos
            delta_dir = (bearing + 2*np.pi) % (2 * np.pi) - np.pi
            #Compute new lat lon
            d_northing = self.wp_dist*np.cos(delta_dir)
            d_easting = self.wp_dist*np.sin(delta_dir)
            (d_lat, d_lon) = ne_to_ll(current_wp, d_northing, d_easting)
            new_lat = current_wp.lat + d_lat
            new_lon = current_wp.lon + d_lon
            # Compute new altitude
            new_height = current_wp.alt - self.start_pos.alt + np.random.uniform(-2.0, 2.0)
            new_alt = self.start_pos.alt + min(self.height_max, max(self.height_min, new_height))
            current_wp.set_lla(new_lat, new_lon, new_alt)
            id_str = "id%d" % wp_id
        mission[id_str] = {
        "lat" : new_lat, "lon": new_lon, "alt": new_alt, "alt_type": "amsl", "heading": "course", "speed": self.default_speed
        }
    # Add start position as final wp
    id_str = "id%d" % n_wps
    mission[id_str] = {
        "lat" : self.start_pos.lat, "lon": self.start_pos.lon, "alt": new_alt, "alt_type": "amsl", "heading": "course", "speed": self.default_speed
    }
    return mission