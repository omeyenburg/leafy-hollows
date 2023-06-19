# pip install opensimplex
# pip install noise

import pygame
import opensimplex
import numpy
import noise
import random



pygame.init()
window = pygame.display.set_mode((500, 500))


world = numpy.zeros((50, 50))

clock = pygame.time.Clock()

while True:
    seed = random.randint(-999999, 999999)
    window.fill((0, 0, 0))
    opensimplex.seed(seed)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            import sys
            sys.exit()
    for x, y in numpy.ndindex(world.shape):
        world[x, y] = opensimplex.noise2(x=x / 10, y=y / 10)
        way_Y = abs(y - noise.pnoise1(x / 100 + seed) * 20 - 25)
        way_H = (noise.pnoise1(x + seed) + 2) * 2
        way_M = max(0, way_H - way_Y) ** 3
        if world[x, y] < max(0.1 - way_M, 0) and way_M < 2:
            pygame.draw.rect(window, (255, 255, 255), (x*10, y*10, 10, 10))
    pygame.display.flip()
    clock.tick(1)
