# pip install opensimplex
# pip install perlin-noise

import pygame
import opensimplex
import numpy
from perlin_noise import PerlinNoise

noise = PerlinNoise()
print(noise(0.5))

opensimplex.random_seed()

pygame.init()
w = pygame.display.set_mode((500, 500))

#n = opensimplex.noise2(x=10, y=10)
#rng = numpy.random.default_rng(seed=0)
#ix, iy = rng.random(50), rng.random(50)
#world = opensimplex.noise2array(ix, iy)

world = numpy.zeros((50, 50))

for x, y in numpy.ndindex(world.shape):
    world[x, y] = opensimplex.noise2(x=x / 10, y=y / 10)
    way_Y = y - noise(x / 1) * 30 - 25#
    #print(noise(x / 1) * 30)
    if world[x, y] < 0.2 and abs(way_Y) > 3:
        pygame.draw.rect(w, (255, 255, 255), (x*10, y*10, 10, 10))
pygame.display.flip()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            import sys
            sys.exit()
