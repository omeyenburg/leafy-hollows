# -*- coding: utf-8 -*-
from scripts.utility.util import realistic
from noise import *
import scripts.utility.geometry as geometry
import scripts.game.worldnoise as noise
import random
import numpy
import math


WATER_PER_BLOCK = 1000
WATER_SPEED = 0.1 # Water update delay


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
        self.water_update_timer: float = 0.0

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
        return abs(self.get((x, y), (0, 0, 0, 0))[3])

    def get_water_side(self, x, y):
        return -1 if self.get((x, y), (0, 0, 0, 0))[3] < 0 else 1

    def update(self, window):
        self.loaded_blocks = window.camera.visible_blocks()
        self.create_view(window)

        self.wind = math.sin(window.time) * 20 + math.cos(window.time * 5) * 10

        self.water_update_timer += window.delta_time
        if self.water_update_timer > WATER_SPEED:
            self.water_update_timer = 0.0
            for y in geometry.shuffled_range(self.view_size[1] - 1):
                for x in geometry.shuffled_range(self.view_size[0] - 1):
                    self.update_block(window, self.loaded_blocks[0][0] + x, self.loaded_blocks[0][1] + y)
        
        for entity in self.entities:
            entity.update(self, window)
        for particle in self.particles:
            particle.update(self, window)

    def update_block(self, window, x, y):
        water_level = self.get_water(x, y)
        if not water_level:
            return

        emmitable_water = min(water_level / 2, WATER_PER_BLOCK / 2)
        overflow_water = max(0, water_level - WATER_PER_BLOCK) / 4
        water_side = self.get_water_side(x, y)

        if self.get_water(x, y + 1):
            water_side = self.get_water_side(x, y + 1)

        # Block below
        if not self.get_block(x, y - 1):
            water_level_below = self.get_water(x, y - 1)
            absorbable_water = max(0, WATER_PER_BLOCK - water_level_below + overflow_water)

            absorbed_water = min(absorbable_water, emmitable_water)
            water_level -= absorbed_water
            emmitable_water -= absorbed_water
            water_level_below += absorbed_water

            self.set_water(x, y - 1, water_level_below * water_side)

        if not emmitable_water:
            self.set_water(x, y, water_level * water_side)
            return

        # Blocks on both sides
        blocks = {(x, y): water_level}
        total_water = water_level
        for _x, _y in ((x - 1, y), (x + 1, y)):
            if not (self.get_block(_x, _y) or self.get_block(_x, _y - 1) and self.get_water(_x, _y - 1) > 1):
                water_level_target = self.get_water(_x, _y)
                total_water += water_level_target
                blocks[(_x, _y)] = water_level_target
        max_water = len(blocks) * WATER_PER_BLOCK
        if total_water > max_water:
            emmitable_water = total_water - max_water
            total_water = max_water
        else:
            emmitable_water = 0
        for (_x, _y), old_water_level_target in blocks.items():
            water_level_target = total_water / len(blocks)
            water_side = self.get_water_side(_x, _y)
            
            if water_level_target > old_water_level_target:
                if _x < x:
                    water_side = 1
                elif _x > x:
                    water_side = -1
                else:
                    if blocks.get((x + 1, y), 1) < blocks.get((x - 1, y), 0):
                        water_side = 1
                    else:
                        water_side = -1

            if self.get_water(_x, _y + 1):
                water_side = self.get_water_side(_x, _y)

            self.set_water(_x, _y, water_level_target * water_side)

        # Block above
        water_side = self.get_water_side(x, y + 1)
        water_level_target_above = self.get_water(x, y + 1)
        self.set_water(x, y + 1, (water_level_target_above + emmitable_water) * water_side)

    def create_view(self, window):
        start, end = self.loaded_blocks
        view_size = (end[0] - start[0], end[1] - start[1])

        if self.view_size != view_size:
            self.view = numpy.zeros((*view_size, 4))
            self.view_size = view_size
  
        for y in range(view_size[1] - 1):
            for x in range(view_size[0] - 1):
                if not (start[0] + x, start[1] + y) in self:
                    self.generate_block(start[0] + x, start[1] + y)
                self.view[x, y] = self[start[0] + x, start[1] + y]
        
        window.world_view = self.view

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
                        #self.set_water(*coord, 1000)

    def generate_block(self, x, y):
        z = noise.terrain(x, y, self.seed)
        if z < 0.5:
            self.set_block(x, y, self.block_name["grass"])
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
