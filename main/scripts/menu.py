import math
import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

import scripts.geometry as geometry
import scripts.graphics as graphics
import scripts.util as util


def update(window: graphics.Window): # Executed from main
    if not Page.opened is None:
        Page.opened.update(window)


class Page:
    opened = None
    
    def __init__(self, columns: int=1, spacing: int=0):
        self.children = []
        self.columns = columns
        self.spacing = spacing

    def layout(self):
        """
        Position all widgets in a grid on a page.
        """
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.column] = max(width[child.column], child.rect.w / child.columnspan - self.spacing * (child.columnspan - 1))
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) + self.spacing * (self.columns - 1)
        total_height = sum(height) + self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.rect.right = sum(width[:child.column + 1]) - total_width / 2 + self.spacing * (child.column + (child.columnspan - 1) / 2) + width[child.column] * (child.columnspan - 1) / 2
            child.rect.bottom = sum(height[:child.row + 1]) - total_height / 2 + self.spacing * child.row - height[child.row] + child.rect.h
            child.rect.centery = -child.rect.centery

    def layout(self):
        """
        Position all widgets in a grid on a page.
        """
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.column] = max(width[child.column], child.rect.w / child.columnspan - self.spacing * (child.columnspan - 1))
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) + self.spacing * (self.columns - 1)
        total_height = sum(height) + self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.rect.centerx = sum(width[:child.column + 1]) - total_width / 2 + self.spacing * (child.column + (child.columnspan - 1) / 2) + width[child.column] * (child.columnspan - 1) / 2 - width[child.column] / 2
            child.rect.centery = sum(height[:child.row + 1]) - total_height / 2 + self.spacing * child.row - height[child.row] + child.rect.h - height[child.row] / 2
            child.rect.centery = -child.rect.centery

    def update(self, window: graphics.Window):
        self.draw(window)
        for child in self.children:
            child.update(window)

    def draw(self, window: graphics.Window):
        pass

    #def coords(self):
    #    return pygame.Rect(self.rect.x + (window.size[0] - self.rect.w) // 2, self.rect.y + (window.size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def open(self):
        Page.opened = self


class Widget:
    def __init__(self, parent, size: [float], row: int=0, column: int=0, columnspan: int=1):
        self.parent = parent
        self.children = []
        self.rect = geometry.Rect(0, 0, *size)
        self.parent.children.append(self)
        self.row = row
        self.column = column
        self.columnspan = columnspan

    def update(self, window: graphics.Window):
        self.draw()
        for child in self.children:
            child.update(window)

    #def coords(self, rect=None):
    #    if rect is None:
    #        rect = self.rect
    #    return pygame.Rect(rect.x + (window.size[0] - rect.w) // 2, rect.y + (window.size[1] - rect.h) // 2, rect.w, rect.h)

    #def draw(self, window: graphics.Window):
    #    raise NotImplementedError("Subclasses of Widget must implement the draw method.")
             

class Button(Widget):
    def __init__(self, *args, text: str="", callback=None, duration: float=0.2, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] seconds

    def update(self, window: graphics.Window):
        pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        if 1 in window.mouse_buttons and self.rect.collidepoint(pos):
            self.clicked = int(self.duration / window.delta_time)
            if not self.callback is None:
                self.callback()

        if self.clicked:
            self.clicked -= 1
            self.draw_clicked(window)
        else:
            self.draw_idle(window)

    def draw_idle(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 255))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), 1.13, centered=True)

    def draw_clicked(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 200))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), 1.13, centered=True)


class Label(Widget):
    def __init__(self, *args, text: str="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self, window: graphics.Window):
        #font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)
        window.draw_text(self.rect.center, self.text, (255, 255, 255, 255), 1.3, centered=True)


class Space(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self):
        pass


class Slider(Widget):
    def __init__(self, *args, value=0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value
        self.selected = False
        self.slider_rect = self.rect.copy()

    def update(self):
        self.slider_rect.w = self.slider_rect.h // 3
        self.slider_rect.x = (self.rect.w - self.slider_rect.w) * self.value + self.coords().x
        self.slider_rect.y = self.coords().y

        if self.slider_rect.collidepoint(window.mouse_pos[:2]) and 1 in window.mouse_buttons:
            self.selected = True
        elif not any(window.mouse_buttons):
            self.selected = False

        if self.selected:
            self.value = min(1.0, max(0.0, (window.mouse_pos[0] - self.coords().x) / self.rect.w))

        self.draw()

    def draw(self):
        pygame.draw.rect(window.world_surface, (255, 255, 255), self.coords(), 1)
        pygame.draw.rect(window.world_surface, (255, 255, 255), self.slider_rect, 1)


class Entry(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.selected = False
        self.cursor = 0

    def update(self):
        if window.unicode == "\x08":
            self.text = self.text[:-1]
        elif window.unicode.isprintable():
            self.text += window.unicode

        self.draw()

    def draw(self):
        pygame.draw.rect(window.world_surface, (255, 255, 255), self.coords(), 1)
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().topleft)


class Switch(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self):
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)

