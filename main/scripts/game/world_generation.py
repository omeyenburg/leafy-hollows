# -*- coding: utf-8 -*-
from scripts.utility.noise_functions import pnoise1, snoise2
from scripts.utility.const import *
from scripts.game import structure
from scripts.game.entity import *
from scripts.game import cave
import copy


# Replace with better names...? Add / Remove?
BIOMES = ["overgrown", "mushroom", "dripstone", "frozen", "underwater", "stone", "desert", "hell", "crystal", "dwarf"]
CAVE_SHAPES = ["intro", "horizontal", "vertical", "blob", "structure"]


# Called from World
def generate_world(world, window):
    """
    Main world generation function
    """
    world.seed: float = random.randint(-10**6, 10**6) + e # Float between -10^6 and 10^6
    window.loading_progress[2] = 11

    # Load structures
    window.loading_progress[:2] = "Loading structures", 0
    structures = structure.load(world.block_name)
    goal_structure = structures["goal"]
    del structures["goal"]

    # Starting point
    position = [0, 0]
    poles = set() # List of x coords of poles

    # Generate intro
    window.loading_progress[:2] = "Generating intro", 1
    cave.intro(world, window, position)

    cave.horizontal(world, position)

    # Generate cave segments
    window.loading_progress[:2] = "Generating caves", 5

    segments_count = 50
    min_special_distance = 2
    special_speading = 2
    next_special = 5

    structure_names = random.sample(list(structures.keys()), k=len(structures))
    structure_names[0] = "ice_cave2"
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

            if cave_type < 0.6:
                # Structure
                structure_name = structure_names[structure_index]
                structure_data = structures[structure_name]

                structure_index += 1
                if structure_index == len(structures):
                    structure_names = random.sample(list(structures.keys()), k=len(structures))
                    structure_index = 0

                cave.interpolated(world, position, end_angle=structure_data["generation"]["entrance_angle"], end_radius=structure_data["generation"]["entrance_size"] / 2)

                generated_structure = (
                    round(position[0] - structure_data["generation"]["entrance_coord"][0]),
                    round(position[1] - structure_data["generation"]["entrance_coord"][1]),
                    structure_data["array"]
                )

                generated_structures.append(generated_structure)

                for dx, dy in numpy.ndindex(generated_structure[2].shape[:2]):
                    world.set_block(generated_structure[0] + dx, generated_structure[1] + dy, world.block_name["dirt_block"])

                position[0] += structure_data["generation"]["exit_coord"][0] - structure_data["generation"]["entrance_coord"][0]
                position[1] += structure_data["generation"]["exit_coord"][1] - structure_data["generation"]["entrance_coord"][1]

                cave.interpolated(world, position, start_angle=structure_data["generation"]["exit_angle"], start_radius=structure_data["generation"]["exit_size"] / 2)

            elif cave_type < 0.9:
                # Vertical (no branch)
                cave.vertical(world, position)
                poles.add(int(position[0]))

            else:
                # Blob
                cave.blob(world, position)


    structure_data = goal_structure
    cave.interpolated(world, position, end_angle=structure_data["generation"]["entrance_angle"], end_radius=structure_data["generation"]["entrance_size"] / 2)
    last_enemy_x = position[0]
    world.camera_stop = position[0] + 40
    generated_structures.append((
        round(position[0] - structure_data["generation"]["entrance_coord"][0]),
        round(position[1] - structure_data["generation"]["entrance_coord"][1]),
        structure_data["array"]
    ))

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

     # Generate poles
    poles_successful = generate_poles(world, poles, blocks_ground, blocks_ceiling)
    if not poles_successful:
        return 0

    # Generate foliage
    generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left)

    # Spawn enemies
    window.loading_progress[:2] = "Spawing enemies", 11
    spawn_blocks = sorted(random.sample(list(blocks_ground), k=int(0.1 * len(blocks_ground))))
    last_bat = 0

    for coord in spawn_blocks:
        if coord[0] < 30 or coord[1] > -500 or world.get_block(coord[0], coord[1] + 1) or coord[0] > last_enemy_x or world.get_water(coord[0], coord[1]):
            continue
        if coord[0] < 100:
            Entity = GreenSlime
        elif coord[0] < 300:
            Entity = random.choice((GreenSlime, Bat))
        elif coord[0] < 400:
            Entity = random.choice((GreenSlime, Bat, Goblin))
        elif coord[0] < 600:
            Entity = random.choice((GreenSlime, YellowSlime, Bat, Goblin))
        else:
            Entity = random.choice((GreenSlime, YellowSlime, BlueSlime, Bat, Goblin))
        if Entity == Bat:
            if coord[0] < last_bat + 10:
                continue
            last_bat = coord[0]
        world.add_entity(Entity(coord))

    return 1


# Called from generate_world
def find_edge_blocks(world):
    blocks_ground = set()
    blocks_ceiling = set()
    blocks_wall_right = set()
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
def generate_foliage(world, blocks_ground, blocks_ceiling, blocks_wall_right, blocks_wall_left):
    blocks_ground = random.sample(list(blocks_ground), k=int(WORLD_VEGETATION_FLOOR_DENSITY * len(blocks_ground)))
    blocks_ceiling = random.choices(list(blocks_ceiling), k=int(WORLD_VEGETATION_CEILING_DENSITY * len(blocks_ceiling)))
    blocks_wall_right = random.choices(list(blocks_wall_right), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_right)))
    blocks_wall_left = random.choices(list(blocks_wall_left), k=int(WORLD_VEGETATION_WALL_DENSITY * len(blocks_wall_left)))

    for (x, y) in blocks_ground + blocks_ceiling + blocks_wall_right + blocks_wall_left:
        args = get_decoration_block_type(world, x, y)
        if not args[0] is None:
            generate_decoration_block(world, x, y, *args)


def get_decoration_block_type(world, x, y):
    block_below = world.get_block(x, y - 1)
    block_above = world.get_block(x, y + 1)
    block_left = world.get_block(x - 1, y)
    block_right = world.get_block(x + 1, y)
    water_level = world.get_water(x, y)

    # Exit early
    if (block_below and block_above) or (0 < water_level < 700) or (block_below != world.block_name["grass_block"] and random.random() > 0.4):
        return [None]
    if block_left and block_right and block_below:
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

    else:
        return [None]

    block_comparison = ("any", block_name, world.block_family[block_name])
    block_generation_properties = world.block_generation_properties

    decoration_list = list(filter(lambda name: (
        any([selected in block_comparison for selected in world.block_generation_properties[name].get("on", "any").split("|")]) and
        side == world.block_generation_properties[name].get("side", "above") and
        water_level >= world.block_generation_properties[name].get("water", False) and
        corner == world.block_generation_properties[name].get("corner", False)
    ), list(world.block_generation_properties)))

    if not len(decoration_list):
        return [None]

    decoration_block = random.choices(decoration_list, weights=[world.block_generation_properties[name].get("weight", 1) for name in decoration_list])

    if len(decoration_block):
        decoration_block = decoration_block[0]
    else:
        decoration_block = None

    return decoration_block, flipped, side


def generate_decoration_block(world, x, y, decoration_block, flipped, side):
    expansion_length = int(sqrt(random.random() * (world.block_generation_properties[decoration_block].get("expansion_length", 1) - 1) ** 2) + 1)
    expansion_direction = {"up": pi / 2, "down": -pi / 2, "left": pi, "right": 0}.get(world.block_generation_properties[decoration_block].get("expansion_direction", "up"), 0)

    size = world.block_group_size.get(decoration_block, (1, 1))
    if size == (1, 1):
        layer = world.block_layer[decoration_block]

        for i in range(expansion_length):
            dx = round(cos(expansion_direction) * i)
            dy = round(sin(expansion_direction) * i)

            if world.get_block(x + dx, y + dy, layer):
                return

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


# Called from generate_world
def generate_poles(world, poles, blocks_ground, blocks_ceiling):
    blocks_ground = dict(blocks_ground)
    blocks_ceiling = dict(blocks_ceiling)

    for x in poles:
        pole_x = x
        pole_y_ground = 0
        pole_y_ceiling = 0
        pole_height = 0

        for x_offest in range(-2, 3):
            if not ((x + x_offest) in blocks_ground and (x + x_offest) in blocks_ceiling):
                continue

            y_ground = blocks_ground[x + x_offest]
            y_ceiling = max(y_ground, blocks_ceiling[x + x_offest] - 2)
            height = y_ceiling - y_ground - abs(x_offest)

            if height > pole_height:
                pole_x = x + x_offest
                pole_y_ground = y_ground
                pole_y_ceiling = y_ceiling
                pole_height = height

        if not pole_height:
            print("Could not generate a pole at x=" + str(x))
            return False

        for y in range(pole_y_ground, pole_y_ceiling):
            world.set_block(pole_x, y, world.block_name["pole"])
            world.set_block(pole_x, y, 0, 0)

    return True


# Called from generate_world
def flatten_edges(world):
    world_copy = copy.deepcopy(world)
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
