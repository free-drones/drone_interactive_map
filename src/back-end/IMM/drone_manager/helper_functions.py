from IMM.drone_manager.node import Node
from IMM.drone_manager.route import Route

def generate_dummy_route(offset=0):
    """ 
    Generate a 4-node long Route object in Linköping (Gottfridsberg) with 
    offset to the north by approximately offset kilometers
    """
    route_simple = [
        f"{58.407910+offset*0.01}, {15.596624}",
        f"{58.408582+offset*0.01}, {15.596526}",
        f"{58.408631+offset*0.01}, {15.597775}",
        f"{58.407848+offset*0.01}, {15.597987}"
    ]
    route_nodes = [Node(as_string=pos) for pos in route_simple]
    return Route(nodes=route_nodes)

def generate_dummy_route_skara(offset=0):
    """ 
    Generate a 4-node long Route object in Skara with offset to the north 
    by approximately offset kilometers.
    """

    point = {
        "lat": 58.38825737644909,
        "lon": 13.481121210496298
    }
    side = 0.001
    route_simple = [
        f"{point['lat']+offset*0.0015}, {point['lon']}",
        f"{point['lat']+side+offset*0.0015}, {point['lon']}",
        f"{point['lat']+side+offset*0.0015}, {point['lon']+side}",
        f"{point['lat']+offset*0.0015}, {point['lon']+side}"
    ]
    route_nodes = [Node(as_string=pos) for pos in route_simple]
    return Route(nodes=route_nodes)

def generate_long_dummy_route():
    """ 
    Generate a one-node long Route object in Ängaryd, Tranås.
    """
    route_simple = [f"{58.039200}, {14.963250}"]
    route_nodes = [Node(as_string=pos) for pos in route_simple]
    return Route(nodes=route_nodes)