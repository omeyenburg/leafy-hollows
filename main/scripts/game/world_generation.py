# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.game import structure
import random
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
                if random.random() > 0.5:
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
    generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)

    # Generate poles
    generate_poles(world, poles, blocks_ground, blocks_ceiling)

    window.loading_progress[:2] = "Finishing", 11


# Called from generate_world
def find_edge_blocks(world):
    blocks_ground = set()
    blocks_ceiling = set()
    blocks_wall_right = set() # Air blocks, which have a wall to their left
    blocks_wall_left = set()

    for coord in world:
        block_type = world[coord][0]

        if block_type == world.block_name["placeholder_terrain"]: # Generate terrain block
            generate_block(world, *coord)
            continue
        elif block_type == world.block_name["placeholder_intro"]: # Generate intro block
            generate_block(world, *coord, repeat=INTRO_REPEAT)
            continue
        elif block_type != 0: # Not air
            continue

        x, y = coord

        if world.get_block(x, y - 1, generate=False) > 0: # On ground
            blocks_ground.add(coord)
        elif world.get_block(x, y + 1, generate=False) > 0: # On ceiling
            blocks_ceiling.add(coord)
        else:
            if world.get_block(x + 1, y, generate=False) > 0: # On wall right
                blocks_wall_right.add(coord)
            if world.get_block(x - 1, y, generate=False) > 0: # On wall left
                blocks_wall_left.add(coord)

    return blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left


# Called from generate_world
def generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left):
    blocks_ground = random.choices(list(blocks_ground), k=int(WORLD_VEGETATION_FLOOR_DENSITY * len(blocks_ground)))
    blocks_ceiling = random.choices(list(blocks_ceiling), k=int(WORLD_VEGETATION_CEILING_DENSITY * len(blocks_ceiling)))
    blocks_wall_right = random.choices(list(blocks_wall_right), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_right)))
    blocks_wall_left = random.choices(list(blocks_wall_left), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_left)))

    for coord in blocks_ground:
        generate_foliage_floor(world, coord)

    for coord in blocks_ceiling:
        generate_foliage_ceiling(world, coord)

    for coord in blocks_wall_right:
        generate_foliage_wall(world, coord, flipped=0)
    
    for coord in blocks_wall_left:
        generate_foliage_wall(world, coord, flipped=1)


# Called from generate_foliage
def generate_foliage_floor(world, coord):
    wall_left = world.get_block(coord[0] - 1, coord[1], generate=False)
    wall_right = world.get_block(coord[0] + 1, coord[1], generate=False)

    if wall_left and not wall_right:
        block_pool = BLOCKS_STEP_GROUND
        flipped = 1
    elif wall_right and not wall_left:
        block_pool = BLOCKS_STEP_GROUND
        flipped = 0
    else:
        flipped: bool = random.random() > 0.5
        group: float = random.random()
        group_layout: bool = False

        if group < 0.15:
            block_pool = BLOCKS_VEGETATION_GROUP_FLOOR
            group_layout = True
        elif group < 0.3:
            block_pool = BLOCKS_VEGETATION_FLOOR_RARE
        elif group < 0.6:
            block_pool = BLOCKS_VEGETATION_FLOOR_UNCOMMON
        else:
            block_pool = BLOCKS_VEGETATION_FLOOR_COMMON
    
    index = random.randint(0, len(block_pool) - 1)
    block = block_pool[index]
    if isinstance(block, str):
        if block + "_flipped" in world.block_name and flipped:
            block += "_flipped"
        if world.get_block(*coord, world.block_layer[block]):
            return
        block_type = world.block_name[block]
        world.set_block(*coord, block_type)
    else:
        coord = (coord[0] - block[1] // 2, coord[1] + block[2] - 1)

        # Check for full blocks below
        for x in range(block[1]):
            if not world.get_block(coord[0] + x, coord[1] - block[2], 0):
                return

        # Check for collisions
        for x in range(block[1]):
            for y in range(block[2]):
                if world.get_block(coord[0] + x, coord[1] - y, world.block_layer[block[0] + "_0_0"]):
                    return

        # Place blocks
        for x in range(block[1]):
            for y in range(block[2]):
                name = f"{block[0]}_{x}_{y}"
                block_type = world.block_name[name]
                world.set_block(coord[0] + x, coord[1] - y, block_type)


# Called from generate_foliage
def generate_foliage_ceiling(world, coord):
    if not world.get_block(coord[0], coord[1] + 1, 0, False, 0):
        return

    index = random.randint(0, len(BLOCKS_VEGETATION_CEILING) - 1)
    block = BLOCKS_VEGETATION_CEILING[index]

    if block.startswith("vines"):
        length = int(math.sqrt(random.random() * 64) + 1)
    else:
        length = 1

    for i in range(length):                
        if random.random() > 0.5:
            block_type = world.block_name[block + "_flipped"]
        else:
            block_type = world.block_name[block]
        x, y = coord[0], coord[1] - i
        if world.get_block(x, y, 0, False, 1) or world.get_block(x, y, world.block_layer[block], False, 1):
            break
        world.set_block(x, y, block_type)


# Called from generate_foliage
def generate_foliage_wall(world, coord, flipped=1):
    index = random.randint(0, len(BLOCKS_VEGETATION_WALL) - 1)
    block = BLOCKS_VEGETATION_WALL[index]
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
    s = world.copy()
    p = 0
    for (x, y) in s:
        block_types = [s.get(tuple(pos), (0, 0, 0, 0))[0] for pos in ([x, y], [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1])]
        block_type = max(block_types, key=block_types.count)
        world.set_block(x, y, block_type)


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
        for dx in range(-radius - border_padding, radius + border_padding + 1):
            for dy in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(x + dx), int(y + dy))
                if dx ** 2 + dy ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif not coord in world:
                    world.set_block(*coord, world.block_name["placeholder_terrain"])


# Called from generate_world
class Shape:
    @staticmethod
    def intro(world, window, position):
        surface_size = (50, 30)
        for x in range(-surface_size[0], surface_size[0] + 1):
            surface_level = pnoise1(x / 20 + world.seed, octaves=3) * 9
            #surface_level = opensimplex.noise2(1.3, x / 20 + world.seed) * 9
            for y in range(-surface_size[0], surface_size[0] + 1):
                if surface_level < y:
                    world.set_block(x, y, 0)
                
        window.loading_progress[1] = 2

        points = set()
        start_angle = angle = -math.pi/2
        length = INTRO_LENGTH
        border_padding = 40
        deviation = 3
        lowest = 0

        for i in range(length):
            position[0] = pnoise1(i * 16 + world.seed, octaves=3, repeat=INTRO_REPEAT * 16) * deviation
            #position[0] = opensimplex.noise2(1.3, i * 16 + world.seed) * deviation
            position[1] = -i
            points.add(tuple(position))

        window.loading_progress[1] = 3

        for (x, y) in points:
            radius = int((pnoise1(y + world.seed, octaves=3, repeat=INTRO_REPEAT) + 2) * 2)
            #radius = int((opensimplex.noise2(1.3, y + world.seed) + 2) * 2)
            for dx in range(-radius - border_padding, radius + border_padding + 1):
                for dy in range(-radius - border_padding, radius + border_padding + 1):
                    coord = (int(x + dx), int(y + dy))
                    if dx ** 2 + (dy * 0.5) ** 2 <= radius ** 2:
                        world.set_block(*coord, 0)
                        if y + dy < lowest:
                            lowest = y + dy
                    elif not coord in world:
                        world.set_block(*coord, world.block_name["placeholder_intro"])
        position[1] = lowest
        
    @staticmethod
    def horizontal(world, position):
        angle = snoise2(position[0] / 100 + world.seed, world.seed, octaves=4) * 0.6
        #angle = opensimplex.noise2(position[0] / 100 + world.seed, world.seed) * 0.6
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
        #radius = int((opensimplex.noise2(1.3, position[0] + world.seed) + 3) * 3)
        for dx in range(-radius - border_padding, radius + border_padding + 1):
            for dy in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(position[0] + dx), int(position[1] + dy))
                if dy > 0 and dx ** 2 + (dy * 0.8) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif dx ** 2 + (dy * 2) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
