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
# 
#
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

    def isConvex(self):
        ab = (self.b[0] - self.a[0], self.b[1] - self.a[1])
        ac = (self.c[0] - self.a[0], self.c[1] - self.a[1])
        
        cross_product = np.cross(ab, ac)
        return cross_product >= 0

    @staticmethod
    def area(a, b, c):
        return abs((a[0] * (b[1] - c[1]) \
		+ b[0] * (c[1] - a[1]) \
		+ c[0] * (a[1] - b[1])) / 2.0)

    def contains(self, point):
        ABC_area = Triangle.area(self.a, self.b, self.c)
        PBC_area = Triangle.area(point, self.b, self.c)
        PAC_area = Triangle.area(point, self.a, self.c)
        PAB_area = Triangle.area(point, self.a, self.b)
        
        return ABC_area == PBC_area + PAC_area + PAB_area

    def is_clockwise(self):
        signed_area = 0
        nodes = self.nodes()
        num_nodes = len(nodes)

        for i in range(num_nodes):
            x1, y1 = nodes[i]
            x2, y2 = nodes[(i+1) % num_nodes]
            signed_area += (x2 - x1) * (y2 + y1)

        return signed_area <= 0

    def nodes(self):
        return [self.a, self.b, self.c]


class Polygon():
    def __init__(self, nodes):
        #assert len(nodes) >= 3
        self.nodes = nodes

    def earcut_triangulate(self):
        nodes = np.array(self.nodes).reshape(-1, 2)
        rings = np.array([len(nodes)])
        result = earcut.triangulate_int32(nodes, rings)
        triangles = []
        for i in range(0, len(result), 3):
            triangle = Triangle([self.nodes[result[i]], self.nodes[result[i+1]], self.nodes[result[i+2]]])
            triangles.append(triangle)

        return triangles

    @staticmethod
    def is_clockwise(nodes):
        signed_area = 0
        num_nodes = len(nodes)

        for i in range(num_nodes):
            x1, y1 = nodes[i]
            x2, y2 = nodes[(i+1) % num_nodes]
            signed_area += (x2 - x1) * (y2 + y1)

        return signed_area <= 0

    def __repr__(self):
        pass
