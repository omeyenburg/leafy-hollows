# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.utility import file
import pygame


def get_sprite_rect(window, image, offset=0):
    """
    Returns the rectangle of the current animation frame of an image.
    """
    frames, speed = window.sprites[image]
    if speed != 0 or len(frames) > 1:
        index = int((window.time + 10 * offset) // speed % len(frames))
    else:
        index = 0
    return window.sprite_rects[frames[index]]


def load_blocks():
    """
    Load block texture atlas from files in a folder.
    """
    block_paths = file.find("data/images/blocks", "*.json", True)
    
    block_data = {}
    block_indices = {}
    frames = []
    animation = []
    blocks = []
    families = {}
    block_group_size = {}
    block_properties = {}
    block_generation_properties = {}

    for path in block_paths:
        blocks.append(file.load(path, file_format="json"))

    for data in sorted(blocks, key=lambda data: data["hardness"]):
        # Large blocks
        block = data["name"]
        sample_image_path = file.find("data/images/blocks", data["frames"][0], True)[0]
        size = pygame.image.load(sample_image_path).get_size()

        if "properties" in data:
            block_properties[block] = data["properties"]

        if "generation" in data:
            block_generation_properties[block] = data["generation"]

        if size == (WORLD_BLOCK_SIZE, WORLD_BLOCK_SIZE):
            frames.extend(data["frames"])
            block_data[block] = (data["hardness"], data["family"], data["layer"])
            animation.append((block, len(data["frames"]), data["speed"]))
        else:
            block_group_size[block] = (size[0] // WORLD_BLOCK_SIZE, size[1] // WORLD_BLOCK_SIZE)
            for frame in data["frames"]:
                for x in range(0, size[0], WORLD_BLOCK_SIZE):
                    for y in range(0, size[1], WORLD_BLOCK_SIZE):
                        frames.append((frame, x, y))
                        sub_block = f"{block}_{x // WORLD_BLOCK_SIZE}_{y // WORLD_BLOCK_SIZE}"
                        block_data[sub_block] = (data["hardness"], data["family"], data["layer"])
                        animation.append((sub_block, len(data["frames"]), data["speed"]))        
        
        if not data["family"] in families:
            families[data["family"]] = len(families)

    width = math.ceil(math.sqrt(len(frames)))
    height = math.ceil(len(frames) / width)
    block_animation_rows = len(frames) // (width * WORLD_BLOCK_SIZE) + 1
    image = pygame.Surface((width * WORLD_BLOCK_SIZE, height * WORLD_BLOCK_SIZE + block_animation_rows), pygame.SRCALPHA)

    for i, frame in enumerate(frames):
        y, x = divmod(i, width)

        if isinstance(frame, str):
            pos = (0, 0)
        else:
            pos = frame[1:]
            frame = frame[0]

        try:
            path = file.find("data/images/blocks", frame, True)[0]
        except IndexError:
            raise Exception("Could not find block " + frame)
        block_surface = pygame.image.load(path)

        image.blit(block_surface, (x * WORLD_BLOCK_SIZE, (height - y - 1) * WORLD_BLOCK_SIZE), (*pos, WORLD_BLOCK_SIZE, WORLD_BLOCK_SIZE))

    x = 0
    for block, length, speed in animation:
        image.set_at((x % (width * WORLD_BLOCK_SIZE), height * WORLD_BLOCK_SIZE + x // (width * WORLD_BLOCK_SIZE)), (length, speed * 255 / 2, families[block_data[block][1]])) # length: 0-255 | speed: 0.0-2.0
        block_data[block] = (x * 2 + 1, *block_data[block][1:])
        if block in block_properties:
            block_properties[x * 2 + 1] = block_properties[block]
            del block_properties[block]
        x += length

    if CREATE_TEXTURE_ATLAS_FILE:
        pygame.image.save(image, file.abspath("data/blocks (testing only).png"))  

    return block_data, block_generation_properties, block_group_size, block_properties, image


def load_sprites():
    """
    Load image texture atlas from files in a folder.
    """
    sprites = {}
    sprite_rects = []

    images_data = file.load("data/images/layout/sprites.properties", split=True)
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
            raise ValueError("Could not find file " + image + ".png in data/images/sprites.\nRun\n'python data/images/layout/setup.py'\nor\n'python3 data/images/layout/setup.py'")

        paths[str(image_path[0])] = len(sprite_rects)
        images[image] = len(sprite_rects)
        sprite_rects.append(rect)

    image = pygame.Surface((width, height), pygame.SRCALPHA)

    for image_path, i in paths.items():
        image.blit(pygame.image.load(image_path), (sprite_rects[i][0], sprite_rects[i][1]))
        sprite_rects[i] = (sprite_rects[i][0] / width, 1 - sprite_rects[i][1] / height - sprite_rects[i][3] / height, sprite_rects[i][2] / width, sprite_rects[i][3] / height)

    sprite_paths = file.find("data/images/sprites", "*.json", True)
    for path in sprite_paths:
        sprite = file.basename(path)
        data = file.load(path, file_format="json")
        indices = []
        for frame in data["frames"]:
            frame = frame.split(".")[0]
            try:
                indices.append(images[frame])
            except KeyError:
                raise Exception(f"Could not find any data of '{frame}'.\nRun\n'python data/images/layout/setup.py'\nor\n'python3 data/images/layout/setup.py'")
        sprites[data["name"]] = (tuple(indices), data["speed"])

    if CREATE_TEXTURE_ATLAS_FILE:
        pygame.image.save(image, file.abspath("data/sprites (testing only).png"))

    return sprites, sprite_rects, image
