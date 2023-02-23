import area_segmentation as seg
import sys
import pygame as ue

def main():
    WIDTH = 800
    HEIGHT = 600
    
    SPACING = 10
    START_LOCATION = seg.Node(100, 100)

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
    node_grid_list = []

    while True:
        clock.tick(60)

        surface.fill(WHITE)
        screen.blit(surface, (0,0))

        for i, node in enumerate(polygon.nodes):
            next = polygon.nodes[(i+1) % len(polygon.nodes)]
            ue.draw.aaline(surface, BLACK, node(), next())
            ue.draw.circle(surface, RED, node(), 5)
        
        for triangle in polygon.triangles:
            for i, node in enumerate(triangle.nodes()): 
                next = triangle.nodes()[(i + 1) % 3]
                ue.draw.aaline(surface, GREEN, node(), next())

        for node in polygon.node_grid:
            ue.draw.circle(surface, BLUE, node(), 2)

        screen.blit(surface, (0,0))

        for event in ue.event.get():
            if event.type == ue.QUIT or ue.key.get_pressed()[ue.K_ESCAPE]:
                ue.quit()
                sys.exit()

            if event.type == ue.MOUSEBUTTONDOWN and ue.mouse.get_pressed()[0]:
                mouse_pos = ue.mouse.get_pos()
                polygon.nodes.append(seg.Node(mouse_pos[0], mouse_pos[1]))
                
            if event.type == ue.KEYDOWN:
                if ue.key.get_pressed()[ue.K_s]:
                    polygon.gogo_gadget(SPACING, START_LOCATION)
                if ue.key.get_pressed()[ue.K_t]:
                    polygon.triangles = polygon.earcut_triangulate()
                if ue.key.get_pressed()[ue.K_g]:
                    polygon.node_grid = polygon.create_node_grid(SPACING)
                if ue.key.get_pressed()[ue.K_c]:
                    polygon.nodes.clear()
                    polygon.triangles.clear()

        ue.display.update()

if __name__ == "__main__":
    main()