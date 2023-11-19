# -*- coding: utf-8 -*-
from scripts.game.world_noise import pnoise1, snoise2
from scripts.game import cave
from scripts.utility.const import *
from scripts.game import structure
from scripts.game.entity import *
from copy import deepcopy
import random
import numpy
import math


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
    cave.intro(world, window, position)

    cave.horizontal(world, position)
    # PASTE HERE TUTORIAL STRUCTURE

    # Generate cave segments
    window.loading_progress[:2] = "Generating caves", 5

    segments_count = 30
    min_special_distance = 2
    special_speading = 2
    next_special = 2

    structure_names = random.sample(list(structures.keys()), k=len(structures))
    structure_index = 0

    generated_structures = []

    for i in range(segments_count):
        next_special -= 1

        if next_special:
            # Horizontal cave
            cave.horizontal(world, position)
        else:
            # Special cave (vertical, blob or random structure)
            next_special = min_special_distance + random.randint(0, special_speading)
            cave_type = random.random()

            if cave_type < 0.5:
                # Structure
                structure_name = structure_names[structure_index]
                structure_data = structures[structure_name]

                structure_index += 1
                if structure_index == len(structures):
                    structure_names = random.sample(list(structures.keys()), k=len(structures))
                    structure_index = 0

                cave.interpolated(world, position, end_angle=structure_data["generation"]["entrance_angle"], end_radius=structure_data["generation"]["entrance_size"] / 2)

                generated_structures.append((
                    round(position[0] - structure_data["generation"]["entrance_coord"][0]),
                    round(position[1] - structure_data["generation"]["entrance_coord"][1]),
                    structure_data["array"]
                ))

                position[0] += structure_data["generation"]["exit_coord"][0] - structure_data["generation"]["entrance_coord"][0]
                position[1] += structure_data["generation"]["exit_coord"][1] - structure_data["generation"]["entrance_coord"][1]

                cave.interpolated(world, position, start_angle=structure_data["generation"]["exit_angle"], start_radius=structure_data["generation"]["exit_size"] / 2)

            elif cave_type < 0.7:
                # Branch
                if random.randint(0, 1):
                    cave.vertical(world, position)
                    poles.add(int(position[0]))
                    branches.add((*position, 0))
                else:
                    cave.horizontal(world, position)
                    branches.add((*position, 1))
            elif cave_type < 0.9:
                # Vertical (no branch)
                cave.vertical(world, position)
                poles.add(int(position[0]))
            else:
                # Blob
                cave.blob(world, position)

    for x, y, direction in branches:
        length = random.randint(2, 3)
        position = [x, y]

        if direction:
            cave.vertical(world, position)
            poles.add(int(position[0]))

        for i in range(length):
            cave.horizontal(world, position)


    # Smoother cave walls
    flatten_edges(world)

    # Generate structures between line cave segments
    window.loading_progress[:2] = "Generating structures", 7
    for x, y, array in generated_structures:
        for dx, dy in numpy.ndindex(array.shape[:2]):
            world.set_block(x + dx, y + dy, array[dx, dy], layer=slice(None))

    # Generate foliage
    window.loading_progress[:2] = "Generating foliage", 9
    
    # Find block edges with air
    blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left = find_edge_blocks(world)

    # Generate foliage
    window.loading_progress[1] = 7
    generate_foliage(world, world.block_generation_properties, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)

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

        if block_type == world.block_name["dirt_block"]: # Generate terrain block
            generate_block(world, *coord)
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
def generate_foliage(world, block_generation_properties, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left):
    blocks_ground = random.choices(list(blocks_ground), k=int(WORLD_VEGETATION_FLOOR_DENSITY * len(blocks_ground)))
    blocks_ceiling = random.choices(list(blocks_ceiling), k=int(WORLD_VEGETATION_CEILING_DENSITY * len(blocks_ceiling)))
    blocks_wall_right = random.choices(list(blocks_wall_right), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_right)))
    blocks_wall_left = random.choices(list(blocks_wall_left), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_left)))

    for (x, y) in blocks_ground + blocks_ceiling + blocks_wall_right + blocks_wall_left:
        args = get_decoration_block_type(world, x, y)
        if not args[0] is None:
            generate_decoration_block(world, x, y, *args)



# Called from generate_foliage
def generate_foliage_floor(world, block_generation_properties, coord):
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


def get_decoration_block_type(world, x, y):
    block_below = world.get_block(x, y - 1)
    block_above = world.get_block(x, y + 1)
    block_left = world.get_block(x - 1, y)
    block_right = world.get_block(x + 1, y)
    water_level = world.get_water(x, y)

    # Exit early
    if (block_below and block_above) or (0 < water_level < 700):
        return [None]
    if block_left and block_right:
        water = random.random()
        if water > 0.9:
            world.set_water(x, y, (water - 0.7) * 2000)
        return [None]

    corner = False
    flipped = random.randint(0, 1)

    # Define requirements
    if block_below:
        side = "above"
        block_name = world.block_index[block_below]
        if block_left:
            corner = random.randint(0, 1)
            flipped = 1
        elif block_right:
            corner = random.randint(0, 1)
            flipped = 0

    elif block_above:
        side = "below"
        block_name = world.block_index[block_above]
        if block_left:
            corner = random.randint(0, 1)
            flipped = 1
        elif block_right:
            corner = random.randint(0, 1)
            flipped = 0

    elif block_left:
        side = "wall"
        block_name = world.block_index[block_left]
        flipped = 1

    elif block_right:
        side = "wall"
        block_name = world.block_index[block_right]
        flipped = 0

    block_comparison = ("any", block_name, world.block_family[block_name])
    block_generation_properties = world.block_generation_properties

    decoration_list = list(filter(lambda name: (
        world.block_generation_properties[name].get("on", "any") in block_comparison and
        side == world.block_generation_properties[name].get("side", "above") and
        water_level >= world.block_generation_properties[name].get("water", False) and
        corner == world.block_generation_properties[name].get("corner", False)
    ), list(world.block_generation_properties)))

    decoration_block = random.choices(decoration_list, weights=[world.block_generation_properties[name].get("weight", 1) for name in decoration_list])

    if len(decoration_block):
        decoration_block = decoration_block[0]
    else:
        decoration_block = None

    return decoration_block, flipped, side


def generate_decoration_block(world, x, y, decoration_block, flipped, side):
    expansion_length = int(math.sqrt(random.random() * (world.block_generation_properties[decoration_block].get("expansion_length", 1) - 1) ** 2) + 1)
    expansion_direction = {"up": math.pi / 2, "down": -math.pi / 2, "left": math.pi, "right": 0}.get(world.block_generation_properties[decoration_block].get("expansion_direction", "up"), 0)

    size = world.block_group_size.get(decoration_block, (1, 1))
    if size == (1, 1):
        if world.get_block(x, y, world.block_layer[decoration_block]):
            return

        for i in range(expansion_length):
            dx = round(math.cos(expansion_direction) * i)
            dy = round(math.sin(expansion_direction) * i)
            block_type = world.block_name[decoration_block] + flipped
            world.set_block(x + dx, y + dy, block_type)
            flipped = random.randint(0, 1)

    else:
        width, height = world.block_group_size[decoration_block]
        layer = world.block_layer[decoration_block + "_0_0"]

        if side == "above":
            coord = (x - size[0] // 2, y + size[1] - 1)
            for dx in range(width):
                if not world.get_block(coord[0] + dx, y - 1):
                    return
            
        elif side == "below":
            coord = (x - size[0] // 2, y)
            for dx in range(width):
                if not world.get_block(coord[0] + dx, y + 1):
                    return

        else:
            raise Exception("Grouped blocks on walls not implemented yet!")

        # Check for collisions
        for dx, dy in numpy.ndindex(size):
            if any(world.get_block(coord[0] + dx, coord[1] - dy, layer=slice(3), default=[1])):
                return

        # Place blocks
        for x in range(width):
            for y in range(height):
                name = f"{decoration_block}_{abs((width - 1) * flipped - x)}_{y}"
                block_type = world.block_name[name] + flipped
                world.set_block(coord[0] + x, coord[1] - y, block_type)


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
    block_type = world.block_name[block] + flipped
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
    world_copy = deepcopy(world)
    for x, y in world_copy.iterate():
        block_types = [world_copy.get_block(x + dx, y + dy, layer=0, default=0) for dx in range(-1, 2) for dy in range(-1, 2)]
        block_type = max(block_types, key=block_types.count)
        world.set_block(x, y, block_type)


def generate_block(world, x, y, repeat=0):
    if x > 30:
        z = snoise2(x / 8 + world.seed, y / 8 + world.seed, octaves=3, persistence=0.1, lacunarity=5)
    if x > 20: # Interpolation (from intro )
        z1 = snoise2(x / 16 + world.seed, y / 16, octaves=3, persistence=0.1, lacunarity=5, repeaty=repeat / 16)
        z2 = snoise2(x / 8 + world.seed, y / 8 + world.seed, octaves=3, persistence=0.1, lacunarity=5)
        i = (x - 20) / 10
        z = z1 * i + z2 * (1 - i)
    else: # Repeating (intro)
        z = snoise2(x / 16 + world.seed, y / 16, octaves=3, persistence=0.1, lacunarity=5, repeaty=repeat / 16)

    threshold = 0.2 # -1 < z < 1

    block = "dirt_block"
    if z < threshold and world.get_block(x, y + 1) == 0: # When air is above
        block = "grass_block"
    elif z >= threshold:
        block = "stone_block"
    
    world.set_block(x, y, world.block_name[block])
