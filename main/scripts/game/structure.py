# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.utility import file
import numpy
import math


def load(block_name):
    """
    Load structures from files.
    """
    # Find structure files
    structure_paths: list = file.find("data/structures", "*.json", True)
    structures: dict = {}

    for path in structure_paths:
        data = file.load(path, file_format="json")
        array = file.load(path.replace("json", "npy"), file_format="numpy")

        # Adjust block indices (if they changed due to recently added blocks)
        for x, y, z in numpy.ndindex((*array.shape[:2], 3)):
            index = array[x, y, z]

            if index == 0:
                block = 0 # Air
            else:
                block = block_name[data["block_indices"][str(index)]]

            array[x, y, z] = block

        name = data["name"]
        del data["name"]
        data["array"] = array


        # Get entrance and exit size
        entrance_coord = data["generation"]["entrance_coord"]
        entrance_angle = data["generation"]["entrance_angle"] * math.pi / 180
        exit_coord = data["generation"]["exit_coord"]
        exit_angle = data["generation"]["exit_angle"] * math.pi / 180
        data["generation"]["entrance_angle"] = entrance_angle
        data["generation"]["exit_angle"] = exit_angle

        entrance_ceiling = find_cave_wall(array, entrance_coord, entrance_angle + math.pi / 2)
        entrance_floor = find_cave_wall(array, entrance_coord, entrance_angle - math.pi / 2)
        entrance_size = math.sqrt((entrance_ceiling[0] - entrance_floor[0]) ** 2 + (entrance_ceiling[1] - entrance_floor[1]) ** 2) - 2
        entrance_coord = ((entrance_ceiling[0] + entrance_floor[0]) / 2, (entrance_ceiling[1] + entrance_floor[1]) / 2)

        exit_ceiling = find_cave_wall(array, exit_coord, exit_angle + math.pi / 2)
        exit_floor = find_cave_wall(array, exit_coord, exit_angle - math.pi / 2)
        exit_size = math.sqrt((exit_ceiling[0] - exit_floor[0]) ** 2 + (exit_ceiling[1] - exit_floor[1]) ** 2) - 2
        exit_coord = ((exit_ceiling[0] + exit_floor[0]) / 2, (exit_ceiling[1] + exit_floor[1]) / 2)

        data["generation"]["entrance_coord"] = entrance_coord
        data["generation"]["entrance_size"] = entrance_size
        data["generation"]["exit_coord"] = exit_coord
        data["generation"]["exit_size"] = exit_size

        structures[name] = data

    return structures


def find_cave_wall(array, start, angle):
    width, height = array.shape[:2]
    x, y = start

    i = 0
    while 0 <= x < width and 0 <= y < height and array[x, y, 0] == 0:
        x = round(start[0] + math.cos(angle) * i)
        y = round(start[1] + math.sin(angle) * i)
        i += 0.1

    return x, y
