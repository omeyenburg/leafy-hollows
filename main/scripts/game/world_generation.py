# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.game import structure
from scripts.game.entity import *
from copy import deepcopy
import random
import numpy
import math


# Import noise / opensimplex
try:
    from noise import *
except ModuleNotFoundError:
    import opensimplex

    def pnoise1(x: float, octaves: int=1, persistence: float=0.5, lacunarity: float=2.0, repeat: float=0):
        z = 0
        octaves = 1

        if repeat:
            x = abs(math.sin(x * math.pi / repeat + 2.928) * repeat)

        for i in range(octaves):
            divisor = 2 ** i
            z += opensimplex.noise2(x / divisor, math.e) / divisor

        return z

    def snoise2(x: float, y: float, octaves: int=1, persistence: float=0.5, lacunarity: float=2.0, repeatx: float=0, repeaty: float=0):
        z = 0
        octaves = 1

        if repeatx:
            x = abs(math.sin(x * math.pi / repeatx + 0.214) * repeatx)
        if repeaty:
            y = abs(math.sin(y * math.pi / repeaty + 1.331) * repeaty)

        for i in range(octaves):
            divisor = 2 ** i
            z += opensimplex.noise2(x / divisor, y / divisor) / divisor

        return z


# Replace with better names...? Add / Remove?
BIOMES = ["overgrown", "mushroom", "dripstone", "frozen", "underwater", "stone", "desert", "hell", "crystal", "dwarf"]
CAVE_SHAPES = ["intro", "horizontal", "vertical", "blob", "structure"]


# Called from World
def generate_world(world, window):
    """
    Main world generation function
    """
    window.loading_progress[2] = 11

    # Load structures
    window.loading_progress[:2] = "Loading structures", 0
    structures = structure.load(world.block_name)

    # Starting point
    branches = set()
    position = [0, 0]
    poles = set() # List of x coords of poles

    # Generate intro
    window.loading_progress[:2] = "Generating intro", 1
    Shape.intro(world, window, position)

    # Line cave segment
    window.loading_progress[:2] = "Generating caves", 5
    last_special = 0
    for i in range(30):
        last_special += 1
        cave_type = random.random()

        if cave_type > 0.6 or last_special < 4:
            Shape.horizontal(world, position)
        else:
            last_special = 0
            cave_type = random.random()

            if cave_type > 0.6:
                if random.randint(0, 1):
                    Shape.vertical(world, position, True)
                    poles.add(int(position[0]))
                    branches.add((*position, 0))
                else:
                    Shape.horizontal(world, position)
                    branches.add((*position, 1))
            elif cave_type > 0.3:
                Shape.vertical(world, position)
                poles.add(int(position[0]))
            else:
                Shape.blob(world, position)

    window.loading_progress[:2] = "Generating cave branches", 7
    for x, y, direction in branches:
        length = random.randint(2, 3)
        position = [x, y]

        if direction:
            Shape.vertical(world, position, True)
            poles.add(int(position[0]))

        for i in range(length):
            Shape.horizontal(world, position)

    # Generate structures between line cave segments
    ...

    # Smoother cave walls
    window.loading_progress[:2] = "Generating foliage", 9
    flatten_edges(world)

    # Find block edges with air
    blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left = find_edge_blocks(world)

    # Generate foliage
    window.loading_progress[1] = 7
    generate_foliage(world, world.block_pools, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)

    # Generate poles
    generate_poles(world, poles, blocks_ground, blocks_ceiling)

    # Spawn enemies
    window.loading_progress[:2] = "Spawing enemies", 11
    spawn_blocks = random.choices(list(blocks_ground), k=int(0.05 * len(blocks_ground)))
    for coord in spawn_blocks:
        world.add_entity(Slime(coord))


# Called from generate_world
def find_edge_blocks(world):
    blocks_ground = set()
    blocks_ceiling = set()
    blocks_wall_right = set() # Air blocks, which have a wall to their left
    blocks_wall_left = set()

    for coord in world.iterate():
        block_type = world.get_block(*coord, layer=0)

        if block_type == world.block_name["placeholder_terrain"]: # Generate terrain block
            generate_block(world, *coord)
            continue
        elif block_type == world.block_name["placeholder_intro"]: # Generate intro block
            generate_block(world, *coord, repeat=INTRO_REPEAT)
            continue
        elif block_type != 0: # Not air
            continue

        x, y = coord

        if world.get_block(x, y - 1) > 0: # On ground
            blocks_ground.add(coord)
        elif world.get_block(x, y + 1) > 0: # On ceiling
            blocks_ceiling.add(coord)
        elif world.get_block(x + 1, y) > 0: # On wall right
            blocks_wall_right.add(coord)
        elif world.get_block(x - 1, y) > 0: # On wall left
            blocks_wall_left.add(coord)

    return blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left


# Called from generate_world
def generate_foliage(world, block_pools, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left):
    blocks_ground = random.choices(list(blocks_ground), k=int(WORLD_VEGETATION_FLOOR_DENSITY * len(blocks_ground)))
    blocks_ceiling = random.choices(list(blocks_ceiling), k=int(WORLD_VEGETATION_CEILING_DENSITY * len(blocks_ceiling)))
    blocks_wall_right = random.choices(list(blocks_wall_right), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_right)))
    blocks_wall_left = random.choices(list(blocks_wall_left), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_left)))

    for coord in blocks_ground:
        generate_foliage_floor(world, block_pools, coord)
    for coord in blocks_ceiling:
        generate_foliage_ceiling(world, block_pools, coord)
    for coord in blocks_wall_right:
        generate_foliage_wall(world, block_pools, coord, flipped=0)
    for coord in blocks_wall_left:
        generate_foliage_wall(world, block_pools, coord, flipped=1)


# Called from generate_foliage
def generate_foliage_floor(world, block_pools, coord):
    group_layout = False

    block_pool, flipped = get_step(world, block_pools, coord, "ground")
    if not block_pool:
        flipped: bool = random.randint(0, 1)
        group: float = random.random()

        if group < 0.15:
            block_pool = block_pools["vegetation_block_group_floor"]
            group_layout = True
        elif group < 0.3:
            block_pool = block_pools["vegetation_floor_rare"]
        elif group < 0.6:
            block_pool = block_pools["vegetation_floor_uncommon"]
        else:
            block_pool = block_pools["vegetation_floor_common"]

    index = random.randint(0, len(block_pool) - 1)
    block = block_pool[index]
    if not group_layout:
        if world.get_block(*coord, world.block_layer[block]):
            return
        block_type = world.block_name[block] + flipped
        world.set_block(*coord, block_type)
    else:
        width, height = world.block_group_size[block]
        layer = world.block_layer[block + "_0_0"]
        coord = (coord[0] - width // 2, coord[1] + height - 1)

        # Check for full blocks below
        for x in range(width):
            if not world.get_block(coord[0] + x, coord[1] - height, 0):
                return

        # Check for collisions
        for x in range(width):
            for y in range(height):
                if world.get_block(coord[0] + x, coord[1] - y, layer):
                    return

        # Place blocks
        for x in range(width):
            for y in range(height):
                name = f"{block}_{abs((width - 1) * flipped - x)}_{y}"
                block_type = world.block_name[name] + flipped
                world.set_block(coord[0] + x, coord[1] - y, block_type)


def get_step(world, block_pools, coord, side):
    block_left = world.get_block(coord[0] - 1, coord[1])
    block_right = world.get_block(coord[0] + 1, coord[1])
    block_vertical = world.get_block(coord[0], coord[1] - 2 * (side == "ground") + 1)
    block_pool = []

    if block_left and not block_right:
        flipped = 1
    elif block_right and not block_left:
        flipped = 0
    else:
        return [], 0
    
    pool_identifier = world.block_family[world.block_index[block_vertical]]
    pool_identifier += ("_step_ground" if side == "ground" else "_step_ceiling")
    if pool_identifier in block_pools:
        block_pool = block_pools[pool_identifier]

    return block_pool, flipped


# Called from generate_foliage
def generate_foliage_ceiling(world, block_pools, coord):
    if not world.get_block(coord[0], coord[1] + 1, 0, False, 0):
        return

    block_pool, flipped = get_step(world, block_pools, coord, "ceiling")
    if not block_pool:
        block_pool = block_pools["vegetation_ceiling"]
        flipped = random.randint(0, 1)

    index = random.randint(0, len(block_pool) - 1)
    block = block_pool[index]

    if block.startswith("vines"):
        length = int(math.sqrt(random.random() * 64) + 1)
    else:
        length = 1

    for i in range(length):                
        block_type = world.block_name[block] + flipped
        x, y = coord[0], coord[1] - i
        if world.get_block(x, y, 0, False, 1) or world.get_block(x, y, world.block_layer[block], False, 1):
            break

        world.set_block(x, y, block_type)

        if i != length - 1:
            flipped = random.randint(0, 1)


# Called from generate_foliage
def generate_foliage_wall(world, block_pools, coord, flipped=1):
    block_pool = block_pools["vegetation_wall"]
    index = random.randint(0, len(block_pool) - 1)
    block = block_pool[index]
    if world.get_block(*coord, world.block_layer[block]):
        return
    if flipped and block + "_flipped" in world.block_name:
        block += "_flipped"
    block_type = world.block_name[block]
    world.set_block(*coord, block_type)


# Called from generate_world
def generate_poles(world, poles, blocks_ground, blocks_ceiling):
    blocks_ground = dict(blocks_ground)
    blocks_ceiling = dict(blocks_ceiling)

    for x in poles:
        if not (x in blocks_ground and x in blocks_ceiling):
            continue

        y_ground = blocks_ground[x]
        y_ceiling = max(y_ground, blocks_ceiling[x] - 2)

        for y in range(y_ground, y_ceiling):
            world.set_block(x, y, world.block_name["pole"])


# Called from generate_world
def flatten_edges(world):
    world_copy = deepcopy(world)#.copy()
    for chunk_x, chunk_y in world_copy.chunks:
        for delta_x, delta_y in numpy.ndindex((WORLD_CHUNK_SIZE, WORLD_CHUNK_SIZE)):
            block_types = [world_copy.get_block(chunk_x + pos[0], chunk_y + pos[1], layer=0, default=0) for pos in ([delta_x, delta_y], [delta_x + 1, delta_y], [delta_x - 1, delta_y], [delta_x, delta_y + 1], [delta_x, delta_y - 1])]
            block_type = max(block_types, key=block_types.count)
            world.set_block(chunk_x + delta_x, chunk_y + delta_y, block_type)


def generate_block(world, x, y, repeat=0):
    if repeat:
        z = snoise2(x / 16 + world.seed, y / 16, octaves=3, persistence=0.1, lacunarity=5, repeaty=repeat / 16)
        #z = opensimplex.noise2(x / 16, y / 16)
    else:
        z = snoise2(x / 16 + world.seed, y / 16 + world.seed, octaves=3, persistence=0.1, lacunarity=5)
        #z = opensimplex.noise2(x / 30 + world.seed, y / 30 + world.seed)

    if z < 0.2:
        world.set_block(x, y, world.block_name["grass_block"])
    else:
        world.set_block(x, y, world.block_name["stone_block"])


# Called from Shape.*
def generate_points_segment(position: [float], length, start_angle: float, deviation: float):
    angle = start_angle
    points = set()

    angle_change = 0
    max_angle_change = 0.5
    step_size = 0.5

    for i in range(length):
        position[0] = position[0] + math.cos(angle) * step_size
        position[1] = position[1] + math.sin(angle) * step_size
        points.add(tuple(position))
        angle_change = snoise2(i * 20.215 + 0.0142, 1, octaves=3) * max_angle_change
        #angle_change = opensimplex.noise2(i * 20.215 + 0.0142, 1) * max_angle_change
        angle_change -= (angle - start_angle) / deviation * max_angle_change
        angle += angle_change

    return points


# Called from Shape.*
def line_cave(world, position, length, angle, deviation, radius):
    border_padding = 4
    points = generate_points_segment(position, length, angle, deviation)

    for (x, y) in points:
        p_radius = int(pnoise1((x + y) / 2 + 100, octaves=3) * 2 + radius)
        #p_radius = int(opensimplex.noise2(1.3, (x + y) / 2 + 100) * 2 + radius)
        for delta_x in range(-radius - border_padding, radius + border_padding + 1):
            for delta_y in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(x + delta_x), int(y + delta_y))
                if delta_x ** 2 + delta_y ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif not world.get_block_exists(*coord):
                    world.set_block(*coord, world.block_name["placeholder_terrain"])


# Called from generate_world
class Shape:
    @staticmethod
    def intro(world, window, position):
        surface_size = (80, 50)
        for x in range(-surface_size[0], surface_size[0] + 1):
            surface_level = pnoise1(x / 20 + world.seed, octaves=3) * 9
            for y in range(-surface_size[0], surface_size[0] + 1):
                if surface_level < y:
                    world.set_block(x, y, 0)
                
        window.loading_progress[1] = 2

        points = set()
        start_angle = angle = -math.pi/2
        length = INTRO_LENGTH
        border_padding = 4
        deviation = 3
        lowest = 0

        for i in range(length):
            position[0] = pnoise1(i * 16 + world.seed, octaves=3, repeat=INTRO_REPEAT * 16) * deviation
            position[1] = -i
            points.add(tuple(position))

        window.loading_progress[1] = 3

        for (x, y) in points:
            radius = int((pnoise1(y + world.seed, octaves=3, repeat=INTRO_REPEAT) + 2) * 2)
            for delta_x in range(-radius - border_padding, radius + border_padding + 1):
                for delta_y in range(-radius - border_padding, radius + border_padding + 1):
                    coord = (int(x + delta_x), int(y + delta_y))
                    if delta_x ** 2 + (delta_y * 0.5) ** 2 <= radius ** 2:
                        world.set_block(*coord, 0)
                        if y + delta_y < lowest:
                            lowest = y + delta_y
                    elif not world.get_block_exists(*coord):
                        world.set_block(*coord, world.block_name["placeholder_intro"])
        position[1] = lowest
        
    @staticmethod
    def horizontal(world, position):
        angle = snoise2(position[0] / 100 + world.seed, world.seed, octaves=4) * 0.6
        length = random.randint(50, 150)
        deviation = random.randint(2, 5)
        radius = 3

        line_cave(world, position, length, angle, deviation, radius)

    @staticmethod
    def vertical(world, position, high=False):
        angle = math.pi / 2 * 3 * (random.randint(0, 1) * 2 - 1)
        if high:
            length = random.randint(40, 50)
        else:
            length = random.randint(10, 30)
        deviation = 0.5
        radius = 1

        line_cave(world, position, length, angle, deviation, radius)

    @staticmethod
    def blob(world, position):
        border_padding = 5
        radius = int((pnoise1(position[0] + world.seed, octaves=3) + 3) * 3)
        for delta_x in range(-radius - border_padding, radius + border_padding + 1):
            for delta_y in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(position[0] + delta_x), int(position[1] + delta_y))
                if delta_y > 0 and delta_x ** 2 + (delta_y * 0.8) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif delta_x ** 2 + (delta_y * 2) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
