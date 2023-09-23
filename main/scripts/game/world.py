# -*- coding: utf-8 -*-
from scripts.game.world_generation import generate_world, generate_block
from scripts.utility.const import *
from scripts.graphics import particle
from scripts.utility import geometry
from scripts.game import player
from scripts.utility import file
import random
import numpy
import math


class World(dict):
    def __init__(self, window):
        super().__init__() # {(x, y): (block, plant, background, water_level)}
        self.seed: float = random.randint(-10**6, 10**6) + math.e # Float between -10^6 and 10^6
        self.view: numpy.array = None # Sent to shader to render
        self.view_size: tuple = (0, 0)
        self.block_layer: dict = {name: {"foreground": 0, "plant": 1, "background": 2, "water": 3}[layer] for name, (index, layer) in window.block_data.items()}
        self.block_name: dict = {name: index for name, (index, layer) in window.block_data.items()}
        self.block_index: dict = {index: name for name, (index, layer) in window.block_data.items()}
        self.block_index[0] = "air"
        self.blocks_climbable: set = {self.block_name[name] for name in BLOCKS_CLIMBABLE}
        self.entities: set = set()
        self.particles: list = []
        self.particle_types: dict = {}
        self.wind: float = 0.0 # Wind direction
        self.loaded_blocks: tuple = ((0, 0), (0, 0)) # (start, end)
        self.water_update_timer: float = 0.0

        if PHYSICS_REALISTIC:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, crouch_speed=2, swim_speed=3, acceleration_time=0.2, jump_force=17)
        else:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=5, sprint_speed=7, crouch_speed=3, swim_speed=3, acceleration_time=.1, jump_force=21)
        self.add_entity(self.player)

        # Create particle types
        particle.setup(window, self, "spark", time=2, delay=1, size=(0.2, 0.2), gravity=-0.7, growth=-1, speed=0, direction=0, divergence=2)
        particle.setup(window, self, "big_leaf", time=10, delay=3, size=(0.2, 0.2), gravity=0.5, growth=-1, speed=0.5, direction=3/2*math.pi, divergence=2)
        particle.setup(window, self, "small_leaf", time=10, delay=3, size=(0.15, 0.15), gravity=0.5, growth=-1, speed=0.5, direction=3/2*math.pi, divergence=2)

    def add_entity(self, entity):
        self.entities.add(entity)
    
    def add_particle(self, particle):
        self.particles.add(particle)

    def set_block(self, x: int, y: int, data: int, layer=0):
        if not (x, y) in self:
            self[(x, y)] = [0, 0, 0, 0]
        if data:
            layer = self.block_layer[self.block_index[data]]
        self[(x, y)][layer] = data
    
    def get_block(self, x: int, y: int, layer: int=0, generate=True, default=0):
        if not (x, y) in self:
            if generate:
                generate_block(self, x, y)
            else:
                return default
        return self[(x, y)][layer]

    def set_water(self, x, y, level):
        if not (x, y) in self:
            generate_block(self, x, y)
        self[(x, y)][3] = int(level)

    def get_water(self, x, y):
        return abs(self.get((x, y), (0, 0, 0, 0))[3])

    def get_water_side(self, x, y):
        return -1 if self.get((x, y), (0, 0, 0, 0))[3] < 0 else 1

    def update(self, window):
        self.wind = math.sin(window.time) * WORLD_WIND_STRENGTH + math.cos(window.time * 5) * WORLD_WIND_STRENGTH / 2

        self.water_update_timer += window.delta_time
        if self.water_update_timer > WORLD_WATER_SPEED:
            self.water_update_timer = 0.0
            for y in geometry.shuffled_range(self.view_size[1] - 1):
                for x in geometry.shuffled_range(self.view_size[0] - 1):
                    self.update_block(window, self.loaded_blocks[0][0] + x, self.loaded_blocks[0][1] + y)
        
        for entity in self.entities:
            entity.update(self, window)
        if window.options["particles"]:
            particle.update(window, self)

    def draw(self, window):
        self.loaded_blocks = window.camera.visible_blocks()
        self.create_view(window)

        for entity in self.entities:
            entity.draw(window)

    def update_block(self, window, x, y):
        water_level = self.get_water(x, y)
        if not water_level:
            return

        emmitable_water = min(water_level / 2, WORLD_WATER_PER_BLOCK / 2)
        overflow_water = max(0, water_level - WORLD_WATER_PER_BLOCK) / 4
        water_side = self.get_water_side(x, y)

        if self.get_water(x, y + 1):
            water_side = self.get_water_side(x, y + 1)

        # Block below
        if not self.get_block(x, y - 1):
            water_level_below = self.get_water(x, y - 1)
            absorbable_water = max(0, WORLD_WATER_PER_BLOCK - water_level_below + overflow_water)

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
        max_water = len(blocks) * WORLD_WATER_PER_BLOCK
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
                    generate_block(self, start[0] + x, start[1] + y)
                block = self[start[0] + x, start[1] + y]
                self.view[x, y] = block

                if self.block_index[block[1]] in ("torch", "torch_flipped"):
                    particle.spawn(window, self, "spark", start[0] + x, start[1] + y)
                    if self.view[x, y, 3] > 600:
                        self[(start[0] + x, start[1] + y)][1] = self.block_name["unlit_torch"]
        
        window.world_view = self.view

    def save(self):
        file.write("data/user/world.data", self, file_format="pickle")

    @staticmethod
    def load(window):
        window.loading_progress[:3] = "Loading world file", 1, 2
        world = file.read("data/user/world.data", default=0, file_format="pickle")
        if isinstance(world, World) and len(window.block_data) == len(world.block_name):
            window.loading_progress[:3] = "Loading world", 2, 2
            for name in world.particle_types:
                world.particle_types[name][0][0] = window.time
            world.particles = []
            return world
        
        world = World(window)
        generate_world(world, window)
        return world
