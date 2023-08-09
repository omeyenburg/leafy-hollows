# -*- coding: utf-8 -*-
from pygame.locals import *
import scripts.utility.file as file
import pygame
import math
import os


sprites = {}
sprite_rects = []


def get_sprite_rect(image, time):
    """
    Returns the rectangle of the current animation frame of an image.
    """
    frames, speed = sprites[image]
    if speed != 0 or len(frames) > 1:
        index = int(time // speed % len(frames))
    else:
        index = 0
    return sprite_rects[frames[index]]


def load_blocks():
    """
    Load block texture atlas from files in a folder.
    """
    block_paths = file.find("data/images/blocks", "*.json", True)
    
    block_indices = {}
    frames = []
    block_data = []
    blocks = []

    for path in block_paths:
        blocks.append(file.read_json(file.relpath(path)))

    for data in sorted(blocks, key=lambda data: data["hardness"]):
        block = data["name"]
        frames.extend(data["frames"])
        block_data.append((data["name"], len(data["frames"]), data["speed"]))

    width = math.ceil(math.sqrt(len(frames)))
    height = math.ceil(len(frames) / width)
    image = pygame.Surface((width * 16, height * 16 + 1), SRCALPHA)

    for i, frame in enumerate(frames):
        y, x = divmod(i, width)
        path = file.find("data/images/blocks", frame + ".png", True)[0]
        block_surface = pygame.image.load(path)
        image.blit(block_surface, (x * 16, (height - y - 1) * 16))

    x = 0
    for block, length, speed in block_data:
        image.set_at((x, height * 16), (length, speed * 255 / 2, 0)) # length: 0-255 | speed: 0.0-2.0
        block_indices[block] = x + 1
        x += length

    pygame.image.save(image, file.abspath("data/blocks (testing only).png"))
    return block_indices, image


def load_sprites():
    """
    Load image texture atlas from files in a folder.
    """
    global sprite_rects
    global sprites

    images_data = file.read("data/images/layout/sprites.properties", split=True)
    images = {}
    paths = {}

    width = 0
    height = 0

    for image_data in images_data:
        image, data = image_data.replace(" ", "").split(":")
        rect = tuple([float(x) for x in data.replace("(", "").replace(")", "").split(",")])
        width = max(width, rect[0] + rect[2])
        height = max(height, rect[1] + rect[3])
        
        image_path = file.find("data/images/sprites", image + ".png", True)
        if not len(image_path):
            raise ValueError("Could not find file " + image + ".png in data/images/sprites")

        paths[str(image_path[0])] = len(sprite_rects)
        images[image] = len(sprite_rects)
        sprite_rects.append(rect)

    image = pygame.Surface((width, height), SRCALPHA)

    for image_path, i in paths.items():
        image.blit(pygame.image.load(image_path), (sprite_rects[i][0], sprite_rects[i][1]))
        sprite_rects[i] = (sprite_rects[i][0] / width, 1 - sprite_rects[i][1] / height - sprite_rects[i][3] / height, sprite_rects[i][2] / width, sprite_rects[i][3] / height)

    sprite_paths = file.find("data/images/sprites", "*.json", True)
    for path in sprite_paths:
        sprite = file.basename(path)
        data = file.read_json(file.relpath(path))
        indices = []
        for frame in data["frames"]:
            try:
                indices.append(images[frame])
            except KeyError:
                raise Exception(f"Could not find any data of '{frame}'.\nRun\n'python data/images/layout/setup.py'\nor\n'python3 data/images/layout/setup.py'")
        sprites[data["name"]] = (tuple(indices), data["speed"])


    pygame.image.save(image, file.abspath("data/sprites (testing only).png"))
    return image