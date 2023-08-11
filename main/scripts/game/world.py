# -*- coding: utf-8 -*-
from scripts.utility.util import realistic
from noise import *
import scripts.game.worldnoise as noise
import random
import numpy
import math


WATER_PER_BLOCK = 1000 # How much water can be in one block.
WATER_SPEED = 1000 # How much water a block can emit each second


class World(dict):
    def __init__(self, block_data: dict):
        super().__init__() # {(x, y): (block, plant, background, water_level)}

        self.seed: float = noise.seed()
        self.seed = 18125.25
        self.view: numpy.array = None
        self.view_size: tuple = (0, 0)
        self.block_data: dict = {name: (index, hardness, family, {"foreground": 0, "plant": 1, "background": 2, "water": 3}[layer]) for name, (index, hardness, family, layer) in block_data.items()} # {"block_name": (id, hardness, group, layer)}
        self.block_index: dict = {index: name for name, (index, *_) in block_data.items()}
        self.block_index[0] = "air"
        self.block_name: dict = {name: index for name, (index, *_) in block_data.items()}
        self.entities: set = set()
        self.particles: set = set()
        self.wind: float = 0.0 # wind direction
        self.loaded_blocks: tuple = ((0, 0), (0, 0))

        self.generate()

    def add_entity(self, entity):
        self.entities.add(entity)
    
    def add_particle(self, particle):
        self.particles.add(particle)

    def set_block(self, x: int, y: int, data: int, layer=0):
        if not (x, y) in self:
            self[(x, y)] = [0, 0, 0, 0]
        if data:
            layer = self.block_data[self.block_index[data]][3]
        self[(x, y)][layer] = data
    
    def get_block(self, x: int, y: int, layer: int=0):
        if not (x, y) in self:
            self.generate_block(x, y)
        return self[(x, y)][layer]

    def set_water(self, x, y, level):
        if not (x, y) in self:
            self.generate_block(x, y)
        self[(x, y)][3] = level

    def get_water(self, x, y):
        return self.get((x, y), (0, 0, 0, 0))[3]

    def update(self, window):
        self.loaded_blocks = window.camera.visible_blocks()
        self.create_view(window)
        window.world_view = self.view

        self.wind = math.sin(window.time) * 20 + math.cos(window.time * 5) * 10
        
        for entity in self.entities:
            entity.update(self, window)
        for particle in self.particles:
            particle.update(self, window)

    def update_block(self, window, x, y):
        water_level = self.get_water(x, y)
        if not water_level:
            return

        directions = (
            ((0, -1), (1, 0), (-1, 0), (0, 1)),
            ((0, -1), (-1, 0), (1, 0), (0, 1))
        )[random.randint(0, 1)]

        for dx, dy in directions:
            if dy == 1 and water_level <= WATER_PER_BLOCK:
                return
            if self.get_block(x + dx, y + dy):
                continue

            water_level_target = self.get_water(x + dx, y + dy)
            absorbable_water = max(0, WATER_PER_BLOCK - water_level_target)
            if not (water_level and absorbable_water):
                return

            emmitable_water = min(water_level, WATER_SPEED * window.delta_time)
            if emmitable_water > absorbable_water and 0:
                water_level_target = WATER_PER_BLOCK
                water_level -= absorbable_water
            else:
                water_level_target += emmitable_water
                water_level -= emmitable_water

            self.set_water(x + dx, y + dy, round(water_level_target))
            self.set_water(x, y, round(water_level))
  
        """
        if water_level and self.get_block(x, y - 1) == 0:
            water_level_below = self.get_water(x, y - 1)
            if water_level_below < 1000:
                space_left = 1000 - water_level_below
                if water_level > space_left:
                    water_level = water_level - space_left
                    water_level_below = 1000
                else:
                    water_level_below += water_level
                    water_level = 0
                    
                self.set_water(x, y, water_level)
                self.set_water(x, y - 1, water_level_below)
        """

    def create_view(self, window):
        start, end = self.loaded_blocks
        view_size = (end[0] - start[0], end[1] - start[1])

        if self.view_size != view_size:
            self.view = numpy.zeros((*view_size, 4))
            self.view_size = view_size

        for offset in ((0, 0), (0, 1), (1, 0), (1, 1)): # loop over offsets --> (3|1) & (3|2) & (3|3) not updated in order
            for x in range(offset[0], view_size[0] - 1, 2):
                for y in range(offset[1], view_size[1] - 1, 2):
                    self.update_block(window, start[0] + x, start[1] + y) # update block
                    if not (start[0] + x, start[1] + y) in self:
                        self.generate_block(start[0] + x, start[1] + y)
                    self.view[x, y] = self[start[0] + x, start[1] + y]

    def generate(self): # work in progress
        points = []
        position = [0, 0]
        angle = 0
        length = 10000
        for i in range(length):
            position = [position[0] + math.cos(angle), position[1] + math.sin(angle)]
            points.append(position)
            angle += snoise2(i * 20.215 + 0.0142, 1, octaves=3) / 2 # use simplex; perlin repeats

        for point in points:
            radius = int((pnoise1(sum(point) / 2 + 100, octaves=3) + 2) * 3)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx ** 2 + dy ** 2 <= radius ** 2:
                        coord = (int(point[0] + dx), int(point[1] + dy))
                        self.set_block(*coord, 0)

    def generate_block(self, x, y):
        z = noise.terrain(x, y, self.seed)
        if z < 0.5:
            self.set_block(x, y, self.block_name["dirt"])
        else:
            self.set_block(x, y, self.block_name["stone"])


        """
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
        """