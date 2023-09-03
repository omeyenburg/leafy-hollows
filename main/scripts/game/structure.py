# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.utility import file
import numpy


def load(block_name):
    """
    Load structures from files.
    """
    # Find structure files
    structure_paths = file.find("data/structures", "*.struct", True)
    structures = []

    # Load structures
    for path in structure_paths:
        structures.append(file.read(path, file_format="pickle"))

    # Convert structure indices to world indices
    for structure in structures:
        for x, y, z in numpy.ndindex((*structure["size"], 3)):
            index = structure["array"][x, y, z]
            if index == 0:
                block = 0 # Air
            else:
                block = block_name[structure["block_indices"][index]]
            structure["array"][x, y, z] = block

    return structures
