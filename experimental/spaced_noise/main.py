import pygame
import random
import numpy
import noise as pnoise
import sys
pygame.init()
block_size = (5, 5)
size = (100, 100)
window = pygame.display.set_mode((block_size[0] * size[0], block_size[1] * size[1]))


def noise(x, y):
    return random.random() > 0.9


seed = random.random()
def noise(x, y):
    return pnoise.pnoise2(x + seed, y - seed/2) > 0.6


world = numpy.zeros(size)
for x in range(size[0]):
    for y in range(size[1]):
        if noise(x, y):
            world[x, y] = 1

while True:
    window.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    for x in range(size[0]):
        for y in range(size[1]):
            if world[x, y]:
                pygame.draw.rect(window, (255, 0, 0), (x * block_size[0], y * block_size[1], block_size[0], block_size[1]))

    pygame.display.flip()