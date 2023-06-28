import numpy
import random


CHUNK_SIZE = 32


class World:
    def __init__(self):
        self.PIXELS_PER_METER = 25

        self.chunks = {} # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))

        # Chunk template, which can be copied later
        self.empty_chunk = numpy.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=int)

    def __getitem__(self, coord):
        return self.get_block(coord[0], coord[1])

    def __setitem__(self, coord, data):
        self.set_block(coord[0], coord[1], data)

    def create_chunk(self, chunk_coord):
        self.chunks[chunk_coord] = self.empty_chunk.copy()
        self.generate_chunk(chunk_coord)

    def set_block(self, x, y, data):
        chunk_x, mod_x = divmod(x, CHUNK_SIZE) # = (x // CHUNK_SIZE, x % CHUNK_SIZE)
        chunk_y, mod_y = divmod(y, CHUNK_SIZE) # = (y // CHUNK_SIZE, y % CHUNK_SIZE)

        if not (chunk_x, chunk_y) in self.chunks: # create chunk, if chunk is not generated
            self.create_chunk((chunk_x, chunk_y))
        self.chunks[(chunk_x, chunk_y)][mod_x, mod_y] = data
    
    def get_block(self, x, y, generate=1, default=0):
        chunk_x, mod_x = divmod(x, CHUNK_SIZE)
        chunk_y, mod_y = divmod(y, CHUNK_SIZE)
        if not (chunk_x, chunk_y) in self.chunks:
            if generate:
                self.create_chunk((chunk_x, chunk_y))
            else:
                return default
        return self.chunks[(chunk_x, chunk_y)][mod_x , mod_y]

    def generate_chunk(self, chunk_coord):
        for x, y in numpy.ndindex((CHUNK_SIZE, CHUNK_SIZE)):
            data = random.randint(0, 10)
            if data == 0:
                self.chunks[chunk_coord][x, y] = 1
            else:
                self.chunks[chunk_coord][x, y] = 0

    def draw(self, window):
        for x in range(-25, 20):
            for y in range(-25, 20):
                if self[x, y]:
                    rect = window.camera.map_coord((x * self.PIXELS_PER_METER, y * self.PIXELS_PER_METER, self.PIXELS_PER_METER, self.PIXELS_PER_METER))
                    window.draw_rect(rect[:2], rect[2:], (0, 255, 0))


"""
#World generation?


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

"""