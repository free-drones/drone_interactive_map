import numpy as np
from bisect import insort
import mapbox_earcut as earcut

from utility import coordinate_conversion
from IMM.drone_manager.route import Route



def angle_diff(angle_a, angle_b):
    """ Calculate the angle difference between two angles accounting for the angle period """
    return np.mod(angle_b - angle_a + np.pi, 2*np.pi) - np.pi

# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------

class Triangle:
    """
    Triangles defined by a set of three nodes of utm coordinates to simplify calculations on an arbitrarily shaped polygon.
    """
    def __init__(self, nodes):
        self.a = nodes[0]
        self.b = nodes[1]
        self.c = nodes[2]
        self.bounding_box = self.create_bounding_box()

    def isConvex(self):
        """ Return True if the angle formed by BAC is convex """
        ab = (self.b.x - self.a.x, self.b.y - self.a.y)
        ac = (self.c.x - self.a.x, self.c.y - self.a.y)
        
        cross_product = np.cross(ab, ac)
        return cross_product >= 0

    @staticmethod
    def area(a, b, c):
        """ Return the area of a triangle formed by the nodes a, b and c """
        return abs((a.x * (b.y - c.y) \
		+ b.x * (c.y - a.y) \
		+ c.x * (a.y - b.y)) / 2.0)
    
    def create_bounding_box(self):
        """ Calculate the bounding box of the triangle, store and return extreme points in a dictionary """
        dic = {}
        x_coords = [node.x for node in self.nodes()]
        y_coords = [node.y for node in self.nodes()]
        dic["x_min"] = min(x_coords)
        dic["x_max"] = max(x_coords)
        dic["y_min"] = min(y_coords)
        dic["y_max"] = max(y_coords)
        return dic

    def is_within_bounding_box(self, point):
        """ Return True if the given point is within the bounding box """
        outside_x = point.x < self.bounding_box["x_min"] or point.x > self.bounding_box["x_max"]
        outside_y = point.y < self.bounding_box["y_min"] or point.y > self.bounding_box["y_max"]
        return not (outside_x or outside_y)

    def contains(self, point):
        """ Return True if the given point is within the triangle """
        if not self.is_within_bounding_box(point):
            return False
        # Calculate the area of each sub-triangle created by the point and each pairwise combination of point a, b and c.
        # The point is inside the triangle if the sum of these areas is the same as the area of the triangle itself.
        ABC_area = Triangle.area(self.a, self.b, self.c)
        PBC_area = Triangle.area(point, self.b, self.c)
        PAC_area = Triangle.area(point, self.a, self.c)
        PAB_area = Triangle.area(point, self.a, self.b)
        
        # ABC is the original triangle and PBC, PAC, PAB are the sub-triangles created with the parameter 'point'.
        return int(ABC_area) == int(PBC_area + PAC_area + PAB_area)

    def nodes(self):
        """ Return the nodes of the triangle as a list """
        return [self.a, self.b, self.c]


class Polygon:
    """
    Creates a polygon from an ordered list of nodes defining an area of interest. Can call helper functions to create nodes and segments to process the area. 
    
    """
    def __init__(self, node_list):
        self.nodes = [Node((node_dict["lat"], node_dict["long"])) for node_dict in node_list]
        self.bounding_box = {}
        self.triangles = []
        self.node_grid = []
        self.segments = []
    
    def create_area_segments(self, node_spacing, start_location, num_seg):
        """ This is the main function to perform area segmentation and calls the necessary helper functions in correct order
            Create area segments of the polygon instance:
                1. Define the polygons bounding box
                2. Triangulate the polygon
                3. Create a node grid inside the polygon
                4. Segmentate the polygon into 'num_seg' segments
        """
        self.bounding_box = self.create_bounding_box()
        self.triangles = self.earcut_triangulate()
        self.node_grid = self.create_node_grid(node_spacing)
        self.update_area_segments(start_location, num_seg)

    def update_area_segments(self, start_location, num_seg):
        """ Create new segments with the given start location and number of segments """
        self.set_node_angles(start_location)
        self.segments = self.create_segments(num_seg)
        
    def plan_routes(self, start_location, drones, drone_data_lock):
        """  """
        if len(self.segments) != len(drones):
            self.update_area_segments(start_location, len(drones))
        
        drone_route_dict = dict()

        available_drones = [drone for drone in drones if not drone.route]
        for seg in self.segments:    
            # Greedy assignment
            closest_drone = None
            closest_dist = float('inf')
            closest_neighbor = None
            for drone in available_drones:
                with drone_data_lock:
                    drone_location = Node((drone.lat, drone.lon))
                closest_node = drone_location.closest_node(seg.owned_nodes)
                dist = closest_node.distance_to(drone_location)
                if dist < closest_dist:
                    closest_drone = drone
                    closest_dist = dist
                    closest_neighbor = closest_node

            with drone_data_lock:
                available_drones.remove(closest_drone)
                seg.plan_route(start_location=Node((closest_drone.lat, closest_drone.lon), start_neighbor=closest_neighbor))

            drone_route_dict[closest_drone] = seg.route

        return drone_route_dict

    def earcut_triangulate(self):
        """ Triangulate the polygon using the Ear Clipping algorithm and return the triangles as a list """
        nodes = np.array([node() for node in self.nodes]).reshape(-1, 2) # Convert node list to a np array
        rings = np.array([len(nodes)]) # Used to describe the geometry of the polygon. Can be used to define holes inside the polygon. (We don't)
        result = earcut.triangulate_float32(nodes, rings) # List of node indices defining the triangles
        triangles = []

        for i in range(0, len(result), 3): # Iterate over all such found triangles to create the triangle objects.
            
            triangle = Triangle([self.nodes[result[i]], self.nodes[result[i + 1]], self.nodes[result[i + 2]]])
            triangles.append(triangle)

        return triangles
    
    def create_bounding_box(self):
        """ Calculate the bounding box of the polygon, store and return its extreme points in a dictionary """
        dic = {}
        x_coords = [node.x for node in self.nodes]
        y_coords = [node.y for node in self.nodes]
        dic["x_min"] = min(x_coords)
        dic["x_max"] = max(x_coords)
        dic["y_min"] = min(y_coords)
        dic["y_max"] = max(y_coords)
        return dic 

    def create_node_grid(self, node_spacing):
        """ Evenly distribute a node grid inside the polygon and return a sorted list of the nodes according to the nodes angle relative 'start_location' 
            'node_spacing' decides the distance between each node in the created grid
        """
        node_grid = []
        self.bounding_box = self.create_bounding_box()
        
        x_min, x_max = self.bounding_box["x_min"], self.bounding_box["x_max"]
        y_min, y_max = self.bounding_box["y_min"], self.bounding_box["y_max"]

        for x in np.arange(x_min, x_max, node_spacing):
            for y in np.arange(y_min, y_max, node_spacing):
                for triangle in self.triangles:
                    node = Node(utm_coordinates=(x, y))

                    if triangle.contains(node):
                        # Find the zone num/letter of the closest node in the polygon node list.
                        # This is because the nodes are created with UTM coordinates, and the lat/lon coordinates
                        # are unknown, which means that the zone information cannot be derived.
                        node.derive_latlon(self.nodes)
                        
                        node_grid.append(node)
                        break
        return node_grid    
    
    def create_segments(self, num_seg):
        """ Evenly partition the amount of node grid nodes into segments 
            Node grid list is presumed to be sorted according to angle relative 'start_location' so resulting segments will be lines drawn from 'start_location'      
        """
        assert num_seg > 0, "Number of segments must be a positive integer"

        total_node_count = 0
        segments = []
        num_nodes = int(np.ceil(len(self.node_grid) / num_seg))
        while total_node_count < len(self.node_grid):
            seg_nodes = self.node_grid[total_node_count : total_node_count + num_nodes]
            segments.append(Segment(seg_nodes))
            total_node_count += num_nodes
        return segments

    def max_diff_angle(self, start_location):
        """ Calculate the difference between (start_location, a) and (start_location, b) for
         each node combination (a and b), and return the angle from the pair with the greatest difference """
        max_separation = 0
        chosen_nodes = (None, None)
        for node_a in self.nodes:
            for node_b in self.nodes:
                if node_a is node_b:
                    continue
                angular_separation = np.abs(start_location.angle_to(node_a) - start_location.angle_to(node_b))
                if angular_separation > max_separation:
                    chosen_nodes = (node_a, node_b)
                    max_separation = angular_separation
        return start_location.angle_to(chosen_nodes[0])
    
    def set_node_angles(self, start_location):
        """ Sort node grid based on individual nodes' angle to 'start_location' """
        max_diff_ang = self.max_diff_angle(start_location)

        self.node_grid.sort(key=lambda n: angle_diff(start_location.angle_to(n), max_diff_ang))

    @staticmethod
    def is_clockwise(nodes):
        """ Return True if the polygon created by the 'nodes' list is defined in a clockwise order """
        signed_area = 0
        num_nodes = len(nodes)

        for i in range(num_nodes):
            x1, y1 = nodes[i]
            x2, y2 = nodes[(i + 1) % num_nodes]
            signed_area += (x2 - x1) * (y2 + y1)

        return signed_area <= 0

class Node:
    """
    Handles coordinate pairs interpreted as nodes and performs conversions and calculations relative to the node instance. 
    Takes lat lon coordinates, and optionally utm coordinates, as input. If created without utm coordinates they are then derived from lat lon. 
    See utility/coodrinate_conversion.py for details pertaining to UTM coordinates and conversion.

    UTM coordinates are always known, since they are either derived from lat/lon or assigned directly.
    UTM zone information is derived directly if the node is initialized with latitude and longitude and must
    otherwise be derived from another node.
    """
    def __init__(self, coordinates=None, utm_coordinates=None):
        assert coordinates or utm_coordinates, "Node must be initialized with either latlon or utm coordinates!"

        if coordinates:
            self.lat, self.lon = coordinates

            # Calculate utm data from lat, lon
            utm_x, utm_y, zone_num, zone_letter = coordinate_conversion.utm_from_latlon(*coordinates)
            self.zone_number, self.zone_letter = zone_num, zone_letter

            if not utm_coordinates:
                utm_coordinates = utm_x, utm_y
        else:
            self.lat = None
            self.lon = None
            self.zone_number = None
            self.zone_letter = None
        
        self.x, self.y = utm_coordinates
        

    def angle_to(self, other_node):
        """ Return the angle in radians of the node instance to the 'other_node' """
        return np.arctan2(other_node.y - self.y, other_node.x - self.x)

    def __call__(self):
        """ Return the coordinates as a tuple when a node object is called """
        return (self.x, self.y)
    
    def distance_to_squared(self, other_node):
        """ Return distance between self and another node squared """
        return ((other_node.x-self.x)**2 + (other_node.y-self.y)**2)
    
    def distance_to(self, other_node):
        """ Return distance between self and another node """
        return np.sqrt((other_node.x-self.x)**2 + (other_node.y-self.y)**2)
    
    def closest_node(self, node_ls):
        """ Return the node closest to 'node' among 'owned_nodes' """
        min_dist = float('inf')
        closest_node = node_ls[0]
        for comp_node in node_ls:
            if comp_node is self:
                continue
            distance = self.distance_to(comp_node)
            if distance < min_dist:
                min_dist = distance
                closest_node = comp_node
        return closest_node

    @staticmethod
    def from_average_location(nodes):
        """ 
        Return a Node object that contains the average position 
        """
        assert nodes, "'nodes' must not be empty!"

        avg_node = Node(utm_coordinates=(0, 0))
        for node in nodes:
            avg_node.x += node.x
            avg_node.y += node.y
        avg_node.x /= len(nodes)
        avg_node.y /= len(nodes)
        
        avg_node.derive_latlon(nodes)
        return avg_node
        
    def derive_utm_zone(self, nodes):
        """ 
        Derive the UTM zone information (number, letter) from the closest node in 'nodes'
        Set the zone number and zone letter accordingly. 
        At least one node in 'nodes' must contain UTM zone information.
        """
        # Nodes that contain utm zone information, i.e where zone_number and zone_letter are not None
        nodes_with_utm_zone = [node for node in nodes if node.zone_number and node.zone_letter]
        if not nodes_with_utm_zone:
            raise ValueError("No nodes with zone information are present in 'nodes'")

        closest_node = self.closest_node(nodes_with_utm_zone)
        self.zone_number = closest_node.zone_number
        self.zone_letter = closest_node.zone_letter

    def set_latlon(self):
        """ 
        Convert the UTM coordinates to lat/lon coordinates and set self.lat and self.lon accordingly.
        Assumes that zone information is known. 
        """
        assert self.zone_number, "Zone number is not defined!"
        assert self.zone_letter, "Zone letter is not defined!"

        latlon = coordinate_conversion.utm_to_latlon(self.x, self.y, self.zone_number, self.zone_letter)
        self.lat = latlon[0]
        self.lon = latlon[1]

    def latlon_dict(self):
        """ Return latitude and longitude as a dictionary """
        assert self.lat and self.lon, "Latitude and longitude are undefined!"

        latlon_dict = {"lat": self.lat, "lon": self.lon}
        return latlon_dict

    def derive_latlon(self, nodes):
        """
        Derive the latitude and longitude from the closest node in 'nodes'
        At least one node in 'nodes' must contain UTM zone information.
        """
        self.derive_utm_zone(nodes)
        self.set_latlon()
    
    def __repr__(self):
        """ String representation of a node object. """
        return f"Node: UTM data: ({self.x}, {self.y}), Zone: {self.zone_number}{self.zone_letter}:"
    
class Segment:
    """
    Representation of a sub area within the polygon containing all nodes within this sub area. Can plan route between the segments nodes.
    """
    def __init__(self, owned_nodes):
        self.owned_nodes = owned_nodes
        self.route = None

    #def route_dicts(self):
    #    """ Convert the route list owned by the segment from utm coordinates to dictionaries containing latitude and longitude """
    #    return [node.latlon_dict() for node in self.route]

    def plan_route(self, start_location, start_neighbour=None):
        """ Plan a route using nearest insert algorithm with a segments owned nodes """
        if not start_neighbour:
            start_neighbour = start_location.closest_node(self.owned_nodes)

        # Insert 'start_location' as a node in the route
        new_route = [start_location, start_neighbour]
        unexplored_nodes = self.owned_nodes[:]
        while (len(new_route) - 1) < len(self.owned_nodes):
            min_insert_cost = float('inf')
            for i in range(len(new_route) - 1):
                node_A = new_route[i]
                node_B = new_route[i + 1]
                for unexplored_node in unexplored_nodes:
                    if unexplored_node in new_route:
                        continue
                    # Cost to insert 'unexplored_node' between 'node_A' and 'node_B'
                    distance = node_A.distance_to(unexplored_node) + node_B.distance_to(unexplored_node)
                    if distance < min_insert_cost:
                        min_insert_cost = distance
                        insert_index = i
                        insert_node = unexplored_node
            new_route.insert(insert_index + 1, insert_node)
            unexplored_nodes.remove(insert_node)
        #new_route.remove(start_location)
        route = Route([node.latlon_dict() for node in new_route], as_dicts=True)
        self.route = route

