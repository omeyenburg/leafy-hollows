import numpy
import random


CHUNK_SIZE = 32


class World:
    def __init__(self):
        self.PIXELS_PER_METER = 25

        self.chunks = {}      # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))

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
