# -*- coding: utf-8 -*-
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
    edit_file = input("Gib 'e' ein, um eine Struktur zu bearbeiten\noder nichts, um eine neu Struktur zu erstellen: ").startswith("e")

    if edit_file:
        filepath = input("Wähle die Datei: ")
        # Read file or exit
        with open(filepath, 'rb') as f:
            structure_data = pickle.load(f)
        print("selected", filepath)
    else:
        name = input("Wähle einen Namen: ")
        width = abs(int(input("Wähle die Breite in Blöcken: ")))
        height = abs(int(input("Wähle die Höhe in Blöcken: ")))
        array = numpy.zeros((width, height, 4), dtype=int)
        structure_data = {"name": name, "size": (width, height), "array": array}

    return structure_data


def save():
    for x, y, z in numpy.ndindex(structure_data["array"].shape):
        if z == 3:
            # Skip water layer
            continue

        if structure_string_array[x][y][z] == "air":
            structure_string_array[x][y][z] = 0
        else:
            block_name = structure_string_array[x][y][z]
            structure_string_array[x][y][z] = block_data[block_name][0]

    name = structure_data["name"]
    array = numpy.flip(numpy.array(structure_string_array, dtype=int), 1)

    entrance_coord = [0, structure_data["size"][1] // 2]
    exit_coord = [structure_data["size"][0] - 1, structure_data["size"][1] // 2]
    for y in range(structure_data["size"][1]):
        if array[0, y, 0] == 0:
            entrance_coord[1] = y
        if array[exit_coord[0], y, 0] == 0:
            exit_coord[1] = y

    properties = {
        "name": name,
        "generation": {
            "weight": 1.0,
            "entrance_coord": entrance_coord,
            "entrance_angle": 0,
            "exit_coord": exit_coord,
            "exit_angle": 0
        },
        "entities": [],
        "block_indices": structure_data["block_indices"]
    }

    file.save(f"data/structures/{name}/{name}.json", properties, file_format="json")
    file.save(f"data/structures/{name}/{name}.npy", array, file_format="numpy")


def load_blocks():
    block_paths = file.find("data/images/blocks", "*.json", True) 
    block_data = {}
    block_indices = {}

    for i, path in enumerate(block_paths):
        data = file.load(path, file_format="json")
        block = data["name"]
        image_name = data["frames"][0]
        path = file.find("data/images/blocks", image_name, True)[0]
        block_surface = pygame.image.load(path)

        block_data[data["name"]] = (i + 1, {"foreground":0, "plant":1, "background":2, "water":3}[data["layer"]], block_surface)
        block_indices[i + 1] = data["name"]
    return block_data, block_indices


structure_data = get_file()
block_data, block_indices = load_blocks()
structure_string_array = structure_data["array"].tolist()

canvas_move_speed = 1


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


pygame.init()
window = pygame.display.set_mode()
offset = [0, 0]
offset_block_list = 0
BLOCK_SIZE = 32
font = pygame.freetype.SysFont(None, 20)
options = {"erase": 0, "draw": 0, "draw water": 0, "add water": 0, "sub water": 0, "layer0": 1, "layer1": 1, "layer2": 1, "layer3": 1, "draw layer": 0}
selected_block = list(block_data.keys())[0]


def get_block_rect(x, y):
    return pygame.Rect((x + offset[0]) * BLOCK_SIZE, (y + offset[1]) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)


can_draw = 0
while True:
    mouse_down = 0
    scroll = 0
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
        if event.type == pygame.MOUSEWHEEL:
            scroll = event.y

    keys = pygame.key.get_pressed()
    if keys[K_RIGHT]:
        offset[0] = offset[0] + canvas_move_speed / structure_data["size"][0]
    if keys[K_LEFT]:
        offset[0] = offset[0] - canvas_move_speed / structure_data["size"][0]
    if keys[K_DOWN]:
        offset[1] = offset[1] + canvas_move_speed / structure_data["size"][1]
    if keys[K_UP]:
        offset[1] = offset[1] - canvas_move_speed / structure_data["size"][1]

    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed(5)
    offset_block_list = min(0, max(-1 + window.get_height() / ((len(block_data) + 10) * BLOCK_SIZE), offset_block_list + scroll / 10))

    if mouse_buttons[0] and mouse_pos[0] < window.get_width() - 120:
        block_coord = (int((mouse_pos[0] - offset[0] * BLOCK_SIZE) // BLOCK_SIZE), int((mouse_pos[1] - offset[1] * BLOCK_SIZE) // BLOCK_SIZE))
        if block_coord[0] < structure_data["size"][0] and block_coord[1] < structure_data["size"][1]:
            if options["erase"]:
                if options["draw layer"] == 3:
                    structure_string_array[block_coord[0]][block_coord[1]][options["draw layer"]] = 0
                else:
                    structure_string_array[block_coord[0]][block_coord[1]][options["draw layer"]] = "air"
            elif options["draw"] and options["draw layer"] != 3 and selected_block != "water":
                layer = block_data[selected_block][1]
                structure_string_array[block_coord[0]][block_coord[1]][layer] = selected_block
            elif can_draw and (options["draw water"] or options["draw"] and selected_block == "water"):
                level = 1000
                if options["add water"]:
                    level = min(1000, structure_string_array[block_coord[0]][block_coord[1]][3] + 100)
                    can_draw = 0
                if options["sub water"] and mouse_down:
                    level = max(0, structure_string_array[block_coord[0]][block_coord[1]][3] - 100)
                    can_draw = 0
                structure_string_array[block_coord[0]][block_coord[1]][3] = level

    for x, y in numpy.ndindex(structure_data["array"].shape[:2]):
        rect = get_block_rect(x, y)
        pygame.draw.rect(window, (200, 200, 200), rect)

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

    d = list(options.items())
    d.append(("type", selected_block))
    for i, (option, value) in enumerate(d):
        if option == "draw layer":
            color = (0, 0, 0)
            rect = font.render_to(window, (window.get_width() - 180, i * BLOCK_SIZE * 0.7), option + ": " + str(value), color)
        elif option == "type":
            rect = font.render_to(window, (window.get_width() - 180, i * BLOCK_SIZE * 0.7), value, (0, 0, 0))
        else:
            color = [(200, 50, 50), (50, 200, 50)][value]
            rect = font.render_to(window, (window.get_width() - 180, i * BLOCK_SIZE * 0.7), option, color)
        
        if mouse_down and rect.collidepoint(mouse_pos) and option != "type":
            if option == "draw layer":
                options[option] = (value + 1) % 4
            else:
                options[option] = not value
            
    for i, (name, (index, layer, surface)) in enumerate(block_data.items()):
        if selected_block == name:
            pygame.draw.rect(window, (50, 200, 50), (window.get_width() - 10 - BLOCK_SIZE, i * BLOCK_SIZE + BLOCK_SIZE * offset_block_list * len(block_data), 10, BLOCK_SIZE))
        rect = pygame.Rect(window.get_width() - BLOCK_SIZE, i * BLOCK_SIZE + BLOCK_SIZE * offset_block_list * len(block_data), BLOCK_SIZE, BLOCK_SIZE)
        window.blit(pygame.transform.scale(surface, (BLOCK_SIZE, BLOCK_SIZE)), rect.topleft)
        if mouse_down and rect.collidepoint(mouse_pos):
            selected_block = name

    pygame.display.flip()
    
        
    