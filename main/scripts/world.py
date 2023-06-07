import numpy

class World:
    def __init__(self):
        self.chunks = {}      # indexed by tuple (x, y) -> numpy.array(shape=(32, 32))
        self.chunk_size = 32  # 32x32

        # Chunk template, which can be copied later
        self.empty_chunk = numpy.zeros((32, 32), dtype=int)

    def create_chunk(self, coord):
        self.chunks[coord] = self.empty_chunk.copy()

    def set_block(self, x, y, data):
        chunk_x, mod_x = divmod(x, self.chunk_size)
        chunk_y, mod_y = divmod(y, self.chunk_size)

        if not (chunk_x, chunk_y) in self.chunks:
            self.create_chunk((chunk_x, chunk_y))

        self.chunks[(chunk_x, chunk_y)][mod_x , mod_y] = data
    
    def get_block(self, x, y, default=0):
        chunk_x, mod_x = divmod(x, self.chunk_size)
        chunk_y, mod_y = divmod(y, self.chunk_size)

        if not (chunk_x, chunk_y) in self.chunks:
            return default
        return self.chunks[(chunk_x, chunk_y)][mod_x , mod_y]
