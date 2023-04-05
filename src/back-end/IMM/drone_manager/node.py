
class Node():
    def __init__(self, lat, lon, altitude=1, weight=1):
        self.lat = lat
        self.lon = lon
        self.alt = altitude
        self.weight = weight
    
    # TODO: proper lat long distance calculation. Maybe use package "LatLon"
    def squared_distance_to(self, node):
        return ((self.lat - node.lat)**2 + (self.lon - node.lon)**2)