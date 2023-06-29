import random
import numpy
import noise


CHUNK_SIZE = 32


class World:
    def __init__(self):
        self.SEED: float = random.randint(-99999, 99999) + random.random()

        self.chunks: dict = {} # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))
        self.empty_chunk: numpy.array = numpy.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=int) # Chunk template, which can be copied later

    def __getitem__(self, coord: [int]):
        return self.get_block(coord[0], coord[1])

    def __setitem__(self, coord: [int], data: int):
        self.set_block(coord[0], coord[1], data)

    def create_chunk(self, chunk_coord: [int]):
        self.chunks[chunk_coord] = self.empty_chunk.copy()
        self.generate_chunk(chunk_coord)

    def set_block(self, x: int, y: int, data: int):
        chunk_x, mod_x = divmod(x, CHUNK_SIZE) # (x // CHUNK_SIZE, x % CHUNK_SIZE)
        chunk_y, mod_y = divmod(y, CHUNK_SIZE) # (y // CHUNK_SIZE, y % CHUNK_SIZE)

        if not (chunk_x, chunk_y) in self.chunks: # create chunk, if chunk is not generated
            self.create_chunk((chunk_x, chunk_y))
        self.chunks[(chunk_x, chunk_y)][mod_x, mod_y] = data
    
    def get_block(self, x: int, y: int, generate: bool=True, default: int=0):
        chunk_x, mod_x = divmod(x, CHUNK_SIZE)
        chunk_y, mod_y = divmod(y, CHUNK_SIZE)
        if not (chunk_x, chunk_y) in self.chunks:
            if generate:
                self.create_chunk((chunk_x, chunk_y))
            else:
                return default
        return self.chunks[(chunk_x, chunk_y)][mod_x , mod_y]

    def generate_chunk(self, chunk_coord: [int]):
        for dx, dy in numpy.ndindex((CHUNK_SIZE, CHUNK_SIZE)):
            x, y = dx + chunk_coord[0] * CHUNK_SIZE, dy + chunk_coord[1] * CHUNK_SIZE
            self.chunks[chunk_coord][dx, dy] = self.generate_block(x, y)
    
    def generate_block(self, x: int, y: int):
        z = noise.snoise2(x / 30 + self.SEED + 0.1, y / 30 + self.SEED + 0.1)
        block = z > 0.1
        if z > 0 and noise.snoise2(x / 30 + self.SEED + 0.1, (y + 1) / 30 + self.SEED + 0.1) > 0.1:
            block = 2
        return block

    def draw(self, window):
        start, end = window.camera.visible_blocks()
        for x in range(start[0], end[0]):
            for y in range(start[1], end[1]):
                if self[x, y] == 1:
                    rect = window.camera.map_coord((x, y, 1, 1), from_world=True)
                    window.draw_image("grass", rect[:2], rect[2:])
                elif self[x, y] == 2:
                    rect = window.camera.map_coord((x, y, 1, 1), from_world=True)
                    window.draw_image("dirt", rect[:2], rect[2:])
                if not (x % CHUNK_SIZE and y % CHUNK_SIZE):
                    rect = window.camera.map_coord((x, y, .4, .4), from_world=True)
                    window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 50))
