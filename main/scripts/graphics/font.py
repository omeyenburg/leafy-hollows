# -*- coding: utf-8 -*-
import pygame


characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äÄüÜöÖß _.,:;?!<=>#@\'\"+-*/()"


class Font:
    def __new__(cls, name=None, size=1, bold=False, antialias=False):
        char_rects = {}

        font = pygame.font.SysFont(name, size, bold=bold)
        images = []
        font_height = font.render(characters, antialias, (0, 0, 0)).get_height()
        font_width = 0
        space = font.render("A", antialias, (0, 0, 0))

        for char in characters:
            if char != " ":
                image = font.render(char, antialias, (255, 255, 255))
            else:
                image = space
            char_width = image.get_width()
            char_rects[char] = (font_width, char_width, font_height)

            font_width += char_width
            images.append(image)

        image = pygame.Surface((font_width, font_height))
        instance = super().__new__(cls)
        instance.char_rects = char_rects
        for i, char in enumerate(characters):
            image.blit(images[i], (instance.char_rects[char][0], 0))
            instance.char_rects[char] = (instance.char_rects[char][0] / font_width, instance.char_rects[char][1] / font_width, font_height / font_width)

        return instance, image

    def get_rect(self, char):
        if not char in characters:
            char = "?"
        return self.char_rects[char]