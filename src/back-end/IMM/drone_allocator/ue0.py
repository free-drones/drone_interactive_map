import area_segmentation as seg
import sys
import numpy as np
import pygame as ue

def main():
    WIDTH = 800
    HEIGHT = 600
    
    SPACING = 25
    START_LOCATION = seg.Node((100, 100))
    NUM_SEG = 5
    # BYT UT SEN
    line_length = 800

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)


    ue.init()
    clock = ue.time.Clock()

    screen = ue.display.set_mode((WIDTH, HEIGHT))
    surface = ue.Surface((WIDTH, HEIGHT), ue.SRCALPHA)

    polygon = seg.Polygon([])

    while True:
        clock.tick(60)

        surface.fill(WHITE)
        screen.blit(surface, (0,0))

        for i, node in enumerate(polygon.nodes):
            next = polygon.nodes[(i+1) % len(polygon.nodes)]
            ue.draw.aaline(surface, BLACK, node(), next())
            ue.draw.circle(surface, RED, node(), 5)
        
        """for triangle in polygon.triangles:
            for i, node in enumerate(triangle.nodes()): 
                next = triangle.nodes()[(i + 1) % 3]
                ue.draw.aaline(surface, GREEN, node(), next())"""

        for node in polygon.node_grid:
            ue.draw.circle(surface, BLUE, node(), 2)

        for segment in polygon.segments:
            # -- Draw start line
            start_angle = segment.owned_nodes[0].angle_to_start
            end_position = seg.Node((START_LOCATION.x + line_length * np.cos(start_angle), \
                                    START_LOCATION.y + line_length * np.sin(start_angle)))
            ue.draw.aaline(surface, RED, START_LOCATION(), end_position())

            # -- Draw end line
            end_angle = segment.owned_nodes[-1].angle_to_start
            end_position = seg.Node((START_LOCATION.x + line_length * np.cos(end_angle), \
                                    START_LOCATION.y + line_length * np.sin(end_angle)))
            ue.draw.aaline(surface, BLUE, START_LOCATION(), end_position())

            for i in range(len(segment.route) - 1):
                ue.draw.aaline(surface, BLACK, segment.route[i](), segment.route[i+1]())
                
            ue.draw.aaline(surface, BLACK, segment.route[0](), segment.route[-1]())
            

        screen.blit(surface, (0,0))

        if ue.key.get_pressed()[ue.K_f] and polygon.triangles:
            mouse_pos = ue.mouse.get_pos()
            START_LOCATION = seg.Node(mouse_pos)
            polygon.node_grid = polygon.create_node_grid(SPACING, START_LOCATION)
            polygon.segments = polygon.create_segments(NUM_SEG)

        for event in ue.event.get():
            if event.type == ue.QUIT or ue.key.get_pressed()[ue.K_ESCAPE]:
                ue.quit()
                sys.exit()

            if event.type == ue.MOUSEBUTTONDOWN:
                mouse_pos = ue.mouse.get_pos()
                if ue.mouse.get_pressed()[0]:
                    polygon.nodes.append(seg.Node(mouse_pos))
                    if len(polygon.nodes) >= 3:
                        polygon.triangles = polygon.earcut_triangulate()
            
            if event.type == ue.MOUSEWHEEL:
                NUM_SEG += event.y
                NUM_SEG = max(1, NUM_SEG)

            if event.type == ue.KEYDOWN:
                if ue.key.get_pressed()[ue.K_s]:
                    polygon.create_area_segments(SPACING, START_LOCATION, NUM_SEG)
                if ue.key.get_pressed()[ue.K_t]:
                    polygon.triangles = polygon.earcut_triangulate()
                if ue.key.get_pressed()[ue.K_g]:
                    polygon.node_grid = polygon.create_node_grid(SPACING, START_LOCATION)
                if ue.key.get_pressed()[ue.K_c]:
                    polygon.nodes.clear()
                    polygon.triangles.clear()
                    polygon.node_grid.clear()
                    polygon.segments.clear()
        ue.display.update()

if __name__ == "__main__":
    main()