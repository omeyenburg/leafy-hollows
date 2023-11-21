# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.utility import file
import pygame
import math


class Font:
    def __new__(cls, name=None, resolution=1, bold=False, antialias=False):
        instance = super().__new__(cls)
        image = instance._load(name, resolution, bold, antialias)

        if CREATE_TEXTURE_ATLAS_FILE:
            pygame.image.save(image, file.abspath("data/font (testing only).png"))

        if ".ttf" in name:
            file.save("data/fonts/" + name.replace(".ttf", ".json"), instance.char_rects, file_format="json")
            pygame.image.save(image, file.abspath("data/fonts/" + name.replace(".ttf", ".png")))

        return instance, image

    def _load(self, name, resolution, bold, antialias):
        # Load font
        if ".json" in name:
            self.char_rects = file.load("data/fonts/" + name, file_format="json")
            image = pygame.image.load(file.abspath("data/fonts/" + name.replace(".json", ".png")))
            return image

        if "." in name:
            font = pygame.font.Font(file.abspath("data/fonts/" + name), resolution)
            font.bold = bold
        else:
            font = pygame.font.SysFont(name, resolution, bold=bold)
        self.char_rects = {}
        
        # Generate character images
        character_images = [font.render(char, antialias, (255, 255, 255)) for char in FONT_CHARACTERS]

        # Get maximum character size
        self.char_width = max([char_img.get_width() for char_img in character_images])
        self.char_height = font.render(FONT_CHARACTERS, antialias, (0, 0, 0)).get_height()
        
        # Get columns and rows
        self.columns = int(FONT_CHARACTERS_LENGTH ** 0.6)
        self.rows = (FONT_CHARACTERS_LENGTH + self.columns - 1) // self.columns
        
        # Create surface
        font_size = (self.columns * self.char_width, self.rows * self.char_height)
        image = pygame.Surface(font_size)

        # Blit characters and store character rectangles
        for i in range(FONT_CHARACTERS_LENGTH):
            row = i // self.columns
            column = i % self.columns

            center = ((column + 0.5) * self.char_width, (row + 0.5) * self.char_height)
            char_img = character_images[i]
            char_size = char_img.get_size()
            char_coord = (center[0] - char_size[0] / 2, center[1] - char_size[1] / 2)

            char_rect = (column * self.char_width / font_size[0], 1 - row * self.char_height / font_size[1] - 1 / self.rows, 1 / self.columns, 1 / self.rows)
            self.char_rects[FONT_CHARACTERS[i]] = char_rect
            image.blit(char_img, char_coord)

        return image

    def get_rect(self, char):
        if not char in FONT_CHARACTERS:
            char = "?"
        return self.char_rects[char]
