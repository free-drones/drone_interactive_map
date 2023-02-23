import area_segmentation as seg
import sys
import pygame as ue

def main():
    WIDTH = 800
    HEIGHT = 600

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    #poly = ue.Polygon()


    ue.init()
    clock = ue.time.Clock()

    screen = ue.display.set_mode((WIDTH, HEIGHT))
    surface = ue.Surface((WIDTH, HEIGHT), ue.SRCALPHA)

    polygon = seg.Polygon([])
    triangles = []

    while True:
        clock.tick(60)

        surface.fill(WHITE)
        screen.blit(surface, (0,0))

        for i, node in enumerate(polygon.nodes):
            next = polygon.nodes[(i+1) % len(polygon.nodes)]
            ue.draw.aaline(surface, BLACK, node, next)
            ue.draw.circle(surface, RED, node, 5)
            #print(f"node: ({node[0]}, {node[1]})")
        
        for triangle in triangles:
            for i, node in enumerate(triangle.nodes()): 
                next = triangle.nodes()[(i + 1) % 3]
                ue.draw.aaline(surface, BLUE, node, next)

        screen.blit(surface, (0,0))

        for event in ue.event.get():
            if event.type == ue.QUIT or ue.key.get_pressed()[ue.K_ESCAPE]:
                ue.quit()
                sys.exit()

            if event.type == ue.MOUSEBUTTONDOWN and ue.mouse.get_pressed()[0]:
                mouse_pos = ue.mouse.get_pos()
                polygon.nodes.append(mouse_pos)
                
            if event.type == ue.KEYDOWN:
                if ue.key.get_pressed()[ue.K_t]:
                    triangles = polygon.earcut_triangulate()
                if ue.key.get_pressed()[ue.K_c]:
                    polygon.nodes.clear()
                    triangles.clear()

        ue.display.update()

if __name__ == "__main__":
    main()