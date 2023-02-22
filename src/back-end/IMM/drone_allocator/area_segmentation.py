import numpy as np

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

    def nodes(self):
        return [self.a, self.b, self.c]


class Polygon():
    def __init__(self, nodes):
        #assert len(nodes) >= 3
        self.nodes = nodes

    def triangulate(self):
        nodes = self.nodes[:]
        print (f"Polygon is clockwise: { Polygon.is_clockwise(nodes)}")
        if Polygon.is_clockwise(nodes):
            nodes = nodes[::-1]
        triangles = []

        while len(nodes) >= 3:
            triangle, index = Polygon.get_ear(nodes)
            del nodes[index]
            if triangle:
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

        return signed_area > 0

    @staticmethod
    def get_ear(nodes):
        num_nodes = len(nodes)
        if num_nodes == 3:
            print("We only have 3 nodes!!! Woah!")
            return Triangle(nodes), 0
        isEar = False
        
        for index, node in enumerate(nodes):
            # Construct a triangle from prev, curr, and next node
            print("Let's create a triangle!")
            triangle = Triangle([nodes[(index-1) % num_nodes], node, nodes[(index+1) % num_nodes]])
            print("Check convex")
            if triangle.isConvex():
                for point in nodes:
                    print("Let's check if it contains pblpslbepsbl")
                    print(f"Node: ({point[0], point[1]})")
                    if not point in triangle.nodes() and triangle.contains(point):
                        isEar = True
                if not isEar:
                    return triangle, index
        print("Did not find ear???")
        return None, 0

    def __repr__(self):
        pass
