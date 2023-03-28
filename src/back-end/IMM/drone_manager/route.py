
class Route():
    def __init__(self, nodes):
        self.nodes = nodes
    
    # reorder route, should be called after having arrived at the next node
    def update_route(self): # :(
        latest_node=self.nodes.pop(0)
        self.nodes.append(latest_node)

    def get_next_node(self):
        return self.nodes[0] if self.nodes else None

    def get_last_visited_node(self):
        return self.nodes[-1] if self.nodes else None
    
    def add_nodes(self, nodes):
        self.nodes.extend(nodes)

    def overwrite_nodes(self, nodes):
        self.nodes = nodes