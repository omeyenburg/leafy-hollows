import numpy

class World:
    def __init__(self):
        self.chunks = {}      # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))
        self.chunk_size = 32  # width and height in blocks

        # Chunk template, which can be copied later
        self.empty_chunk = numpy.zeros((self.chunk_size, self.chunk_size), dtype=int)

    def create_chunk(self, coord):
        self.chunks[coord] = self.empty_chunk.copy()

    def set_block(self, x, y, data):
        chunk_x, mod_x = divmod(x, self.chunk_size) # = (x // self.chunk_size, x % self.chunk_size)
        chunk_y, mod_y = divmod(y, self.chunk_size) # = (y // self.chunk_size, y % self.chunk_size)

        if not (chunk_x, chunk_y) in self.chunks: # chunk not generated; create chunk
            self.create_chunk((chunk_x, chunk_y))
        self.chunks[(chunk_x, chunk_y)][mod_x , mod_y] = data
    
    def get_block(self, x, y, default=0): # chunk not generated; return default value
        chunk_x, mod_x = divmod(x, self.chunk_size)
        chunk_y, mod_y = divmod(y, self.chunk_size)

        if not (chunk_x, chunk_y) in self.chunks:
            return default
        return self.chunks[(chunk_x, chunk_y)][mod_x , mod_y]
