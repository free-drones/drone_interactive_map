from IMM.drone_manager.node import Node
from IMM.drone_manager.route import Route

def generate_dummy_route(offset=0):
    """ Generate a Route object with offset to the north by approximately offset kilometers (offset vs ) """
    route_simple = [
        f"{58.407910+offset*0.01}, {15.596624}",
        f"{58.408582+offset*0.01}, {15.596526}",
        f"{58.408631+offset*0.01}, {15.597775}",
        f"{58.407848+offset*0.01}, {15.597987}"
    ]

    route_nodes = [Node(as_string=pos) for pos in route_simple]
    return Route(nodes=route_nodes)