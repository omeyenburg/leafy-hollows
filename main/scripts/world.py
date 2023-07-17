# -*- coding: utf-8 -*-
from scripts.util import realistic
from noise import *
import scripts.worldnoise as noise
from threading import Thread
import random
import numpy
import math


CHUNK_SIZE = 16


class Chunk:
    template: numpy.array = numpy.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=int) # Chunk template, which can be copied later

    def __init__(self, x: int, y: int, seed: float, blocks: dict):
        self.x = x
        self.y = y
        self.array = Chunk.template.copy()
        self.generate(seed, blocks)

    def __getitem__(self, index):
        return self.array[index]

    def __setitem__(self, index, value):
        self.array[index] = value

    def generate(self, seed: float, blocks: dict):
        for dx, dy in numpy.ndindex((CHUNK_SIZE, CHUNK_SIZE)):
            x, y = dx + self.x * CHUNK_SIZE, dy + self.y * CHUNK_SIZE
            self.array[dx, dy] = self.generate_block(x, y, seed, blocks)

    def generate_block(self, x: int, y: int, seed: float, blocks: dict):
        world_gen = 1

        if world_gen == 1:
            z = noise.terrain(x, y, seed)
            z_top1 = noise.terrain(x, y + 1, seed)
            z_top2 = noise.terrain(x, y + 2, seed)
            z_bottom1 = noise.terrain(x, y - 1, seed)
            if z > 0 and z_top1 <= 0:
                block = blocks["grass"]
            elif z <= 0 and z_bottom1 > 0:
                block = blocks["grass_idle"]
            #elif z > 0 and z_top2 <= 0:
            #    block = blocks["dirt"]
            elif z > 0:
                block = blocks["dirt"]
            else:
                block = 0 # air
            #if 0 >= z > -0.3:
            #    block += 1000 * blocks["stone"]
        elif world_gen == 2:
            z = abs(noise.terrain(x, y, seed))
            z_top1 = abs(noise.terrain(x, y + 1, seed))
            z_top2 = abs(noise.terrain(x, y + 2, seed))
            z_bottom1 = abs(noise.terrain(x, y - 1, seed))

            threshold = 0.25

            if z > threshold and z_top1 <= threshold:
                block = blocks["grass"]
            elif z <= threshold and z_bottom1 > threshold:
                block = blocks["grass_idle"]
            elif z > threshold and z_top2 <= threshold:
                block = blocks["dirt"]
            elif z > threshold:
                block = blocks["stone"]
            else:
                block = 0 # air
            
            if threshold > z > threshold * 0.7:
                block += 1000 * blocks["stone"]
        elif world_gen == 3:
            h = pnoise2(x / 100 - seed, y / 10, octaves=4) * 3 + 4
            d = pnoise1(x / 100 + seed * 3, octaves=4) * 5 + 145
            z = pnoise1(x / d + seed, octaves=4) * 60
            z2 = abs(noise.terrain(x, y, seed))
            dist = abs(z - y)
            if dist < h:
                block = 0
            else:
                block = blocks["stone"]
        
            
        return block

        # Generate drip stone: 1dnoise(x) -> change treshold
        # Generate spaced points: spaced_noise + check for free space
        # noise.snoise2(x, y, octaves=1, persistence=0.5, lacunarity=2.0, repeatx=None, repeaty=None, base=0.0)


class World:
    def __init__(self, blocks: dict):
        self.seed: float = noise.seed()
        self.seed = 18125.25
        self.chunks: dict = {} # indexed with a tuple (x, y) -> numpy.array(shape=(32, 32))
        self.view: numpy.array = None
        self.view_size: tuple = (0, 0)
        self.blocks: dict = blocks # {"block_name": id}
        self.entities: list = [] # inefficent, but easy to handle
        self.particles: list = []
        self.wind: float = 0.0 # wind direction
        self.loaded_chunks: tuple = (0, 0, 0, 0)
        self.transparent_blocks = [blocks["grass_idle"]]

    def __getitem__(self, coord: [int]):
        return self.get_block(coord[0], coord[1])

    def __setitem__(self, coord: [int], data: int):
        self.set_block(coord[0], coord[1], data)

    def create_chunk(self, chunk_coord: [int]):
        self.chunks[chunk_coord] = Chunk(*chunk_coord, self.seed, self.blocks)

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

    def get_collision_block(self, x: int, y: int):
        block = self[x, y]
        return block % 1000 > 0 and not block % 1000 in self.transparent_blocks

    def update(self, window):
        loaded_blocks = window.camera.visible_blocks()
        self.create_view(*loaded_blocks)
        window.world_view = self.view

        self.wind = math.sin(window.time) * 20 + math.cos(window.time * 5) * 10
        
        """
        for dx, dy in numpy.ndindex(self.view.shape):
            block = self.view[dx, dy]
            if block == self.blocks["grass"]:
                x, y = self.loaded_chunks[0] * 16 + dx, self.loaded_chunks[1] * 16 + dy
                for i in range(5):
                    rect = window.camera.map_coord((x + i / 16 * 3, y + 1.5, 3/16, 7/16), from_world=True)
                    if noise.terrain(x * 10 + i * 200, y * 10 + 100, self.seed) < 0:
                        window.draw_image("grass_left", rect[:2], rect[2:], angle=noise.wind(x + i * 10, y, self.wind))
                    else:
                        window.draw_image("grass_right", rect[:2], rect[2:], angle=noise.wind(x + i * 10, y, self.wind))
        """
        

        for entity in self.entities:
            entity.update(self, window)
        for particle in self.particles:
            particle.update(self, window)

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

    def create_view(self, start, end):
        chunks_size = (math.ceil((end[0] - start[0]) / CHUNK_SIZE) + 1, 
                       math.ceil((end[1] - start[1]) / CHUNK_SIZE) + 1)
        chunk_start = (math.floor(start[0] / CHUNK_SIZE),
                       math.floor(start[1] / CHUNK_SIZE))
        self.loaded_chunks = (*chunk_start, *chunks_size)

        if self.view_size == chunks_size:
            chunk_view = self.view
        else:
            chunk_view = numpy.zeros((chunks_size[0] * CHUNK_SIZE, chunks_size[1] * CHUNK_SIZE))
            self.view = chunk_view
            self.view_size = chunks_size

        for d_chunk_x in range(chunks_size[0]):
            for d_chunk_y in range(chunks_size[1]):
                chunk_x = d_chunk_x + chunk_start[0]
                chunk_y = d_chunk_y + chunk_start[1]
                if not (chunk_x, chunk_y) in self.chunks:
                    self.create_chunk((chunk_x, chunk_y))
                chunk_view[d_chunk_x * CHUNK_SIZE:(d_chunk_x + 1) * CHUNK_SIZE, d_chunk_y * CHUNK_SIZE:(d_chunk_y + 1) * CHUNK_SIZE] = self.chunks[(chunk_x, chunk_y)].array

        self.view = chunk_view


