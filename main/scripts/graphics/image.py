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
    frames, length = sprites[image]
    if length != 0 or len(frames) > 1:
        index = int(time // length % len(frames))
    else:
        index = 0
    return sprite_rects[frames[index]]


def load_blocks():
    """
    Load block texture atlas from files in a folder.
    """
    paths = file.find("data/blocks", "*.png", True)        
    width = math.ceil(math.sqrt(len(paths)))
    height = math.ceil(len(paths) / width)
    image = pygame.Surface((width * 16, height * 16 + 1), SRCALPHA)
    block_indices = {}
    animation_frames = {}

    for i, path in enumerate(paths):
        y, x = divmod(i, width)
        file_name = os.path.basename(path).split(".")
        if len(file_name) == 2:
            block = file_name[0]
            frame = 1
        else:
            block = file_name[0]
            frame = int(file_name[1])
        if not block in animation_frames:
            block_indices[block] = i + 1
        block_surface = pygame.image.load(path)
        image.blit(block_surface, (x * 16, (height - y - 1) * 16))
        animation_frames[block] = max(animation_frames.get(block, 1), frame)
        
    x = 0
    for block in animation_frames:
        image.set_at((x, height * 16), (animation_frames[block], 0, 0))
        x += animation_frames[block]

    pygame.image.save(image, file.abspath("data/blocks.png"))
    return block_indices, image


def load_sprites():
    """
    Load image texture atlas from files in a folder.
    """
    global sprite_rects
    global sprites


    images_data = file.read("data/images/layout/sprites.properties", split=True)
    images = {} # "image": [rect_index, animation_frames]
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
                raise Exception(f"Could not find any data of '{frame}'.\nRun 'python data/images/layout/setup.py'\nor\n'python3 data/images/layout/setup.py'")
        sprites[data["name"]] = (tuple(indices), data["time"])


    pygame.image.save(image, file.abspath("data/sprites (testing only).png"))
    return image