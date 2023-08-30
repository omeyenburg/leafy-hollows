# -*- coding: utf-8 -*-
from scripts.utility.const import *
#from noise import *
import opensimplex
import scripts.game.structure as structure
import random
import math


# Replace with better names...? Add / Remove?
BIOMES = ["overgrown", "mushroom", "dripstone", "frozen", "underwater", "stone", "desert", "hell", "crystal", "dwarf"]
CAVE_SHAPES = ["intro", "horizontal", "vertical", "blob", "structure"]

"""
def _random(world, x, y=0, z=0):
    return (hash(f"{world.seed}-{x}-{y}") % 2147483647) / 2147483647
def _randint(world, x: float, y: float=0.0, start: int=0, stop: int=1, z: float=0.0):
    return round(start + random(world, x, y, z + start + stop) * (stop - start))
"""


def generate_world(world):
    """
    Main world generation function
    """
    # Load structures
    structures = structure.load(world.block_name)

    # Starting point
    branches = set()
    position = [0, 0]
    poles = set() # List of x coords of poles

    # Generate intro
    print("generate intro cave")
    Shape.intro(world, position)

    # Line cave segment
    last_special = 0
    for i in range(30):
        last_special += 1
        cave_type = random.random()

        if cave_type > 0.6 or last_special < 4:
            print("generate horizontal cave")
            Shape.horizontal(world, position)
        else:
            last_special = 0
            cave_type = random.random()

            if cave_type > 0.6:
                if random.random() > 0.5:
                    print("generate vertical cave (branch)")
                    Shape.vertical(world, position, True)
                    poles.add(int(position[0]))
                    branches.add((*position, 0))
                else:
                    print("generate horizontal cave (branch)")
                    Shape.horizontal(world, position)
                    branches.add((*position, 1))
            elif cave_type > 0.3:
                print("generate vertical cave")
                Shape.vertical(world, position)
                poles.add(int(position[0]))
            else:
                print("generate blob cave")
                Shape.blob(world, position)

    for x, y, direction in branches:
        length = random.randint(2, 3)
        position = [x, y]

        if direction:
            print("generate vertical cave (branch)")
            Shape.vertical(world, position, True)
            poles.add(int(position[0]))

        for i in range(length):
            print("generate horizontal cave")
            Shape.horizontal(world, position)

    # Generate structures between line cave segments
    ...

    # Smoother cave walls
    flatten_edges(world)
    print("flattened edges")

    # Find block edges with air
    print("store block edges")
    blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left = find_edge_blocks(world)

    # Generate foliage
    print("generate foliage")
    generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)

    # Generate poles
    print("generate poles")
    generate_poles(world, poles, blocks_ground, blocks_ceiling)

    print("done")


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


def generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left):
    """
    for coord in blocks_ground:
        if _random(world, *coord) > 0.4: # Put vegetation
            if _random(world, *coord, 1) > 0.5: # Put grass
                r = _randint(world, *coord, 0, 2)
                block = ("plant0", "bush2", "grass0")[r]
                block_type = world.block_name[block]
            else: # Put mushroom
                r = _randint(world, *coord, 0, 13, z=2140)
                block_type = world.block_name["mushroom" + str(r)]
            world.set_block(*coord, block_type)
    """
    for coord in blocks_ground:
        if random.random() > 0.2:
            group = random.random()
            if group < 0.2:
                block_pool = BLOCKS_VEGETATION_FLOOR_RARE
            elif group < 0.4:
                block_pool = BLOCKS_VEGETATION_FLOOR_UNCOMMON
            else:
                block_pool = BLOCKS_VEGETATION_FLOOR_COMMON
            
            index = random.randint(0, len(block_pool) - 1)
            flipped = random.random() > 0.5
            block = block_pool[index]
            if flipped and block + "_flipped" in world.block_name:
                block += "_flipped"
            block_type = world.block_name[block]
            world.set_block(*coord, block_type)

    for coord in blocks_ceiling:
        if not world.get_block(coord[0], coord[1] + 1, 0, False, 0):
            continue

        if random.random() > 0.5:
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
                if world.get_block(x, y, 0, False, 1) or world.get_block(x, y, 1, False, 1):
                    break

                world.set_block(x, y, block_type)


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
        #angle_change = snoise2(i * 20.215 + 0.0142, 1, octaves=3) * max_angle_change
        angle_change = opensimplex.noise2(i * 20.215 + 0.0142, 1) * max_angle_change
        angle_change -= (angle - start_angle) / deviation * max_angle_change
        angle += angle_change

    return points


def flatten_edges(world):
    s = world.copy()
    p = 0
    for (x, y) in s:
        block_types = [s.get(tuple(pos), (0, 0, 0, 0))[0] for pos in ([x, y], [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1])]
        block_type = max(block_types, key=block_types.count)
        world.set_block(x, y, block_type)


def generate_block(world, x, y, repeat=0):
    if repeat:
        #z = snoise2(x / 16, y / 16, octaves=3, persistence=0.1, lacunarity=5, repeaty=repeat / 16)
        z = opensimplex.noise2(x / 16, y / 16)

    else:
        #z = snoise2(x / 30 + world.seed, y / 30 + world.seed, octaves=3, persistence=0.1, lacunarity=5)
        z = opensimplex.noise2(x / 30 + world.seed, y / 30 + world.seed)
    if z < 0.5:
        world.set_block(x, y, world.block_name["grass_block"])
    else:
        world.set_block(x, y, world.block_name["stone_block"])


def line_cave(world, position, length, angle, deviation, radius):
    border_padding = 4
    points = generate_points_segment(position, length, angle, deviation)

    for (x, y) in points:
        #p_radius = int(pnoise1((x + y) / 2 + 100, octaves=3) * 2 + radius)
        p_radius = int(opensimplex.noise2(1.3, (x + y) / 2 + 100) * 2 + radius)
        for dx in range(-radius - border_padding, radius + border_padding + 1):
            for dy in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(x + dx), int(y + dy))
                if dx ** 2 + dy ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif not coord in world:
                    world.set_block(*coord, world.block_name["placeholder_terrain"])


class Shape:
    @staticmethod
    def intro(world, position):
        surface_size = (50, 30)
        for x in range(-surface_size[0], surface_size[0] + 1):
            #surface_level = pnoise1(x / 20 + world.seed, octaves=3) * 9
            surface_level = opensimplex.noise2(1.3, x / 20 + world.seed) * 9
            for y in range(-surface_size[0], surface_size[0] + 1):
                if surface_level < y:
                    world.set_block(x, y, 0)

        points = set()
        start_angle = angle = -math.pi/2
        length = INTRO_LENGTH
        border_padding = 40
        deviation = 3
        lowest = 0

        for i in range(length):
            #position[0] = pnoise1(i * 16 + world.seed, octaves=3, repeat=INTRO_REPEAT * 16) * deviation
            position[0] = opensimplex.noise2(1.3, i * 16 + world.seed) * deviation
            position[1] = -i
            points.add(tuple(position))

        for (x, y) in points:
            #radius = int((pnoise1(y + world.seed, octaves=3, repeat=INTRO_REPEAT) + 2) * 2)
            radius = int((opensimplex.noise2(1.3, y + world.seed) + 2) * 2)
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
        #angle = snoise2(position[0] / 100 + world.seed, world.seed, octaves=4) * 0.6
        angle = opensimplex.noise2(position[0] / 100 + world.seed, world.seed) * 0.6
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
        #radius = int((pnoise1(position[0] + world.seed, octaves=3) + 3) * 3)
        radius = int((opensimplex.noise2(1.3, position[0] + world.seed) + 3) * 3)
        for dx in range(-radius - border_padding, radius + border_padding + 1):
            for dy in range(-radius - border_padding, radius + border_padding + 1):
                coord = (int(position[0] + dx), int(position[1] + dy))
                if dy > 0 and dx ** 2 + (dy * 0.8) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif dx ** 2 + (dy * 2) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)



        
