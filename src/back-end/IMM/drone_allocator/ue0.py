import area_segmentation as seg
import sys
import numpy as np
import pygame as ue

import colorsys

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

    DRAW_POLYGON = True
    DRAW_NODE_GRID = True
    DRAW_SEGMENTS = True
    DRAW_TRIANGLES = False
    DRAW_PATHS = True

    ue.init()
    clock = ue.time.Clock()

    screen = ue.display.set_mode((WIDTH, HEIGHT))
    surface = ue.Surface((WIDTH, HEIGHT), ue.SRCALPHA)

    polygon = seg.Polygon([])

    colors = []
    for i in range(NUM_SEG):
        rgb = colorsys.hsv_to_rgb(1.0/(i+1), 1.0, 1,1)
        colors.append((rgb[0]*255, rgb[1]*255, rgb[2]*255, 100))

    while True:
        clock.tick(60)

        surface.fill(WHITE)
        screen.blit(surface, (0,0))

        if DRAW_SEGMENTS:
            for i, segment in enumerate(polygon.segments):
                # -- Draw start line
                start_angle = segment.owned_nodes[0].angle_to_start
                start_position = seg.Node((START_LOCATION.x + line_length * np.cos(start_angle), \
                                        START_LOCATION.y + line_length * np.sin(start_angle)))

                # -- Draw end line
                end_angle = segment.owned_nodes[-1].angle_to_start
                end_position = seg.Node((START_LOCATION.x + line_length * np.cos(end_angle), \
                                        START_LOCATION.y + line_length * np.sin(end_angle)))

                ue.draw.polygon(surface, colors[i], (START_LOCATION(), start_position(), end_position()))

        if DRAW_POLYGON:
            for i, node in enumerate(polygon.nodes):
                next = polygon.nodes[(i+1) % len(polygon.nodes)]
                ue.draw.aaline(surface, BLACK, node(), next())
                ue.draw.circle(surface, RED, node(), 5)
        
        if DRAW_TRIANGLES:
            for triangle in polygon.triangles:
                for i, node in enumerate(triangle.nodes()): 
                    next = triangle.nodes()[(i + 1) % 3]
                    ue.draw.aaline(surface, GREEN, node(), next())

        if DRAW_NODE_GRID:
            for node in polygon.node_grid:
                ue.draw.circle(surface, BLUE, node(), 2)

        if DRAW_SEGMENTS:
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

        if DRAW_PATHS:
            for segment in polygon.segments:
                for i in range(len(segment.route) - 1):
                    ue.draw.aaline(surface, BLACK, segment.route[i](), segment.route[i+1]())
                    
                ue.draw.aaline(surface, BLACK, segment.route[0](), segment.route[-1]())
                

        screen.blit(surface, (0,0))

        if ue.key.get_pressed()[ue.K_f] and polygon.triangles:
            mouse_pos = ue.mouse.get_pos()
            START_LOCATION = seg.Node(mouse_pos)
            polygon.update_area_segments(START_LOCATION, NUM_SEG)

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
                    polygon.create_area_segments(SPACING, START_LOCATION(), NUM_SEG)
                if ue.key.get_pressed()[ue.K_t]:
                    polygon.triangles = polygon.earcut_triangulate()
                if ue.key.get_pressed()[ue.K_g]:
                    polygon.node_grid = polygon.create_node_grid(SPACING, START_LOCATION())
                if ue.key.get_pressed()[ue.K_c]:
                    polygon.nodes.clear()
                    polygon.triangles.clear()
                    polygon.node_grid.clear()
                    polygon.segments.clear()
                if ue.key.get_pressed()[ue.K_k]:
                    for segment in polygon.segments:
                        segment.smooth_route()

                if ue.key.get_pressed()[ue.K_1]:
                    DRAW_POLYGON = not DRAW_POLYGON
                if ue.key.get_pressed()[ue.K_2]:
                    DRAW_TRIANGLES = not DRAW_TRIANGLES
                if ue.key.get_pressed()[ue.K_3]:
                    DRAW_NODE_GRID = not DRAW_NODE_GRID
                if ue.key.get_pressed()[ue.K_4]:
                    DRAW_SEGMENTS = not DRAW_SEGMENTS
                if ue.key.get_pressed()[ue.K_5]:
                    DRAW_PATHS = not DRAW_PATHS

        ue.display.update()

if __name__ == "__main__":
    main()