import numpy as np
from bisect import insort
import mapbox_earcut as earcut



class Triangle():
    def __init__(self, nodes):
        self.a = nodes[0]
        self.b = nodes[1]
        self.c = nodes[2]
        self.area = self.area(self.a, self.b, self.c)
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

    def check_bounding_box(self, point):
        """ Return True if the given point is within the bounding box """
        outside_x = point.x < self.bounding_box["x_min"] or point.x > self.bounding_box["x_max"]
        outside_y = point.y < self.bounding_box["y_min"] or point.y > self.bounding_box["y_max"]
        return not (outside_x or outside_y)

    def contains(self, point):
        """ Return True if the given point is within the triangle """
        if not self.check_bounding_box(point):
            return False
        # Calculate the area of each sub-triangle created by the point and each pairwise combination of point a, b and c.
        # The point is inside the triangle if the sum of these areas is the same as the area of the triangle itself.
        ABC_area = Triangle.area(self.a, self.b, self.c)
        PBC_area = Triangle.area(point, self.b, self.c)
        PAC_area = Triangle.area(point, self.a, self.c)
        PAB_area = Triangle.area(point, self.a, self.b)
        
        # ABC is the original triangle and PBC, PAC, PAB are the sub-triangles created with the parameter 'point'.
        return ABC_area == PBC_area + PAC_area + PAB_area

    def nodes(self):
        """ Return the nodes of the triangle as a list """
        return [self.a, self.b, self.c]


class Polygon():
    def __init__(self, node_dict):
        self.nodes = [Node(node["lat" ], node["long"]) for node in node_dict]
        self.bounding_box = {}
        self.triangles = []
        self.node_grid = []
        self.segments = []
    
    def create_area_segments(self, node_spacing, start_location, num_seg):
        """ This is the main function to perform area segmentation and calls the necessary helper functions in correct order
            Create area segments of the polygon instance:
                1. Triangulate the polygon
                2. Define the polygons bounding box
                3. Create a node grid inside the polygon
                4. Segmentate the polygon into 'num_seg' segments
        """
        self.triangles = self.earcut_triangulate()
        self.bounding_box = self.create_bounding_box()
        self.node_grid = self.create_node_grid(node_spacing, start_location)
        self.update_area_segments(node_spacing, start_location, num_seg)
 
    def update_area_segments(self, node_spacing, start_location, num_seg):
        """ Create new segments with the given node spacing, start location, and number of segments """
        self.set_node_angles(start_location)
        self.segments = self.create_segments(num_seg)
        for seg in self.segments:
            seg.plan_route(start_location)

    def earcut_triangulate(self):
        """ Triangulate the polygon using the Ear Clipping algorithm and return the triangles as a list """
        nodes = np.array([node() for node in self.nodes]).reshape(-1, 2) # Convert node list to a np array
        rings = np.array([len(nodes)]) # Used to describe the geometry of the polygon. Can be used to define holes inside the polygon. (We don't)
        result = earcut.triangulate_int32(nodes, rings) # List of node indices defining the triangles
        triangles = []
        for i in range(0, len(result), 3): # Iterate over all such found triangles to create the triangle objects.
            triangle = Triangle([self.nodes[result[i]], self.nodes[result[i+1]], self.nodes[result[i+2]]])
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

    def create_node_grid(self, node_spacing, start_location):
        """ Evenly distribute a node grid inside the polygon and return a sorted list of the nodes according to the nodes angle relative 'start_location' 
            'node_spacing' decides the distance between each node in the created grid
        """
        node_grid = []
        self.bounding_box = self.create_bounding_box()
        max_diff_ang = self.max_diff_angle(start_location)
        for x in range(self.bounding_box["x_min"], self.bounding_box["x_max"], node_spacing):
            for y in range(self.bounding_box["y_min"], self.bounding_box["y_max"], node_spacing):
                for triangle in self.triangles:
                    node = Node((x, y))
                    if triangle.contains(node):
                        node.angle_to_start = start_location.angle_to(node)
                        node_grid.append(node)
                        break
        node_grid.sort(key=lambda n: (n.angle_to_start - max_diff_ang), reverse=False)
        return node_grid    
    
    def create_segments(self, num_seg):
        """ Evenly partition the amount of node grid nodes into segments 
            Node grid list is presumed to be sorted according to angle relative 'start_location' so resulting segments will be lines drawn from 'start_location'      
        """
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
        def node_angle(angle_a, angle_b): # TODO: Move to util class or whatever
            return np.mod(angle_b - angle_a + np.pi, 2*np.pi) - np.pi
        max_diff_ang = self.max_diff_angle(start_location)
        for node in self.node_grid:
            node.angle_to_start = start_location.angle_to(node)
 
        self.node_grid.sort(key=lambda n: node_angle(n.angle_to_start, max_diff_ang), reverse=False)

    @staticmethod
    def is_clockwise(nodes):
        """ Return True if the polygon created by the 'nodes' list is defined in a clockwise order """
        signed_area = 0
        num_nodes = len(nodes)

        for i in range(num_nodes):
            x1, y1 = nodes[i]
            x2, y2 = nodes[(i+1) % num_nodes]
            signed_area += (x2 - x1) * (y2 + y1)

        return signed_area <= 0
        
    def __repr__(self):
        pass

class Node():
    def __init__(self, position):
        self.lat = position[0]
        self.lon = position[1]
        self.angle_to_start = None

    def angle_to(self, other_node):
        """ Return the angle in radians of the node instance to the 'other_node' """
        lat1, lon1 = self.to_radians()
        lat2, lon2 = other_node.to_radians()
        delta_lon = lon2 - lon1
        y = np.sin(delta_lon) * np.cos(lat2)
        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)
        theta = np.arctan2(y, x)
        bearing = (theta + 2*np.pi) % (2*np.pi)
        return bearing

    def __call__(self):
        """ Return the coordinates as a tuple when a node object is called """
        return (self.lat, self.long)
    
    def distance_to(self, other_node):
        """ Return distance between self and another node """
        R = 6371 # Radius of the earth in kilometers
        lat1, lon1 = self.to_radians()
        lat2, lon2 = other_node.to_radians()
        return np.arccos(np.sin(lat1)*np.sin(lat2) + 
                         np.cos(lat1)*np.cos(lat2)*np.cos(lon2 - lon1)) * R
    
    def to_radians(self):
        """ Return latitude and longitude as radians """
        return map(np.radians, [self.lat, self.lon])
    
class Segment():
    def __init__(self, owned_nodes):
        self.owned_nodes = owned_nodes
        self.route = []

    def route_dict(self):
        return [{"lat": node.x, "long": node.y} for node in self.route]

    def plan_route(self, start_location):
        """ Plan a route using nearest insert algorithm with a segments owned nodes """
        start_neighbour = self.closest_owned_node(start_location)
        # Insert 'start_location' as a node in the route
        new_route = [start_location, start_neighbour]
        unexplored_nodes = self.owned_nodes[:]
        while (len(new_route) - 1) < len(self.owned_nodes):
            min_insert_cost = float('inf')
            for i in range(len(new_route) - 1):
                node_A = new_route[i]
                node_B = new_route[i+1]
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
        self.route = new_route
                        

    def closest_owned_node(self, node):
        """ Returns the node closest to 'node' among 'owned_nodes' """
        min_dist = float('inf')
        closest_node = node
        for comp_node in self.owned_nodes:
            if comp_node is closest_node:
                continue
            distance = comp_node.distance_to(node)
            if distance < min_dist:
                min_dist = distance
                closest_node = comp_node
        return closest_node

    