# -*- coding: utf-8 -*-
from scripts.game.world_generation import generate_world, generate_block
from scripts.game.physics import PhysicsObject
from scripts.graphics import particle
from scripts.utility import geometry
from scripts.utility.const import *
from scripts.graphics import sound
from scripts.utility import file
from scripts.game import player
import time


class World:
    def __init__(self, block_data, block_generation_properties, block_group_size, block_properties):
        self.view: numpy.array = None # Sent to shader to render
        self.view_size: tuple = (0, 0)
        self.chunks = {} # {(chunk_x, chunk_y): numpy_array(16x16x4)} -> (block, plant, background, water_level)
        self.camera_stop: int = 0 # maximum camera x
        self.item_count: int = 0
        os.environ["item_count"] = "0"

        self.delta_time = 0

        self.block_generation_properties = block_generation_properties
        self.block_properties = block_properties
        self.block_family: dict = {
            (name + "_flipped" if flipped else name):
            family
            for name, (index, family, layer) in block_data.items()
            for flipped in range(2)
        }
        self.block_layer: dict = {
            (name + "_flipped" if flipped else name):
            {"foreground": 0, "plant": 1, "background": 2, "water": 3}[layer]
            for name, (index, family, layer) in block_data.items()
            for flipped in range(2)
        }
        self.block_name: dict = {
            (name + "_flipped" if flipped else name):
            index + flipped
            for name, (index, family, layer) in block_data.items()
            for flipped in range(2)
        }
        self.block_index: dict = {
            index + flipped:
            (name + "_flipped" if flipped else name)
            for name, (index, family, layer) in block_data.items()
            for flipped in range(2)
        }
        self.block_family["air"] = "air"
        self.block_index[0] = "air"
        self.block_group_size = block_group_size
        self.blocks_climbable: set = {self.block_name[name] for name in BLOCKS_CLIMBABLE}

        self.entities: set = set()
        self.loaded_entities: set = set()
        self.wind: float = 0.0 # Wind direction
        self.loaded_blocks: tuple = ((0, 0), (0, 0)) # (start, end)
        self.water_update_timer: float = 0.0

        if PHYSICS_REALISTIC:
            self.player: player.Player = player.Player(spawn_pos=[0, 0])
        else:
            self.player: player.Player = player.Player(spawn_pos=[0, 0])
        self.add_entity(self.player)

    def iterate(self):
        for chunk_x, chunk_y in self.chunks:
            for delta_x, delta_y in numpy.ndindex((WORLD_CHUNK_SIZE, WORLD_CHUNK_SIZE)):
                yield chunk_x * WORLD_CHUNK_SIZE + delta_x, chunk_y * WORLD_CHUNK_SIZE + delta_y

    def get_block_friction(self, block_type: int):
        properties = self.block_properties.get(block_type, 0)
        if properties:
            return properties["friction"]
        return 0.1

    def add_entity(self, entity):
        self.entities.add(entity)

    def create_chunk(self, x: int, y: int):
        self.chunks[(x, y)] = numpy.zeros((32, 32, 4))
        self.chunks[(x, y)][:, :, 0] = self.block_name["dirt_block"]

    def get_block_exists(self, x: int, y: int):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER
        return (chunk_x, chunk_y) in self.chunks

    def get_chunk_exists(self, chunk_x: int, chunk_y: int):
        return (chunk_x, chunk_y) in self.chunks

    def set_block(self, x: int, y: int, data: int, layer=0):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER
        mod_x = x & (WORLD_CHUNK_SIZE - 1)
        mod_y = y & (WORLD_CHUNK_SIZE - 1)

        if not (chunk_x, chunk_y) in self.chunks:
            self.create_chunk(chunk_x, chunk_y)
        if isinstance(data, (int, float)) and data:
            layer = self.block_layer[self.block_index[data]]
        self.chunks[(chunk_x, chunk_y)][mod_x, mod_y, layer] = data
    
    def get_block(self, x: int, y: int, layer: int=0, generate: bool=False, default: int=(0, 0, 0, 0)):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER
        mod_x = x & (WORLD_CHUNK_SIZE - 1)
        mod_y = y & (WORLD_CHUNK_SIZE - 1)

        if not (chunk_x, chunk_y) in self.chunks:
            if generate:
                self.create_chunk(chunk_x, chunk_y)
            else:
                if isinstance(default, (tuple, list)):
                    return default[layer]
                return default
        return self.chunks[(chunk_x, chunk_y)][mod_x, mod_y, layer]

    def set_water(self, x, y, level):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER
        mod_x = x & (WORLD_CHUNK_SIZE - 1)
        mod_y = y & (WORLD_CHUNK_SIZE - 1)

        if not (chunk_x, chunk_y) in self.chunks:
            self.create_chunk(chunk_x, chunk_y)
        self.chunks[(chunk_x, chunk_y)][mod_x, mod_y, 3] = int(level)

    def get_water(self, x, y):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER

        if not (chunk_x, chunk_y) in self.chunks:
            return 0

        mod_x = x & (WORLD_CHUNK_SIZE - 1)
        mod_y = y & (WORLD_CHUNK_SIZE - 1)
        return abs(self.chunks[(chunk_x, chunk_y)][mod_x, mod_y, 3])

    def get_water_side(self, x, y):
        chunk_x = x >> WORLD_CHUNK_SIZE_POWER
        chunk_y = y >> WORLD_CHUNK_SIZE_POWER

        if not (chunk_x, chunk_y) in self.chunks:
            return 1

        mod_x = x & (WORLD_CHUNK_SIZE - 1)
        mod_y = y & (WORLD_CHUNK_SIZE - 1)

        return copysign(1, abs(self.chunks[(chunk_x, chunk_y)][mod_x, mod_y, 3]))

    def update_physics(self, window):
        for entity in self.loaded_entities:
            if hasattr(entity, "health") and entity.health <= 0:
                if not entity is self.player:
                    self.player.obtain_weapon_drop(window, entity)
                self.entities.discard(entity)
            entity.update(self, window)

        if window.options["particles"]:
            particle.update(window)

    def update(self, window):
        self.delta_time += window.delta_time
        if self.delta_time < WORLD_UPDATE_INTERVAL:
            return
        delta_time = self.delta_time
        self.delta_time = 0

        # Filter entites
        (start_x, start_y), (end_x, end_y) = self.loaded_blocks
        self.loaded_entities.clear()
        self.loaded_entities.add(self.player)
        for entity in self.entities.copy():
            if start_x < entity.rect.x < end_x and start_y < entity.rect.y < end_y:
                self.loaded_entities.add(entity)
            elif entity.destroy_unloaded:
                self.entities.discard(entity)
        
        # Update wind
        self.wind = sin(window.time) * WORLD_WIND_STRENGTH + cos(window.time * 5) * WORLD_WIND_STRENGTH / 2
        window.particle_wind = self.wind / 50

        # Play ambient sounds
        if not random.randint(0, int(10 / delta_time)):
            sound.play(window, "water_drop", x=random.random() * 2 - 1)
        elif not random.randint(0, int(60 / delta_time)):
            sound.play(window, "cave_ambient", x=random.random() * 2 - 1)

        # Update water
        for y in geometry.shuffled_range(self.view_size[1] - 1):
            for x in geometry.shuffled_range(self.view_size[0] - 1):
                self.update_block(window, self.loaded_blocks[0][0] + x, self.loaded_blocks[0][1] + y)

        # Update particles
        if window.options["particles"]:
            # Spawn ambient particles
            if particle.spawn_possible(window, "big_leaf_particle"):
                x = random.randint(self.loaded_blocks[0][0], self.loaded_blocks[1][0])
                particle.spawn(window, "big_leaf_particle", x, self.loaded_blocks[1][1])

            if particle.spawn_possible(window, "small_leaf_particle"):
                x = random.randint(self.loaded_blocks[0][0], self.loaded_blocks[1][0])
                particle.spawn(window, "small_leaf_particle", x, self.loaded_blocks[1][1])

    def draw(self, window):
        self.loaded_blocks = window.camera.visible_blocks()
        self.create_view(window)

        for entity in self.loaded_entities:
            entity.draw(window)

    def update_block(self, window, x, y):
        block_array = self.get_block(x, y, layer=slice(None), generate=True)

        # Update water
        self.update_block_water(window, x, y)

        # Update torches
        if self.block_index[block_array[1]] in ("torch", "torch_flipped"):
            particle.spawn(window, "fire_particle", x + 0.5, y + 0.7)
            if block_array[3] > 600:
                self.set_block(x, y, self.block_name["unlit_torch"])

    def update_block_water(self, window, x, y):
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
            self.view = numpy.empty((*view_size, 4))
            self.view_size = view_size

        start_chunk_x = start[0] >> WORLD_CHUNK_SIZE_POWER
        start_chunk_y = start[1] >> WORLD_CHUNK_SIZE_POWER
        start_mod_x = start[0] & (WORLD_CHUNK_SIZE - 1)
        start_mod_y = start[1] & (WORLD_CHUNK_SIZE - 1)
        chunk_num_x = ceil((start_mod_x + view_size[0]) / WORLD_CHUNK_SIZE)
        chunk_num_y = ceil((start_mod_y + view_size[1]) / WORLD_CHUNK_SIZE)
        uncut_view = numpy.empty((chunk_num_x * WORLD_CHUNK_SIZE, chunk_num_y * WORLD_CHUNK_SIZE, 4))

        #print("view_size", view_size)
        #print("start", start)
        #print("end", end)
        #print("start_chunk", start_chunk_x, start_chunk_y)
        #print("start_mod", start_mod_x, start_mod_y)
        #print("chunk_num", chunk_num_x, chunk_num_y)

        for chunk_delta_x, chunk_delta_y in numpy.ndindex((chunk_num_x, chunk_num_y)):
            chunk_x = start_chunk_x + chunk_delta_x
            chunk_y = start_chunk_y + chunk_delta_y

            if not (chunk_x, chunk_y) in self.chunks:
                self.chunks[(chunk_x, chunk_y)] = numpy.zeros((WORLD_CHUNK_SIZE, WORLD_CHUNK_SIZE, 4))
                self.chunks[(chunk_x, chunk_y)][:, :, 0] = self.block_name["dirt_block"]
                #print(chunk_x, chunk_y)

            uncut_view[chunk_delta_x * WORLD_CHUNK_SIZE:(chunk_delta_x + 1) * WORLD_CHUNK_SIZE, chunk_delta_y * WORLD_CHUNK_SIZE:(chunk_delta_y + 1) * WORLD_CHUNK_SIZE] = self.chunks[(chunk_x, chunk_y)]

        window.world_view = self.view = uncut_view[start_mod_x:start_mod_x + view_size[0], start_mod_y:start_mod_y + view_size[1]]

            #print("chunk", "[rel]", chunk_delta_x, chunk_delta_y, "[abs]", chunk_x, chunk_y)
            
            #copy_start_x = max(start[0], chunk_x * WORLD_CHUNK_SIZE) & (WORLD_CHUNK_SIZE - 1)
            #copy_start_y = max(start[1], chunk_y * WORLD_CHUNK_SIZE) & (WORLD_CHUNK_SIZE - 1)
            #copy_end_x = min(end[0], (chunk_x + 1) * WORLD_CHUNK_SIZE - 1) & (WORLD_CHUNK_SIZE - 1)
            #copy_end_y = min(end[1], (chunk_y + 1) * WORLD_CHUNK_SIZE - 1) & (WORLD_CHUNK_SIZE - 1)
            #print("copy start", copy_start_x, copy_start_y)
            #print("copy end", copy_end_x, copy_end_y)
            #print("copy size", copy_end_x - copy_start_x, copy_end_y - copy_start_y)

            #dest_start_x = max(0, WORLD_CHUNK_SIZE * (chunk_x) - start_mod_x)
            #dest_start_y = max(0, WORLD_CHUNK_SIZE * (chunk_y) - start_mod_y)
            #dest_end_x = copy_end_x - copy_start_x + dest_start_x#min(view_size[0], start_mod_x + WORLD_CHUNK_SIZE * (chunk_x - 1))
            #dest_end_y = copy_end_y - copy_start_y + dest_start_y#min(view_size[1], start_mod_y + WORLD_CHUNK_SIZE * (chunk_y - 1))
            #print("dest start", dest_start_x, dest_start_y)
            #print("dest end", dest_end_x, dest_end_y)
            #print("dest size", dest_end_x - dest_start_x, dest_end_y - dest_start_y)

            #data = self.chunks[(chunk_x, chunk_y)][copy_start_x:copy_end_x, copy_start_y:copy_end_y]
            #self.view[dest_start_x:dest_end_x, dest_start_y:dest_end_y] = data  

    def save(self, window):
        window.loading_progress[:3] = "Saving inventory", 0, 2
        if not window.options["save world"]:
            return        

        self.item_count = int(os.environ.get("item_count"))
        self.player.inventory.save(self)
        window.loading_progress[:2] = "Saving world", 1
        file.save("data/user/world.data", self, file_format="pickle")
        window.loading_progress[1] = 2
        time.sleep(0.1)

    @staticmethod
    def load(window, block_data):
        window.loading_progress[:3] = "Loading world file", 1, 2
        world = file.load("data/user/world.data", default=0, file_format="pickle")

        try:
            if isinstance(world, World):
                window.loading_progress[:3] = "Loading world", 2, 2
                os.environ["item_count"] = str(world.item_count)
                return world
        except Exception as e:
            print(e)
            pass

        world = World(*block_data)
        generated = False
        while not generated:
            generated = generate_world(world, window)

        return world
