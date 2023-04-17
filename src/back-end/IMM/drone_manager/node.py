from IMM.drone_manager.dm_config import ALTITUDE, GROUND_LEVEL


class Node():
    
    def __init__(self, lat=0, lon=0, altitude=(ALTITUDE + GROUND_LEVEL), weight=1, as_string=None):
        """
        Create a Node either with lat, lon OR as a string on the form "lat, lon"
        """
        self.lat = lat
        self.lon = lon
        self.alt = altitude
        self.weight = weight
        if as_string is not None:
            self._str_to_node(as_string)
    
    # TODO: proper lat long distance calculation. Maybe use package "LatLon"
    def squared_distance_to(self, node):
        return ((self.lat - node.lat)**2 + (self.lon - node.lon)**2)
    
    def _str_to_node(self, string):
        lat, lon = string.split(", ")
        self.lat, self.lon = float(lat), float(lon)

    def __repr__(self):
        return f"{str(self.lat).ljust(9, '0')}, {str(self.lon).ljust(9, '0')}"