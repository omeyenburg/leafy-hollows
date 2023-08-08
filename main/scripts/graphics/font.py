# -*- coding: utf-8 -*-
import pygame


class Font:
    def fromPNG(path):
        """
        Load a monospaced font from a PNG file with all letters from chr(32) to chr(96).
        """
        image = pygame.image.load(path).convert()

        letter_width = image.get_width() // 64
        letter_height = image.get_height()
        letters = {chr(i + 32): (1 / 64 * i, 1 / 64, letter_height / image.get_width()) for i in range(64)}

        return (letters, image)

    def fromTTF(path, size=1, antialias=False, lower=True):
        """
        Load a font from a TrueTypeFont file.
        """
        font = pygame.font.Font(path, size)
        images = []
        letters = {}
        if lower: # upper letters :96 | lower letters :123
            limit = 123
        else:
            limit = 96

        font_height = font.render("".join([chr(i) for i in range(32, limit)]), antialias, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", antialias, (0, 0, 0))

        for i in range(32, limit):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, antialias, (255, 255, 255))
            else:
                image = space
            letter_width = image.get_width()
            letters[chr(i)] = (font_width, letter_width, font_height)

            font_width += letter_width
            images.append(image)

        image = pygame.Surface((font_width, font_height))

        for letter in letters:
            image.blit(images[ord(letter) - 32], (0, letters[letter][0]))
            letters[letter] = (letters[letter][0] / font_width, letters[letter][1] / font_width, font_height / font_width)

        return (letters, image)

    def fromSYS(name, size=1, bold=False, antialias=False, lower=True):
        """
        Load a font from the system.
        """
        font = pygame.font.SysFont(name, size, bold=bold)
        images = []
        letters = {}
        if lower: # upper letters 32:96 | upper & lower letters 32:123
            limit = 123
        else:
            limit = 96

        font_height = font.render("".join([chr(i) for i in range(32, limit)]), antialias, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", antialias, (0, 0, 0))
        for i in range(32, limit):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, antialias, (255, 255, 255))
            else:
                image = space
            letter_width = image.get_width()
            letters[chr(i)] = (font_width, letter_width, font_height)

            font_width += letter_width
            images.append(image)

        image = pygame.Surface((font_width, font_height))
        for letter in letters:
            image.blit(images[ord(letter) - 32], (letters[letter][0], 0))
            letters[letter] = (letters[letter][0] / font_width, letters[letter][1] / font_width, font_height / font_width)

        return (letters, image)