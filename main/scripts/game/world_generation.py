# -*- coding: utf-8 -*-
from scripts.utility.const import *
from noise import *
import random
import math


# Replace with better names...? Add / Remove?
BIOMES = ["overgrown", "mushroom", "dripstone", "frozen", "underwater", "stone", "desert", "hell", "crystal", "dwarf"]
CAVE_SHAPES = ["intro", "horizontal", "vertical", "blob", "structure"]


def _random(world, x, y=0, z=0):
    return (hash(f"{world.seed}-{x}-{y}") % 2147483647) / 2147483647


def _randint(world, x: float, y: float=0.0, start: int=0, stop: int=1, z: float=0.0):
    return round(start + random(world, x, y, z + start + stop) * (stop - start))


def generate_world(world):
    """
    Main world generation function
    """
    # Starting point
    position = [0, 0]


    # Generate intro
    Shape.intro(world, position)


    # Horizontal cave
    Shape.horizontal(world, position)


    # Generate structures
    ...


    # Smoother cave walls
    flatten_edges(world)
    print("flattened edges")


    # Find block edges with air
    blocks_ground = set()
    blocks_ceiling = set()
    blocks_wall_right = set() # Air blocks, which have a wall to their left
    blocks_wall_left = set()

    for coord in world:
        block_type = world[coord][0]

        if block_type == world.block_name["placeholder0"]: # Generate terrain block
            generate_block(world, *coord)
            continue
        elif block_type == world.block_name["placeholder1"]: # Generate intro block
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
    print("Stored block edges")

    # Generate foliage
    generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)
    print("Generated foliage")


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
        if random.random() > 0.4: # Put vegetation
            if random.random() > 0.5: # Put grass
                r = random.randint(0, 2)
                block = ("plant0", "bush2", "grass0")[r]
                block_type = world.block_name[block]
            else: # Put mushroom
                r = random.randint(0, 13)
                block_type = world.block_name["mushroom" + str(r)]
            world.set_block(*coord, block_type)

    for coord in blocks_ceiling:
        if not world.get_block(coord[0], coord[1] + 1, 0, False, 0):
            continue

        if random.random() > 0.8: # Put vegetation
            length = int(math.sqrt(random.random() * 64) + 1)
            block_type = world.block_name["vines0"]
            for i in range(length):
                x, y = coord[0], coord[1] - i
                if world.get_block(x, y, 0, False, 1) or world.get_block(x, y, 1, False, 1):
                    break
                world.set_block(x, y, block_type)


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
        z = snoise2(x / 16, y / 16, octaves=3, persistence=0.1, lacunarity=5, repeaty=repeat / 16)
    else:
        z = snoise2(x / 30 + world.seed, y / 30 + world.seed, octaves=3, persistence=0.1, lacunarity=5)
    if z < 0.5:
        world.set_block(x, y, world.block_name["grass_block"])
    else:
        world.set_block(x, y, world.block_name["stone_block"])


class Shape:
    @staticmethod
    def intro(world, position):
        print("generating intro")

        surface_size = (50, 30)
        for x in range(-surface_size[0], surface_size[0] + 1):
            surface_level = pnoise1(x / 20 + world.seed, octaves=3) * 9
            for y in range(-surface_size[0], surface_size[0] + 1):
                if surface_level < y:
                    world.set_block(x, y, 0)

        points = set()
        start_angle = angle = -math.pi/2
        length = INTRO_LENGTH
        border_width = 40
        deviation = 3
        lowest = 0

        for i in range(length):
            position[0] = pnoise1(i * 16 + world.seed, octaves=3, repeat=INTRO_REPEAT * 16) * deviation
            position[1] = -i
            points.add(tuple(position))

        print("generated points")

        for (x, y) in points:
            radius = int((pnoise1(y + world.seed, octaves=3, repeat=INTRO_REPEAT) + 2) * 2)
            for dx in range(-radius - border_width, radius + border_width + 1):
                for dy in range(-radius - border_width, radius + border_width + 1):
                    coord = (int(x + dx), int(y + dy))
                    if dx ** 2 + (dy / 2) ** 2 <= radius ** 2:
                        world.set_block(*coord, 0)
                        if y + dy < lowest:
                            lowest = y + dy
                    elif not coord in world:
                        world.set_block(*coord, world.block_name["placeholder1"])

        print("mined out path\n")

        position[1] = lowest
        

    @staticmethod
    def horizontal(world, position):
        print("generated horizontal cave")

        angle = 0
        length = 2000
        deviation = 2 # 2 - 6 works fine
        border_width = 5

        points = generate_points_segment(position, length, angle, deviation)
        print("generating points")

        for (x, y) in points:
            radius = int((pnoise1((x + y) / 2 + 100, octaves=3) + 2) * 3)
            for dx in range(-radius - border_width, radius + border_width + 1):
                for dy in range(-radius - border_width, radius + border_width + 1):
                    coord = (int(x + dx), int(y + dy))
                    if dx ** 2 + dy ** 2 <= radius ** 2:
                        world.set_block(*coord, 0)
                    elif not coord in world:
                        world.set_block(*coord, world.block_name["placeholder0"])

        print("mined out path\n")


        