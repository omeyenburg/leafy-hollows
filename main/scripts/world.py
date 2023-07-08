# -*- coding: utf-8 -*-
from threading import Thread
import random
import numpy
import noise
import math


CHUNK_SIZE = 16


class Chunk:
    template: numpy.array = numpy.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=int) # Chunk template, which can be copied later

    def __init__(self, x: int, y: int, seed: float):
        self.x = x
        self.y = y
        self.array = Chunk.template.copy()
        self.generate(seed)

    def __getitem__(self, index):
        return self.array[index]

    def __setitem__(self, index, value):
        self.array[index] = value

    def generate(self, seed: float):
        for dx, dy in numpy.ndindex((CHUNK_SIZE, CHUNK_SIZE)):
            x, y = dx + self.x * CHUNK_SIZE, dy + self.y * CHUNK_SIZE
            self.array[dx, dy] = self.generate_block(x, y, seed)

    def generate_block(self, x: int, y: int, seed: float):
        z = noise.snoise2(x / 30 + seed + 0.1, y / 30 + seed + 0.1)
        block = int(z > 0.1) * 2
        if z > 0 and noise.snoise2(x / 30 + seed + 0.1, (y + 1) / 30 + seed + 0.1) > 0.1:
            block = 1
        return block


class World:
    def __init__(self):
        self.SEED: float = random.randint(-99999, 99999) + random.random()
        self.chunks: dict = {} # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))
        self.view_cache = None
        self.view_cache_size = (0, 0)

    def __getitem__(self, coord: [int]):
        return self.get_block(coord[0], coord[1])

    def __setitem__(self, coord: [int], data: int):
        self.set_block(coord[0], coord[1], data)

    def create_chunk(self, chunk_coord: [int]):
        self.chunks[chunk_coord] = Chunk(*chunk_coord, self.SEED)

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

    def draw(self, window):
        start, end = window.camera.visible_blocks()
        for x in range(start[0], end[0]):
            for y in range(start[1], end[1]):
                if self[x, y] == 1:
                    rect = window.camera.map_coord((x, y, 1, 1), from_world=True)
                    #window.draw_image("dirt", rect[:2], rect[2:])
                elif self[x, y] == 2:
                    rect = window.camera.map_coord((x, y, 1, 1), from_world=True)
                    window.draw_image("grass", rect[:2], rect[2:])
                if not (x % CHUNK_SIZE and y % CHUNK_SIZE):
                    rect = window.camera.map_coord((x, y, .4, .4), from_world=True)
                    window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 50))

    def view(self, start, end):
        chunks_size = (math.ceil((end[0] - start[0]) / CHUNK_SIZE) + 1, 
                       math.ceil((end[1] - start[1]) / CHUNK_SIZE) + 1)
        chunk_start = (math.floor(start[0] / CHUNK_SIZE),
                       math.floor(start[1] / CHUNK_SIZE))
        if self.view_cache_size == chunks_size:
            chunk_view = self.view_cache
        else:
            chunk_view = numpy.zeros((chunks_size[0] * CHUNK_SIZE, chunks_size[1] * CHUNK_SIZE))
            self.view_cache = chunk_view
            self.view_cache_size = chunks_size


        for d_chunk_x in range(chunks_size[0]):
            for d_chunk_y in range(chunks_size[1]):
                chunk_x = d_chunk_x + chunk_start[0]
                chunk_y = d_chunk_y + chunk_start[1]
                if not (chunk_x, chunk_y) in self.chunks:
                    self.create_chunk((chunk_x, chunk_y))
                chunk_view[d_chunk_x * CHUNK_SIZE:(d_chunk_x + 1) * CHUNK_SIZE, d_chunk_y * CHUNK_SIZE:(d_chunk_y + 1) * CHUNK_SIZE] = self.chunks[(chunk_x, chunk_y)].array

        return chunk_view


