import math

class Route():
    def __init__(self, nodes):
        self.nodes = nodes
        self.drone = None
    
    # The following functions are not currently used but will probably be helpful later

    # reorder route, should be called after having arrived at the next node
    def update_route(self, reuse_node=True):
        latest_node = self.nodes.pop(0)
        if reuse_node:
            self.nodes.append(latest_node)

    def get_next_node(self):
        return self.nodes[0] if self.nodes else None
    
    def add_nodes(self, nodes):
        self.nodes.extend(nodes)

    def squared_distance_to(self, node):
        dist = math.inf
        for n in self.nodes:
            d = node.squared_distance_to(n)
            if d < dist:
                dist = d
        return dist
        
    def __repr__(self):
        output = "\n"
        for node in self.nodes:
            output += f"{node}\n"
        return output
