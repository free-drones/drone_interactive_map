import numpy as np
import mapbox_earcut as earcut

# Polygon
# node_list
#
# Bygga nodnät
# segments(source_position, num_active_drones) - kan ha utanför Polygon-klassen
# - Bestämma antal linjer
# - Stråla ut linjer med vinkel
# - (Iterativt) hitta vinkel på varje stråle för jämn indelning (av antal noder)  
# - 
# - Skapa nya polygoner från indelning
# - 
#
# Identifiera vilka noder som finns i Polygon
# 
# Triangulation 
#

# Utility:
#
#  
#
#
class Triangle():
    def __init__(self, nodes):
        self.a = nodes[0]
        self.b = nodes[1]
        self.c = nodes[2]
        self.area = self.area(self.a, self.b, self.c)
        self.bounding_box = self.create_bounding_box()

    def isConvex(self):
        # Checks if the angle formed by BAC
        ab = (self.b.x - self.a.x, self.b.y - self.a.y)
        ac = (self.c.x - self.a.x, self.c.y - self.a.y)
        
        cross_product = np.cross(ab, ac)
        return cross_product >= 0

    @staticmethod
    def area(a, b, c):
        # Return the area of a triangle formed by the nodes a, b and c
        return abs((a.x * (b.y - c.y) \
		+ b.x * (c.y - a.y) \
		+ c.x * (a.y - b.y)) / 2.0)
    
    def create_bounding_box(self):
        # Calculate the bounding box of the triangle and store extreme points in a dictionary
        dic = {}
        x_coords = [node.x for node in self.nodes()]
        y_coords = [node.y for node in self.nodes()]
        dic["x_min"] = min(x_coords)
        dic["x_max"] = max(x_coords)
        dic["y_min"] = min(y_coords)
        dic["y_max"] = max(y_coords)
        return dic

    def check_bounding_box(self, point):
        # Check if the given point is within the bounding box
        outside_x = point.x < self.bounding_box["x_min"] or point.x > self.bounding_box["x_max"]
        outside_y = point.y < self.bounding_box["y_min"] or point.y > self.bounding_box["y_max"]
        return not (outside_x or outside_y)

    def contains(self, point):
        # Check if the given point is within the triangle
        if not self.check_bounding_box(point):
            return False
        ABC_area = Triangle.area(self.a, self.b, self.c)
        PBC_area = Triangle.area(point, self.b, self.c)
        PAC_area = Triangle.area(point, self.a, self.c)
        PAB_area = Triangle.area(point, self.a, self.b)
        
        return ABC_area == PBC_area + PAC_area + PAB_area

    def nodes(self):
        # Return the nodes of the triangle as a list
        return [self.a, self.b, self.c]


class Polygon():
    def __init__(self, nodes):
        self.nodes = nodes
        self.bounding_box = {}
        self.triangles = []
        self.node_grid = []
    
    def gogo_gadget(self, node_spacing, start_location):
        # Find area segments
        self.triangles = self.earcut_triangulate()
        self.bounding_box = self.create_bounding_box()
        self.node_grid = self.create_node_grid(node_spacing)
        #........... Fortsättning följer ;)
        #
        #

    def earcut_triangulate(self):
        # Triangulate the polygon and return the triangles as a list
        nodes = np.array([node() for node in self.nodes]).reshape(-1, 2)
        rings = np.array([len(nodes)])
        result = earcut.triangulate_int32(nodes, rings)
        triangles = []
        for i in range(0, len(result), 3):
            triangle = Triangle([self.nodes[result[i]], self.nodes[result[i+1]], self.nodes[result[i+2]]])
            triangles.append(triangle)

        return triangles

    def create_bounding_box(self):
        # Calculate the bounding box of the polygon and store extreme points in a dictionary
        dic = {}
        x_coords = [node.x for node in self.nodes]
        y_coords = [node.y for node in self.nodes]
        dic["x_min"] = min(x_coords)
        dic["x_max"] = max(x_coords)
        dic["y_min"] = min(y_coords)
        dic["y_max"] = max(y_coords)
        return dic 

    def create_node_grid(self, node_spacing, start_location=None):
        # Create a node grid for the polygon
        node_grid = []
        self.bounding_box = self.create_bounding_box()
        for x in range(self.bounding_box["x_min"], self.bounding_box["x_max"], node_spacing):
            for y in range(self.bounding_box["y_min"], self.bounding_box["y_max"], node_spacing):
                for triangle in self.triangles:
                    node = Node(x, y)
                    if triangle.contains(node):
                        node_grid.append(node)
                        if start_location:
                            node.angle_to_start = node.angle_to(start_location)
                        break
        return node_grid

    @staticmethod
    def is_clockwise(nodes):
        # Check if the polygon is clockwise
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
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle_to_start = None
    
    def angle_to(self, other_node):
        return np.arctan2(other_node.y - self.y, other_node.x - self.x)

    def __call__(self):
        return (self.x, self.y)

class Segment():
    def __init__(self, start_location, start_angle, end_angle):
        self.start_location = start_location
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.owned_nodes = []