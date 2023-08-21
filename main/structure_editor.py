# -*- coding: utf-8 -*-
from tkinter import filedialog
from pygame.locals import *
import scripts.utility.file as file
import random
import pygame
import pickle
import numpy
import sys
import os


def get_file():
    print("\n"*5)
    edit_file = input("Enter 'e' to edit a file or nothing to create a new file: ") == "e"

    if edit_file:
        print("Select file")
        filepath = filedialog.askopenfilename(
            title="Select file",
            filetypes=(("Structures", "*.struct"),),
            initialdir=os.path.join(os.path.dirname(__file__), "data", "structures"))
        # Read file or exit
        with open(filepath, 'rb') as f:
            structure_data = pickle.load(f)
        print("selected", filepath)
    else:
        print("Choose file name")
        filepath = filedialog.asksaveasfilename(
            title="Choose file name",
            filetypes=(("Structures", "*.struct"),),
            initialdir=os.path.join(os.path.dirname(__file__), "data", "structures")
        )
        if not filepath:
            raise Exception

        name = os.path.basename(filepath).split(".")[0]
        width = abs(int(input("Choose the width: ")))
        height = abs(int(input("Choose the height: ")))
        array = numpy.zeros((width, height, 4), dtype=int)
        structure_data = {"name": name, "size": (width, height), "array": array}

        print("created", filepath)

    return filepath, structure_data


def save():
    for x, y, z in numpy.ndindex(structure_data["array"].shape):
        if z == 3:
            # Water layer
            continue
        if structure_string_array[x][y][z] == "air":
            structure_string_array[x][y][z] = 0
        else:
            block_name = structure_string_array[x][y][z]
            structure_string_array[x][y][z] = block_data[block_name][0]
    structure_data["array"] = numpy.array(structure_string_array, dtype=int)

    with open(filepath, 'wb') as f:
        pickle.dump(structure_data, f)


def load_blocks():
    block_paths = file.find("data/images/blocks", "*.json", True) 
    block_data = {}
    block_indices = {}

    for i, path in enumerate(block_paths):
        data = file.read_json(path)
        block = data["name"]
        image_name = data["frames"][0]
        path = file.find("data/images/blocks", image_name, True)[0]
        block_surface = pygame.image.load(path)

        block_data[data["name"]] = (i + 1, data["layer"], block_surface)
        block_indices[i + 1] = data["name"]
    return block_data, block_indices


filepath, structure_data = get_file()
block_data, block_indices = load_blocks()
structure_string_array = structure_data["array"].tolist()


for x, y, z in numpy.ndindex(structure_data["array"].shape):
    if z == 3:
        # Water layer
        continue
    if structure_string_array[x][y][z] == 0:
        structure_string_array[x][y][z] = "air"
    elif "block_indices" in structure_data:
        block_name = structure_data["block_indices"][structure_string_array[x][y][z]]
        structure_string_array[x][y][z] = block_name
    else:
        raise Exception

structure_data["block_indices"] = block_indices


del filedialog # Collision with pygame
pygame.init()
window = pygame.display.set_mode()
offset = [0, 0]
offset_block_list = 0
BLOCK_SIZE = 32
font = pygame.freetype.SysFont(None, 10)
options = {"erase": 0, "draw": 0, "draw water": 0, "add water": 0, "sub water": 0, "layer0": 1, "layer1": 1, "layer2": 1, "layer3": 1, "draw layer": 0}
selected_block = list(block_data.keys())[0]


def get_block_rect(x, y):
    return pygame.Rect((x + offset[0]) * BLOCK_SIZE, (y + offset[1]) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)


can_draw = 0
while True:
    mouse_down = 0
    window.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == QUIT:
            save()
            pygame.quit()
            sys.exit()
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_down = 1
                can_draw = 1

    keys = pygame.key.get_pressed()
    if keys[K_RIGHT]:
        offset[0] = min(1, offset[0] + 0.1 / structure_data["size"][0])
    if keys[K_LEFT]:
        offset[0] = max(0, offset[0] - 0.1 / structure_data["size"][0])
    if keys[K_DOWN]:
        offset[1] = min(1, offset[1] + 0.1 / structure_data["size"][1])
    if keys[K_UP]:
        offset[1] = max(0, offset[1] - 0.1 / structure_data["size"][1])

    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed(5)
    if mouse_buttons[3]:
        offset_block_list = min(1, offset_block_list + 0.1)
    elif mouse_buttons[4]:
        offset_block_list = max(0, offset_block_list - 0.1)

    if mouse_buttons[0] and mouse_pos[0] < window.get_width() - 120:
        block_coord = (mouse_pos[0] // BLOCK_SIZE - offset[0], mouse_pos[1] // BLOCK_SIZE - offset[1])
        if block_coord[0] < structure_data["size"][0] and block_coord[1] < structure_data["size"][1]:
            if options["erase"]:
                if options["draw layer"] == 3:
                    structure_string_array[block_coord[0]][block_coord[1]][options["draw layer"]] = 0
                else:
                    structure_string_array[block_coord[0]][block_coord[1]][options["draw layer"]] = "air"
            elif options["draw"] and options["draw layer"] != 3:
                layer = block_data[selected_block][1]
                structure_string_array[block_coord[0]][block_coord[1]][layer] = selected_block
            elif options["draw water"] and can_draw:
                level = 1000
                if options["add water"]:
                    level = min(1000, structure_string_array[block_coord[0]][block_coord[1]][3] + 100)
                    can_draw = 0
                if options["sub water"] and mouse_down:
                    level = max(0, structure_string_array[block_coord[0]][block_coord[1]][3] - 100)
                    can_draw = 0
                structure_string_array[block_coord[0]][block_coord[1]][3] = level

    for x, y in numpy.ndindex(structure_data["array"].shape[:2]):
        for z in reversed(range(4)):
            if not options["layer" + str(z)]:
                continue
            if z == 3:
                rect = get_block_rect(x, y)
                rect.height = structure_string_array[x][y][z] / 1000 * rect.height
                rect.y += BLOCK_SIZE - rect.height
                pygame.draw.rect(window, (50, 40, 150), rect)
            else:
                block = structure_string_array[x][y][z]
                if block == "air":
                    continue
                rect = get_block_rect(x, y)
                surface = block_data[block][2]
                window.blit(pygame.transform.scale(surface, (BLOCK_SIZE, BLOCK_SIZE)), rect.topleft)

    for i, (option, value) in enumerate(options.items()):
        if option == "draw layer":
            color = (0, 0, 0)
            rect = font.render_to(window, (window.get_width() - 120, i * BLOCK_SIZE / 2), option + ": " + str(value), color)
        else:
            color = [(200, 50, 50), (50, 200, 50)][value]
            rect = font.render_to(window, (window.get_width() - 120, i * BLOCK_SIZE / 2), option, color)
        
        if mouse_down and rect.collidepoint(mouse_pos):
            if option == "draw layer":
                options[option] = (value + 1) % 4
            else:
                options[option] = not value
            

    for i, (name, (index, layer, surface)) in enumerate(block_data.items()):
        if selected_block == name:
            pygame.draw.rect(window, (50, 200, 50), (window.get_width() - 10 - BLOCK_SIZE, i * BLOCK_SIZE, 10, BLOCK_SIZE))
        rect = pygame.Rect(window.get_width() - BLOCK_SIZE, i * BLOCK_SIZE + BLOCK_SIZE * offset_block_list * len(block_data), BLOCK_SIZE, BLOCK_SIZE)
        window.blit(pygame.transform.scale(surface, (BLOCK_SIZE, BLOCK_SIZE)), rect.topleft)
        if mouse_down and rect.collidepoint(mouse_pos):
            selected_block = name

    pygame.display.flip()
    
        
    